#!/usr/bin/env python3
"""
Thumbnail Pipeline - Generate 6 thumbnails + 6 titles

Mode 1: Template-based (3 thumbnails from your templates)
Mode 2: Competitor-based (3 thumbnails from top competitor styles)

Output: 6 thumbnails uploaded to Content Mate Airtable as attachments
        6 AI-generated YouTube titles

Usage:
    python3 run_pipeline.py                     # Full pipeline (both modes)
    python3 run_pipeline.py --mode template     # Only template-based
    python3 run_pipeline.py --mode competitor   # Only competitor-based
    python3 run_pipeline.py --scrape-faces      # Scrape face refs first
    python3 run_pipeline.py --cleanup           # Delete error records first
"""

import os
import sys
import json
import glob
import re
import time
import base64
import urllib.request
import argparse
from datetime import datetime

from config import (
    GEMINI_API_KEY, YOUTUBE_API_KEY, AIRTABLE_TOKEN,
    NANO_BANANA_MODEL, NANO_BANANA_PRO_MODEL, FACE_REFS_DIR,
    ANDY_TEMPLATES_DIR, COMPETITOR_DIR, PRODUCED_THUMBNAILS_DIR,
    OUTPUT_WIDTH, OUTPUT_HEIGHT,
    CONTENT_MATE_BASE, CONTENT_MATE_TABLE,
    DEFAULT_COMPETITOR_CHANNELS
)
from generate_thumbnail import (
    get_face_references, load_competitor_ref, save_and_upscale
)

# Add parent dir for youtube_publisher imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Error records to clean up
ERROR_RECORDS = []  # Add Airtable record IDs to clean up (e.g., ["recXXXXXXXXXXXXXX"])


# === Airtable helpers (Content Mate) ===

