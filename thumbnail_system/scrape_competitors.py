#!/usr/bin/env python3
"""
Thumbnail Mate v1.0 - Competitor Thumbnail Scraper

Scrapes thumbnails from competitor YouTube channels, downloads them,
analyzes the style using Gemini, and stores results in Airtable.

Usage:
    python3 scrape_competitors.py              # Scrape all active competitors
    python3 scrape_competitors.py --channel "Nick Saraev"  # Scrape one channel
    python3 scrape_competitors.py --max 10     # Max videos per channel
"""

import urllib.request
import json
import os
import sys
import base64
import time
from datetime import datetime

from config import (
    YOUTUBE_API_KEY, GEMINI_API_KEY, AIRTABLE_TOKEN,
    AIRTABLE_BASE_ID, AIRTABLE_TABLES, NANO_BANANA_MODEL,
    COMPETITOR_DIR, TEMPLATES_DIR
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


def get_active_competitors(channel_filter=None):
    data = airtable_get("competitors")
    channels = []
    for rec in data.get("records", []):
        f = rec["fields"]
        if f.get("Active") and (not channel_filter or channel_filter.lower() in f.get("Channel Name", "").lower()):
            channels.append({
                "record_id": rec["id"],
                "name": f.get("Channel Name", ""),
                "channel_id": f.get("Channel ID", ""),
                "scraped": f.get("Thumbnails Scraped", 0),
            })
    return channels


def get_channel_videos(channel_id, max_results=15):
    """Get recent videos from a channel via YouTube Data API."""
    url = (
        f"https://www.googleapis.com/youtube/v3/search?"
        f"part=snippet&channelId={channel_id}&type=video&order=date"
        f"&maxResults={max_results}&key={YOUTUBE_API_KEY}"
    )
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    videos = []
    for item in data.get("items", []):
        vid = item["id"].get("videoId")
        if vid:
            videos.append({
                "video_id": vid,
                "title": item["snippet"]["title"],
                "thumbnail_url": f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg",
                "published": item["snippet"]["publishedAt"],
            })
    return videos


def get_video_stats(video_ids):
    """Get view counts to identify top performers."""
    ids_str = ",".join(video_ids)
    url = (
        f"https://www.googleapis.com/youtube/v3/videos?"
        f"part=statistics&id={ids_str}&key={YOUTUBE_API_KEY}"
    )
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    stats = {}
    for item in data.get("items", []):
        stats[item["id"]] = int(item["statistics"].get("viewCount", 0))
    return stats


def download_thumbnail(video_id, thumbnail_url, channel_name):
    """Download a thumbnail image to the competitor_thumbnails folder."""
    safe_name = channel_name.replace(" ", "_").replace("|", "").replace("/", "_")
    channel_dir = os.path.join(COMPETITOR_DIR, safe_name)
    os.makedirs(channel_dir, exist_ok=True)

    filepath = os.path.join(channel_dir, f"{video_id}.jpg")
    if os.path.exists(filepath):
        return filepath

    try:
        urllib.request.urlretrieve(thumbnail_url, filepath)
        return filepath
    except Exception:
        # Fallback to hqdefault if maxres not available
        fallback = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        try:
            urllib.request.urlretrieve(fallback, filepath)
            return filepath
        except Exception as e:
            print(f"  Failed to download {video_id}: {e}")
            return None


def analyze_thumbnail_style(image_path):
    """Use Gemini to analyze the thumbnail style and generate a style brief."""
    with open(image_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("utf-8")

    prompt = """Analyze this YouTube thumbnail and describe its style in a structured format:

1. LAYOUT: Where is the face positioned? Where is the text? (e.g., "Face right, bold text left")
2. COLORS: What are the dominant colors? (e.g., "Orange text, dark background, blue accents")
3. TEXT STYLE: Font style, size relative to image, effects (glow, outline, shadow)
4. EMOTION: What facial expression or mood is conveyed?
5. ELEMENTS: Any icons, logos, screenshots, or props visible?
6. OVERALL VIBE: One-line description of the visual style

Be concise. Output as plain text, not markdown."""

    payload = {
        "contents": [{"parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": "image/jpeg", "data": img_data}}
        ]}],
        "generationConfig": {"maxOutputTokens": 500}
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    for candidate in result.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "text" in part:
                return part["text"]
    return "Analysis failed"


