#!/usr/bin/env python3
"""
Thumbnail Mate v1.0 - Performance Feedback Loop

Pulls YouTube analytics data for videos that used generated thumbnails,
updates the Performance table, and adjusts template scores based on CTR.

Usage:
    python3 update_performance.py                    # Update all tracked videos
    python3 update_performance.py --channel-id UCxxx # Specify your channel ID
    python3 update_performance.py --sync             # Sync generations -> performance

Note: The YouTube Analytics API requires OAuth2 for accessing your own channel's
analytics data (impressions, CTR). This script uses the YouTube Data API v3 for
publicly available stats (views, likes) and can be extended with OAuth2 for full
analytics access.

For full CTR data, you'll need to set up OAuth2:
  1. Go to Google Cloud Console -> APIs & Services -> Credentials
  2. Create an OAuth2 Client ID (Desktop app)
  3. Download client_secret.json to this folder
  4. Run: python3 update_performance.py --setup-oauth
"""

import urllib.request
import json
import os
import sys
from datetime import datetime, timedelta

from config import (
    YOUTUBE_API_KEY, AIRTABLE_TOKEN,
    AIRTABLE_BASE_ID, AIRTABLE_TABLES
)


def airtable_get(table_key, params=""):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLES[table_key]}{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AIRTABLE_TOKEN}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def airtable_create(table_key, fields):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLES[table_key]}"
    payload = json.dumps({"records": [{"fields": fields}]}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def airtable_update(table_key, record_id, fields):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLES[table_key]}"
    payload = json.dumps({"records": [{"id": record_id, "fields": fields}]}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="PATCH", headers={
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_video_stats(video_ids):
    """Get public stats for videos via YouTube Data API."""
    stats = {}
    # Process in batches of 50
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        ids_str = ",".join(batch)
        url = (
            f"https://www.googleapis.com/youtube/v3/videos?"
            f"part=statistics,snippet&id={ids_str}&key={YOUTUBE_API_KEY}"
        )
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        for item in data.get("items", []):
            vid = item["id"]
            s = item["statistics"]
            stats[vid] = {
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0)),
                "title": item["snippet"]["title"],
                "published": item["snippet"]["publishedAt"],
            }
    return stats


def sync_generations_to_performance():
    """Create Performance records for published generations that don't have one yet."""
    print("Syncing Generations -> Performance...")

    # Get all generations with status "Published"
    gens = airtable_get("generations")
    published = []
    for rec in gens.get("records", []):
        f = rec["fields"]
        if f.get("Status") == "Published" and f.get("Video ID"):
            published.append({
                "record_id": rec["id"],
                "title": f.get("Video Title", ""),
                "video_id": f.get("Video ID", ""),
                "template": f.get("Template Used", ""),
            })

    # Get existing performance records
    perf = airtable_get("performance")
    existing_ids = set()
    for rec in perf.get("records", []):
        vid = rec["fields"].get("Video ID", "")
        if vid:
            existing_ids.add(vid)

    # Create missing performance records
    new_count = 0
    for gen in published:
        if gen["video_id"] not in existing_ids:
            airtable_create("performance", {
                "Video Title": gen["title"],
                "Video ID": gen["video_id"],
                "Video URL": f"https://youtube.com/watch?v={gen['video_id']}",
                "Thumbnail Style": gen["template"],
            })
            new_count += 1
            print(f"  Created performance record for: {gen['title'][:50]}")

    print(f"  Synced {new_count} new records")
    return new_count