def content_mate_create(fields):
    """Create a record in Content Mate table."""
    url = f"https://api.airtable.com/v0/{CONTENT_MATE_BASE}/{CONTENT_MATE_TABLE}"
    payload = json.dumps({"records": [{"fields": fields}]}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def content_mate_delete(record_ids):
    """Delete records from Content Mate table."""
    params = "&".join([f"records[]={rid}" for rid in record_ids])
    url = f"https://api.airtable.com/v0/{CONTENT_MATE_BASE}/{CONTENT_MATE_TABLE}?{params}"
    req = urllib.request.Request(url, method="DELETE", headers={
        "Authorization": f"Bearer {AIRTABLE_TOKEN}"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


# === Generation helpers ===

def generate_single_with_title(prompt, face_refs, style_ref_data=None, model=None):
    """Generate a thumbnail and extract AI-suggested title from response.

    Returns: (image_bytes, title_text)
    """
    model = model or NANO_BANANA_PRO_MODEL
    parts = [{"text": prompt}]

    for ref in face_refs:
        parts.append({"inline_data": {"mime_type": ref["mime_type"], "data": ref["data"]}})

    if style_ref_data:
        parts.append({"inline_data": {
            "mime_type": style_ref_data["mime_type"],
            "data": style_ref_data["data"]
        }})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=180) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    image_data = None
    text_response = ""

    for candidate in result.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "inlineData" in part:
                image_data = base64.b64decode(part["inlineData"]["data"])
            elif "text" in part:
                text_response += part["text"]

    title = extract_title(text_response)
    return image_data, title


def extract_title(text):
    """Parse TITLE: from AI response text."""
    match = re.search(r'TITLE:\s*(.+?)(?:\n|$)', text)
    if match:
        return match.group(1).strip().strip('"')
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    return lines[0][:70] if lines else "Untitled Video"


def build_template_prompt():
    """Prompt for template-based generation (AI picks the title)."""
    return """You are creating a YouTube thumbnail AND title for the channel "YOUR_CHANNEL_NAME".

Channel niche: YOUR_CHANNEL_NICHE (e.g., AI automation, productivity tools, tech tutorials).

Instructions:
1. FIRST, suggest a compelling YouTube title (max 60 chars, clickable, curiosity-driven)
2. THEN create a thumbnail that matches that title

Format your text response EXACTLY as:
TITLE: [Your suggested title here]

Thumbnail requirements:
- Resolution: 1920x1080 (16:9 aspect ratio)
- Bold, large, attention-grabbing text on the thumbnail matching the title
- Use the provided face reference photo(s) — this person MUST appear prominently
- High contrast colors that pop on YouTube
- Clean, professional design
- Text must be readable even at small sizes

I've included a style reference thumbnail. Match its general layout, color scheme,
and visual energy, but create something with a COMPLETELY DIFFERENT topic and title.
Use MY face (from the face references) instead of anyone else's face."""


def build_competitor_prompt():
    """Prompt for competitor-based generation."""
    return """You are recreating a competitor's YouTube thumbnail style for the channel "YOUR_CHANNEL_NAME".

Channel niche: YOUR_CHANNEL_NICHE (e.g., AI automation, productivity tools, tech tutorials).

Instructions:
1. FIRST, suggest a compelling YouTube title (max 60 chars, clickable, curiosity-driven)
2. THEN create a thumbnail matching that title

Format your text response EXACTLY as:
TITLE: [Your suggested title here]

Thumbnail requirements:
- Resolution: 1920x1080 (16:9 aspect ratio)
- Bold, large text on the thumbnail
- Use the provided face reference photo(s) — this person MUST appear prominently
- High contrast, eye-catching colors
- Professional, clickable design

I've included a competitor's thumbnail as a STYLE reference ONLY.
Use the same general layout and visual approach, but:
- Use MY face (from the face reference photos) instead of theirs
- Create a NEW, DIFFERENT title about AI automation
- Make it slightly more polished and attention-grabbing"""


# === Mode 1: Template-based ===

def generate_template_thumbnails(face_refs):
    """Generate 3 thumbnails from your 3 templates."""
    print("\n" + "=" * 60)
    print("MODE 1: Template-Based Thumbnails")
    print("=" * 60)

    templates = sorted(glob.glob(os.path.join(ANDY_TEMPLATES_DIR, "*.png")))
    if not templates:
        print("ERROR: No templates found in", ANDY_TEMPLATES_DIR)
        return []

    prompt = build_template_prompt()
    results = []

    for i, template_path in enumerate(templates[:3]):
        label = chr(65 + i)  # A, B, C
        template_name = os.path.basename(template_path)
        print(f"\n  Generating Thumbnail {label} (style: {template_name})...")

        style_ref = load_competitor_ref(template_path)

        try:
            img_bytes, title = generate_single_with_title(prompt, face_refs, style_ref)
            if img_bytes:
                out_path = os.path.join(PRODUCED_THUMBNAILS_DIR, f"template_{label}.png")
                save_and_upscale(img_bytes, out_path)
                print(f"  Saved: template_{label}.png ({len(img_bytes):,} bytes)")
                print(f"  Title: {title}")
                results.append({
                    "path": out_path,
                    "title": title,
                    "source_type": "Template",
                    "source_ref": template_name,
                    "label": label
                })
            else:
                print(f"  Failed: No image returned")
        except Exception as e:
            print(f"  Error: {e}")

        if i < 2:
            time.sleep(3)

    print(f"\nTemplate mode: {len(results)}/3 thumbnails generated")
    return results


# === Mode 2: Competitor-based ===

def get_top_competitor_thumbnails(max_per_channel=5, top_n=3):
    """Find top competitor thumbnails by view count."""
    print("\n  Fetching competitor videos...")

    # Try using existing downloaded thumbnails first
    existing = glob.glob(os.path.join(COMPETITOR_DIR, "*", "*.jpg"))
    if existing and not YOUTUBE_API_KEY:
        print(f"  No YouTube API key — using {len(existing)} existing competitor thumbnails")
        # Pick 3 random ones
        import random
        selected = random.sample(existing, min(top_n, len(existing)))
        return [{"path": p, "name": os.path.basename(p)} for p in selected]

    if not YOUTUBE_API_KEY:
        print("  ERROR: No YouTube API key and no existing competitor thumbnails")
        return []

    # Import scraper functions
    from scrape_competitors import get_channel_videos, download_thumbnail, get_video_stats

    all_videos = []
    for ch in DEFAULT_COMPETITOR_CHANNELS:
        try:
            videos = get_channel_videos(ch["channel_id"], max_per_channel)
            for v in videos:
                v["channel_name"] = ch["name"]
            all_videos.extend(videos)
            print(f"  {ch['name']}: {len(videos)} videos")
        except Exception as e:
            print(f"  {ch['name']}: error - {e}")

    if not all_videos:
        return []

    # Get view stats
    video_ids = [v["video_id"] for v in all_videos]
    stats = get_video_stats(video_ids[:50])  # API limit
    for v in all_videos:
        v["views"] = stats.get(v["video_id"], 0)

    # Sort by views and take top N
    all_videos.sort(key=lambda x: x["views"], reverse=True)
    top_videos = all_videos[:top_n]

    # Download thumbnails
    results = []
    for v in top_videos:
        path = download_thumbnail(v["video_id"], v["thumbnail_url"], v["channel_name"])
        if path:
            results.append({
                "path": path,
                "name": f"{v['channel_name']} - {v['title'][:40]}",
                "views": v["views"]
            })
            print(f"  Top: {v['title'][:50]}... ({v['views']:,} views)")

    return results


def generate_competitor_thumbnails(face_refs):
    """Generate 3 thumbnails from top competitor styles."""
    print("\n" + "=" * 60)
    print("MODE 2: Competitor-Based Thumbnails")
    print("=" * 60)

    competitors = get_top_competitor_thumbnails()
    if not competitors:
        print("No competitor thumbnails available. Skipping Mode 2.")
        return []

    prompt = build_competitor_prompt()
    results = []

    for i, comp in enumerate(competitors[:3]):
        label = chr(68 + i)  # D, E, F (continuing from template A, B, C)
        print(f"\n  Generating Thumbnail {label} (style: {comp['name']})...")

        style_ref = load_competitor_ref(comp["path"])

        try:
            img_bytes, title = generate_single_with_title(prompt, face_refs, style_ref)
            if img_bytes:
                out_path = os.path.join(PRODUCED_THUMBNAILS_DIR, f"competitor_{label}.png")
                save_and_upscale(img_bytes, out_path)
                print(f"  Saved: competitor_{label}.png ({len(img_bytes):,} bytes)")
                print(f"  Title: {title}")
                results.append({
                    "path": out_path,
                    "title": title,
                    "source_type": "Competitor",
                    "source_ref": comp["name"],
                    "label": label
                })
            else:
                print(f"  Failed: No image returned")
        except Exception as e:
            print(f"  Error: {e}")

        if i < 2:
            time.sleep(3)

    print(f"\nCompetitor mode: {len(results)}/3 thumbnails generated")
    return results


# === Airtable upload ===

def upload_results_to_airtable(results):
    """Upload thumbnails + titles to Content Mate Airtable."""
    print("\n" + "=" * 60)
    print("Uploading to Airtable")
    print("=" * 60)

    for r in results:
        try:
            fields = {
                "📹 Video Title": r["title"],
                "Status": "📝 Draft",
                "Channel": "YOUR_CHANNEL_NAME",  # Replace with your channel name
                "Thumbnail Path": r["path"],
                "Thumbnail Folder": PRODUCED_THUMBNAILS_DIR,
            }

            record = content_mate_create(fields)
            record_id = record['records'][0]['id']
            print(f"  [{r['label']}] Created record {record_id}")
            print(f"       Title: {r['title']}")
            print(f"       Source: {r['source_type']} ({r['source_ref']})")

        except Exception as e:
            print(f"  [{r['label']}] Airtable error: {e}")


# === Cleanup ===

def cleanup_airtable():
    """Delete error records from Content Mate."""
    print("\nCleaning up Airtable error records...")
    try:
        result = content_mate_delete(ERROR_RECORDS)
        deleted = len(result.get("records", []))
        print(f"  Deleted {deleted} error records")
    except Exception as e:
        print(f"  Cleanup error: {e}")


# === Main ===

def main():
    parser = argparse.ArgumentParser(description="Thumbnail Pipeline")
    parser.add_argument("--mode", choices=["template", "competitor", "both"], default="both")
    parser.add_argument("--cleanup", action="store_true", help="Delete Airtable error records")
    parser.add_argument("--scrape-faces", action="store_true", help="Scrape face refs first")
    args = parser.parse_args()

    print("=" * 60)
    print("Thumbnail Pipeline")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Mode: {args.mode}")
    print("=" * 60)

    # Step 1: Optional face scraping
    if args.scrape_faces:
        from scrape_faces import scrape_andy_faces
        scrape_andy_faces()

    # Step 2: Optional cleanup
    if args.cleanup:
        cleanup_airtable()

    # Step 3: Verify face references
    face_refs = get_face_references(max_refs=3)
    if not face_refs:
        print("\nERROR: No face references found!")
        print(f"  Add face photos to: {FACE_REFS_DIR}")
        print(f"  Or run: python3 run_pipeline.py --scrape-faces")
        sys.exit(1)

    # Ensure output dir exists
    os.makedirs(PRODUCED_THUMBNAILS_DIR, exist_ok=True)

    results = []

    # Step 4: Mode 1 — Template-based
    if args.mode in ("template", "both"):
        template_results = generate_template_thumbnails(face_refs)
        results.extend(template_results)

    # Step 5: Mode 2 — Competitor-based
    if args.mode in ("competitor", "both"):
        competitor_results = generate_competitor_thumbnails(face_refs)
        results.extend(competitor_results)

    # Step 6: Upload to Airtable
    if results:
        upload_results_to_airtable(results)

    # Summary
    print("\n" + "=" * 60)
    print(f"DONE! Generated {len(results)} thumbnails")
    print("=" * 60)
    for r in results:
        print(f"  [{r['label']}] {r['title']}")
        print(f"       {r['path']}")
    print(f"\nOutput folder: {PRODUCED_THUMBNAILS_DIR}")
    print(f"Airtable: https://airtable.com/{CONTENT_MATE_BASE}/{CONTENT_MATE_TABLE}")


if __name__ == "__main__":
    main()
