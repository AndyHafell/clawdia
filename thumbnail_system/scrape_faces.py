#!/usr/bin/env python3
"""
Scrape your YouTube channel thumbnails and crop face references.

Uses YouTube RSS feed (no API key needed) to find recent videos,
downloads maxres thumbnails, and crops faces using OpenCV.

Usage:
    python3 scrape_faces.py
    python3 scrape_faces.py --max 20
"""

import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
import cv2
import numpy as np
from datetime import datetime

from config import FACE_REFS_DIR

ANDY_CHANNEL_ID = "YOUR_YOUTUBE_CHANNEL_ID"  # Replace with your YouTube channel ID (format: UC...)
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={}"


def get_channel_video_ids(channel_id, max_videos=15):
    """Fetch video IDs from YouTube RSS feed (no API key needed)."""
    url = RSS_URL.format(channel_id)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml_data = resp.read().decode("utf-8")

    root = ET.fromstring(xml_data)
    ns = {"yt": "http://www.youtube.com/xml/schemas/2015", "atom": "http://www.w3.org/2005/Atom"}

    video_ids = []
    for entry in root.findall("atom:entry", ns):
        vid_el = entry.find("yt:videoId", ns)
        if vid_el is not None:
            video_ids.append(vid_el.text)
        if len(video_ids) >= max_videos:
            break

    return video_ids


def download_thumbnail(video_id, output_dir):
    """Download maxresdefault thumbnail for a video."""
    filepath = os.path.join(output_dir, f"thumb_{video_id}.jpg")
    if os.path.exists(filepath):
        return filepath

    urls = [
        f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
    ]

    for url in urls:
        try:
            urllib.request.urlretrieve(url, filepath)
            if os.path.getsize(filepath) > 5000:
                return filepath
        except Exception:
            continue

    return None


def detect_and_crop_faces(image_path, output_dir, padding=0.4):
    """Detect faces with OpenCV and crop with padding.

    Returns list of saved face crop paths.
    """
    img = cv2.imread(image_path)
    if img is None:
        return []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img.shape[:2]

    cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    face_cascade = cv2.CascadeClassifier(cascade_path)

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

    if len(faces) == 0:
        return []

    # Take the largest face (most likely the main person)
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, fw, fh = faces[0]

    # Add padding
    pad_x = int(fw * padding)
    pad_y = int(fh * padding)
    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(w, x + fw + pad_x)
    y2 = min(h, y + fh + pad_y)

    crop = img[y1:y2, x1:x2]

    # Extract video_id from filename
    basename = os.path.basename(image_path)
    video_id = basename.replace("thumb_", "").replace(".jpg", "")
    out_path = os.path.join(output_dir, f"face_{video_id}.jpg")

    cv2.imwrite(out_path, crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return [out_path]


def scrape_andy_faces(channel_id=None, max_videos=15):
    """Main: scrape channel thumbnails and crop faces."""
    channel_id = channel_id or ANDY_CHANNEL_ID
    os.makedirs(FACE_REFS_DIR, exist_ok=True)
    tmp_dir = os.path.join(FACE_REFS_DIR, "_thumbnails_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    print(f"Face Reference Scraper")
    print(f"Channel: {channel_id}")
    print(f"Output: {FACE_REFS_DIR}")
    print()

    # Get video IDs
    print("Fetching video IDs from RSS feed...")
    video_ids = get_channel_video_ids(channel_id, max_videos)
    print(f"Found {len(video_ids)} videos")

    faces_saved = 0
    for i, vid in enumerate(video_ids):
        # Skip if face already exists
        face_path = os.path.join(FACE_REFS_DIR, f"face_{vid}.jpg")
        if os.path.exists(face_path):
            print(f"  [{i+1}/{len(video_ids)}] {vid} - already cropped, skipping")
            faces_saved += 1
            continue

        # Download thumbnail
        thumb_path = download_thumbnail(vid, tmp_dir)
        if not thumb_path:
            print(f"  [{i+1}/{len(video_ids)}] {vid} - download failed")
            continue

        # Detect and crop face
        crops = detect_and_crop_faces(thumb_path, FACE_REFS_DIR)
        if crops:
            print(f"  [{i+1}/{len(video_ids)}] {vid} - face cropped!")
            faces_saved += 1
        else:
            print(f"  [{i+1}/{len(video_ids)}] {vid} - no face detected")

    # Clean up temp thumbnails
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\nDone! {faces_saved} face references saved to {FACE_REFS_DIR}")
    return faces_saved


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scrape face references from YouTube channel")
    parser.add_argument("--max", type=int, default=15, help="Max videos to process")
    parser.add_argument("--channel", type=str, default=ANDY_CHANNEL_ID, help="Channel ID")
    args = parser.parse_args()

    scrape_andy_faces(args.channel, args.max)