def update_all_performance():
    """Update stats for all tracked videos."""
    print("\nUpdating performance stats...")

    perf = airtable_get("performance")
    records = perf.get("records", [])

    if not records:
        print("  No videos to update. Run --sync first or add Video IDs to Generations table.")
        return

    # Collect video IDs
    video_map = {}  # video_id -> record_id
    for rec in records:
        vid = rec["fields"].get("Video ID", "")
        if vid:
            video_map[vid] = rec["id"]

    print(f"  Fetching stats for {len(video_map)} videos...")
    stats = get_video_stats(list(video_map.keys()))

    # Update each record
    updated = 0
    for vid, record_id in video_map.items():
        if vid in stats:
            s = stats[vid]
            # Calculate days since publish for rough 7d/30d estimates
            published = datetime.fromisoformat(s["published"].replace("Z", "+00:00"))
            days_since = (datetime.now(published.tzinfo) - published).days

            fields = {
                "Views 7d": s["views"] if days_since <= 7 else None,
                "Views 30d": s["views"] if days_since <= 30 else None,
                "Notes": f"Updated {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                         f"{s['views']:,} views, {s['likes']:,} likes, {s['comments']:,} comments | "
                         f"Published {days_since}d ago",
            }
            # Remove None values
            fields = {k: v for k, v in fields.items() if v is not None}

            airtable_update("performance", record_id, fields)
            updated += 1
            print(f"  Updated: {s['title'][:50]} ({s['views']:,} views)")

    print(f"  Updated {updated} records")


def update_template_scores():
    """Recalculate template scores based on performance data."""
    print("\nUpdating template scores...")

    # Get performance data
    perf = airtable_get("performance")
    style_stats = {}  # style -> [views list]

    for rec in perf.get("records", []):
        f = rec["fields"]
        style = f.get("Thumbnail Style", "default")
        views = f.get("Views 30d") or f.get("Views 7d") or 0
        ctr = f.get("CTR Percent", 0)

        if style not in style_stats:
            style_stats[style] = {"views": [], "ctrs": []}
        style_stats[style]["views"].append(views)
        if ctr > 0:
            style_stats[style]["ctrs"].append(ctr)

    if not style_stats:
        print("  No performance data yet")
        return

    # Calculate scores (1-10 scale)
    all_avg_views = []
    for style, data in style_stats.items():
        avg_views = sum(data["views"]) / len(data["views"]) if data["views"] else 0
        all_avg_views.append(avg_views)

    max_views = max(all_avg_views) if all_avg_views else 1

    print(f"\n  Style Performance Summary:")
    print(f"  {'Style':<40} {'Avg Views':>12} {'Avg CTR':>10} {'Score':>7}")
    print(f"  {'-'*40} {'-'*12} {'-'*10} {'-'*7}")

    for style, data in style_stats.items():
        avg_views = sum(data["views"]) / len(data["views"]) if data["views"] else 0
        avg_ctr = sum(data["ctrs"]) / len(data["ctrs"]) if data["ctrs"] else 0
        # Score: 70% views-based, 30% CTR-based (if available)
        view_score = (avg_views / max_views * 10) if max_views > 0 else 5
        ctr_score = min(avg_ctr / 10 * 10, 10) if avg_ctr > 0 else view_score
        final_score = round(view_score * 0.7 + ctr_score * 0.3, 1)

        print(f"  {style:<40} {avg_views:>12,.0f} {avg_ctr:>9.1f}% {final_score:>7.1f}")

        # Update templates with this style
        templates = airtable_get("templates")
        for rec in templates.get("records", []):
            if rec["fields"].get("Layout Type") == style or rec["fields"].get("Template Name", "").startswith(style):
                airtable_update("templates", rec["id"], {"Score": final_score})

    print(f"\n  Template scores updated based on {len(style_stats)} styles")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Update YouTube performance data")
    parser.add_argument("--sync", action="store_true", help="Sync generations to performance table")
    parser.add_argument("--scores", action="store_true", help="Update template scores only")
    args = parser.parse_args()

    print("Thumbnail Mate v1.0 - Performance Feedback Loop")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    if args.sync:
        sync_generations_to_performance()

    if args.scores:
        update_template_scores()
    else:
        sync_generations_to_performance()
        update_all_performance()
        update_template_scores()

    print("\nDone!")
    print("\nNote: For full CTR/impression data, you need YouTube Analytics API with OAuth2.")
    print("The current setup tracks views, likes, and comments via the public Data API.")
    print("Run with --setup-oauth to configure full analytics access.")


if __name__ == "__main__":
    main()