def detect_layout_type(style_description):
    """Determine layout type from style analysis."""
    desc = style_description.lower()
    if "face" in desc and "right" in desc and "text" in desc and "left" in desc:
        return "Face Right + Text Left"
    elif "face" in desc and "left" in desc and "text" in desc and "right" in desc:
        return "Face Left + Text Right"
    elif "center" in desc and "face" in desc:
        return "Center Face + Text Overlay"
    elif "split" in desc:
        return "Split Screen"
    elif "product" in desc or "screen" in desc or "device" in desc:
        return "Product Focus"
    else:
        return "Full Width Text + Background"


def scrape_channel(channel_info, max_videos=15):
    """Scrape thumbnails from a single channel."""
    name = channel_info["name"]
    channel_id = channel_info["channel_id"]

    print(f"\n{'='*60}")
    print(f"Scraping: {name}")
    print(f"{'='*60}")

    # Get recent videos
    videos = get_channel_videos(channel_id, max_videos)
    print(f"Found {len(videos)} recent videos")

    if not videos:
        return 0

    # Get view stats to find top performers
    video_ids = [v["video_id"] for v in videos]
    stats = get_video_stats(video_ids)

    # Sort by views (top performers first)
    for v in videos:
        v["views"] = stats.get(v["video_id"], 0)
    videos.sort(key=lambda x: x["views"], reverse=True)

    scraped = 0
    for i, video in enumerate(videos):
        print(f"\n  [{i+1}/{len(videos)}] {video['title'][:60]}...")
        print(f"  Views: {video['views']:,}")

        # Download thumbnail
        filepath = download_thumbnail(video["video_id"], video["thumbnail_url"], name)
        if not filepath:
            continue
        print(f"  Downloaded: {os.path.basename(filepath)}")

        # Analyze style (only for top 5 by views to save API calls)
        if i < 5:
            print(f"  Analyzing style...")
            try:
                style = analyze_thumbnail_style(filepath)
                layout = detect_layout_type(style)
                print(f"  Layout: {layout}")

                # Save to Airtable Templates table
                airtable_create("templates", {
                    "Template Name": f"{name} - {video['title'][:50]}",
                    "Source Channel": name,
                    "Source Video URL": f"https://youtube.com/watch?v={video['video_id']}",
                    "Style Description": style,
                    "Layout Type": layout,
                })
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"  Analysis error: {e}")

        scraped += 1

    # Update competitor record with scrape count
    airtable_update("competitors", channel_info["record_id"], {
        "Thumbnails Scraped": channel_info["scraped"] + scraped,
    })

    return scraped


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scrape competitor YouTube thumbnails")
    parser.add_argument("--channel", type=str, help="Filter to specific channel name")
    parser.add_argument("--max", type=int, default=15, help="Max videos per channel")
    args = parser.parse_args()

    print("Thumbnail Mate v1.0 - Competitor Scraper")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    channels = get_active_competitors(args.channel)
    print(f"\nFound {len(channels)} active competitor channels")

    total_scraped = 0
    for ch in channels:
        try:
            count = scrape_channel(ch, args.max)
            total_scraped += count
        except Exception as e:
            print(f"Error scraping {ch['name']}: {e}")

    print(f"\n{'='*60}")
    print(f"Done! Scraped {total_scraped} thumbnails total")
    print(f"Thumbnails saved to: {COMPETITOR_DIR}")
    print(f"Style analyses saved to Airtable: Thumbnail Templates")


if __name__ == "__main__":
    main()
