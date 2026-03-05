#!/usr/bin/env python3
"""
Viral Radar Cleanup — Remove duplicates + backfill Outlier Scores.

This script:
1. Fetches ALL records from the Viral Videos table (handles pagination)
2. Removes duplicates by URL (keeps the OLDEST record to preserve Thumbnail Used flags)
3. Calculates and backfills Outlier Score for records missing it

Usage:
    python3 viral_radar_cleanup.py              # Full cleanup: dedup + backfill
    python3 viral_radar_cleanup.py --dedup-only  # Only remove duplicates
    python3 viral_radar_cleanup.py --backfill-only  # Only backfill Outlier Score
    python3 viral_radar_cleanup.py --dry-run     # Preview changes without applying
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import argparse
from collections import defaultdict
from statistics import median as calc_median

# Load .env
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
AIRTABLE_TOKEN = ""
with open(ENV_PATH) as f:
    for line in f:
        if line.startswith("AIRTABLE_PERSONAL_ACCESS_TOKEN="):
            AIRTABLE_TOKEN = line.strip().split("=", 1)[1]

AIRTABLE_BASE = "YOUR_AIRTABLE_BASE_ID"
VIDEOS_TABLE = "YOUR_VIRAL_VIDEOS_TABLE_ID"
BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{VIDEOS_TABLE}"


def airtable_request(url, method="GET", data=None):
    """Make an Airtable API request with proper headers."""
    headers = {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        print(f"  ERROR {e.code}: {body[:300]}")
        return None


def fetch_all_records(fields=None):
    """Fetch ALL records from Viral Videos table, handling pagination."""
    all_records = []
    offset = None
    page = 0

    params = {"pageSize": "100"}
    if fields:
        for i, f in enumerate(fields):
            params[f"fields[{i}]"] = f

    while True:
        page += 1
        query = urllib.parse.urlencode(params)
        url = f"{BASE_URL}?{query}"
        if offset:
            url += f"&offset={offset}"

        resp = airtable_request(url)
        if not resp:
            break

        records = resp.get("records", [])
        all_records.extend(records)
        print(f"  Page {page}: {len(records)} records (total: {len(all_records)})")

        offset = resp.get("offset")
        if not offset:
            break

    return all_records


def remove_duplicates(records, dry_run=False):
    """Remove duplicate records by URL, keeping the OLDEST one.

    Oldest = earliest Scraped Date (or earliest createdTime if no Scraped Date).
    This preserves Thumbnail Used flags from older records.
    """
    print("\n=== DEDUP: Removing duplicate URLs ===")

    # Group records by URL
    by_url = defaultdict(list)
    for rec in records:
        url = rec.get("fields", {}).get("URL", "")
        if url:
            by_url[url].append(rec)

    # Find duplicates
    total_dupes = 0
    ids_to_delete = []

    for url, recs in by_url.items():
        if len(recs) <= 1:
            continue

        # Sort by Scraped Date ascending (oldest first), fallback to createdTime
        recs.sort(key=lambda r: (
            r.get("fields", {}).get("Scraped Date", "") or
            r.get("createdTime", "")
        ))

        # Keep the first (oldest), delete the rest
        keeper = recs[0]
        dupes = recs[1:]
        total_dupes += len(dupes)

        keeper_title = keeper.get("fields", {}).get("Title", "?")[:50]
        keeper_date = keeper.get("fields", {}).get("Scraped Date", "?")
        thumb_used = keeper.get("fields", {}).get("Thumbnail Used", False)

        print(f"  URL: {url}")
        print(f"    KEEP: {keeper['id']} — \"{keeper_title}\" ({keeper_date})"
              f"{' [Thumbnail Used]' if thumb_used else ''}")
        for d in dupes:
            d_title = d.get("fields", {}).get("Title", "?")[:50]
            d_date = d.get("fields", {}).get("Scraped Date", "?")
            print(f"    DELETE: {d['id']} — \"{d_title}\" ({d_date})")
            ids_to_delete.append(d["id"])

    if not ids_to_delete:
        print("  No duplicates found!")
        return 0

    print(f"\n  Total duplicates to delete: {total_dupes}")

    if dry_run:
        print("  [DRY RUN] No records deleted.")
        return total_dupes

    # Delete in batches of 10 (Airtable max per DELETE request)
    deleted = 0
    for i in range(0, len(ids_to_delete), 10):
        batch = ids_to_delete[i:i + 10]
        params = "&".join(f"records[]={rid}" for rid in batch)
        url = f"{BASE_URL}?{params}"
        resp = airtable_request(url, method="DELETE")
        if resp:
            deleted += len(batch)
            print(f"  Deleted batch {i // 10 + 1}: {len(batch)} records")
        time.sleep(0.25)  # Rate limit

    print(f"  Total deleted: {deleted}")
    return deleted


def backfill_outlier_scores(records, dry_run=False):
    """Calculate and backfill Outlier Score for records missing it.

    Outlier Score = Views / Channel Median Views (e.g., 3.4x)
    """
    print("\n=== BACKFILL: Calculating Outlier Scores ===")

    # Group by channel to calculate medians
    by_channel = defaultdict(list)
    for rec in records:
        fields = rec.get("fields", {})
        channel = fields.get("Channel Name", "Unknown")
        views = fields.get("Views", 0) or 0
        by_channel[channel].append({"rec": rec, "views": views})

    # Calculate channel medians
    channel_medians = {}
    for channel, vids in by_channel.items():
        views_list = [v["views"] for v in vids if v["views"] > 0]
        if views_list:
            channel_medians[channel] = calc_median(views_list)
        else:
            channel_medians[channel] = 0
        print(f"  {channel}: {len(vids)} videos, median = {channel_medians[channel]:,.0f} views")

    # Find records missing Outlier Score or with score = 0
    to_update = []
    for rec in records:
        fields = rec.get("fields", {})
        current_score = fields.get("Outlier Score")
        views = fields.get("Views", 0) or 0
        channel = fields.get("Channel Name", "Unknown")
        ch_median = channel_medians.get(channel, 0)

        if ch_median > 0 and views > 0:
            new_score = round(views / ch_median, 1)
        else:
            new_score = 0

        # Update if missing, zero, or significantly different
        if current_score is None or current_score == 0 or abs((current_score or 0) - new_score) > 0.1:
            to_update.append({
                "id": rec["id"],
                "old_score": current_score,
                "new_score": new_score,
                "title": fields.get("Title", "?")[:50],
            })

    if not to_update:
        print(f"\n  All {len(records)} records already have correct Outlier Scores!")
        return 0

    print(f"\n  Records to update: {to_update[:5]}")
    if len(to_update) > 5:
        print(f"  ... and {len(to_update) - 5} more")

    if dry_run:
        print(f"  [DRY RUN] Would update {len(to_update)} records.")
        return len(to_update)

    # Update in batches of 10
    updated = 0
    for i in range(0, len(to_update), 10):
        batch = to_update[i:i + 10]
        payload = {
            "records": [
                {
                    "id": item["id"],
                    "fields": {"Outlier Score": item["new_score"]}
                }
                for item in batch
            ]
        }
        resp = airtable_request(BASE_URL, method="PATCH", data=payload)
        if resp:
            updated += len(batch)
            print(f"  Updated batch {i // 10 + 1}: {len(batch)} records")
        time.sleep(0.25)  # Rate limit

    print(f"  Total updated: {updated}")
    return updated


def main():
    parser = argparse.ArgumentParser(description="Viral Radar Cleanup — dedup + backfill")
    parser.add_argument("--dedup-only", action="store_true", help="Only remove duplicates")
    parser.add_argument("--backfill-only", action="store_true", help="Only backfill Outlier Score")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    args = parser.parse_args()

    do_dedup = not args.backfill_only
    do_backfill = not args.dedup_only

    print("=" * 60)
    print("VIRAL RADAR CLEANUP")
    print("=" * 60)

    # Fetch all records (need all fields for both operations)
    fields = ["URL", "Title", "Scraped Date", "Views", "Channel Name",
              "Outlier Score", "Thumbnail Used"]
    print(f"\nFetching all records from Viral Videos table...")
    records = fetch_all_records(fields=fields)
    print(f"Total records: {len(records)}")

    results = {}

    if do_dedup:
        results["duplicates_removed"] = remove_duplicates(records, dry_run=args.dry_run)
        # Re-fetch after dedup (records have changed)
        if results["duplicates_removed"] > 0 and not args.dry_run and do_backfill:
            print("\nRe-fetching records after dedup...")
            records = fetch_all_records(fields=fields)

    if do_backfill:
        results["scores_updated"] = backfill_outlier_scores(records, dry_run=args.dry_run)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if "duplicates_removed" in results:
        print(f"  Duplicates removed: {results['duplicates_removed']}")
    if "scores_updated" in results:
        print(f"  Outlier Scores updated: {results['scores_updated']}")
    if args.dry_run:
        print("  [DRY RUN — no changes applied]")
    print("=" * 60)


if __name__ == "__main__":
    main()
