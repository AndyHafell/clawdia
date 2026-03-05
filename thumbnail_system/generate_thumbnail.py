#!/usr/bin/env python3
"""
Thumbnail Mate v2.0 - Fast Parallel Thumbnail Generator

Generates YouTube thumbnails using Gemini image model with:
- Parallel generation (3 workers simultaneously instead of sequential)
- Parallel Drive uploads
- Auto SSL configuration (no manual export needed)
- Source image input (--source-image or --source-url)
- All face references loaded by default

Usage:
    python3 generate_thumbnail.py "My Video Title"
    python3 generate_thumbnail.py "My Video Title" --source-image path/to/thumb.png
    python3 generate_thumbnail.py "My Video Title" --source-url "https://i.ytimg.com/vi/XXX/maxresdefault.jpg"
    python3 generate_thumbnail.py "My Video Title" --model flash
    python3 generate_thumbnail.py "My Video Title" --count 3
"""

import http.client
import urllib.request
import urllib.error
import urllib.parse
import json
import os
import sys
import base64
import glob
import random
import time
import pickle
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

# Auto SSL fix — must run before any HTTPS calls
import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

from config import (
    GEMINI_API_KEY, AIRTABLE_TOKEN,
    NANO_BANANA_MODEL, NANO_BANANA_PRO_MODEL,
    BASE_DIR, FACE_REFS_DIR, OUTPUT_DIR,
    OUTPUT_WIDTH, OUTPUT_HEIGHT, NUM_OPTIONS,
    CONTENT_MATE_BASE, VIRAL_VIDEOS_TABLE, THUMBNAIL_GENERATIONS_TABLE,
)

MATE_OS_BASE = CONTENT_MATE_BASE
GENERATION_WORKERS = 3  # parallel Gemini calls (balances speed vs 503 risk)
UPLOAD_WORKERS = 6      # parallel Drive uploads

# ─── Airtable helpers ────────────────────────────────────────────────

_source_fields_ensured = False

def ensure_source_fields():
    """Create Source A-F attachment fields in Thumbnail Generations table (idempotent, runs once)."""
    global _source_fields_ensured
    if _source_fields_ensured:
        return
    for label in "ABCDEF":
        field_name = f"Source {label}"
        url = f"https://api.airtable.com/v0/meta/bases/{MATE_OS_BASE}/tables/{THUMBNAIL_GENERATIONS_TABLE}/fields"
        payload = json.dumps({"name": field_name, "type": "multipleAttachments"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={
            "Authorization": f"Bearer {AIRTABLE_TOKEN}",
            "Content-Type": "application/json"
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                json.loads(resp.read().decode("utf-8"))
            print(f"  Created field: {field_name}")
        except urllib.error.HTTPError as e:
            if e.code == 422:  # Field already exists — fine
                pass
            else:
                body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
                print(f"  Warning: Could not create field {field_name}: {e.code} {body[:200]}")
    _source_fields_ensured = True


_thumbnail_used_ensured = False

def ensure_thumbnail_used_field():
    """Create 'Thumbnail Used' checkbox field in Viral Videos table (idempotent, runs once)."""
    global _thumbnail_used_ensured
    if _thumbnail_used_ensured:
        return
    url = f"https://api.airtable.com/v0/meta/bases/{MATE_OS_BASE}/tables/{VIRAL_VIDEOS_TABLE}/fields"
    payload = json.dumps({
        "name": "Thumbnail Used",
        "type": "checkbox",
        "options": {"icon": "check", "color": "greenBright"},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            json.loads(resp.read().decode("utf-8"))
        print("  Created field: Thumbnail Used")
    except urllib.error.HTTPError as e:
        if e.code == 422:  # Already exists
            pass
        else:
            body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
            print(f"  Warning: Could not create Thumbnail Used field: {e.code} {body[:200]}")
    _thumbnail_used_ensured = True


def mark_thumbnails_used(record_ids):
    """Mark viral thumbnails as used in Airtable."""
    ensure_thumbnail_used_field()
    for rec_id in record_ids:
        url = f"https://api.airtable.com/v0/{MATE_OS_BASE}/{VIRAL_VIDEOS_TABLE}/{rec_id}"
        payload = json.dumps({"fields": {"Thumbnail Used": True}}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={
            "Authorization": f"Bearer {AIRTABLE_TOKEN}",
            "Content-Type": "application/json"
        })
        req.get_method = lambda: "PATCH"
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp.read()
            print(f"  Marked as used: {rec_id}")
        except Exception as e:
            print(f"  Warning: Could not mark {rec_id} as used: {e}")


def airtable_create_gen(fields):
    url = f"https://api.airtable.com/v0/{MATE_OS_BASE}/{THUMBNAIL_GENERATIONS_TABLE}"
    payload = json.dumps({"records": [{"fields": fields}]}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def airtable_update_gen(record_id, fields):
    url = f"https://api.airtable.com/v0/{MATE_OS_BASE}/{THUMBNAIL_GENERATIONS_TABLE}/{record_id}"
    payload = json.dumps({"fields": fields}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    })
    req.get_method = lambda: "PATCH"
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


# Legacy wrappers
def airtable_create(table_key, fields):
    return airtable_create_gen(fields)

def airtable_update(table_key, record_id, fields):
    return airtable_update_gen(record_id, fields)


# ─── Google Drive upload ─────────────────────────────────────────────

def _get_drive_service():
    """Build and cache a Drive service with auto-refresh."""
    try:
        from googleapiclient.discovery import build
    except ImportError:
        print("  Warning: google-api-python-client not installed")
        return None

    token_file = os.path.join(os.path.dirname(BASE_DIR), "youtube_token.pickle")
    if not os.path.exists(token_file):
        print(f"  Warning: No token file at {token_file}")
        return None

    with open(token_file, "rb") as f:
        creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            with open(token_file, "wb") as f:
                pickle.dump(creds, f)
        else:
            print("  Warning: Drive credentials expired — run youtube_publisher.py to re-auth")
            return None

    return build("drive", "v3", credentials=creds)


def upload_to_drive(file_path, drive_service=None):
    """Upload a file to Google Drive and return a public shareable link.
    Retries up to 3 times on failure."""
    try:
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        return None

    filename = os.path.basename(file_path)

    for attempt in range(3):
        try:
            # Build a fresh service each attempt to avoid stale connections
            drive = drive_service if attempt == 0 else _get_drive_service()
            if not drive:
                drive = _get_drive_service()
            if not drive:
                return None

            media = MediaFileUpload(file_path, mimetype="image/png", resumable=True,
                                    chunksize=2 * 1024 * 1024)
            uploaded = drive.files().create(
                body={"name": filename},
                media_body=media,
                fields="id"
            ).execute()

            file_id = uploaded.get("id")
            drive.permissions().create(
                fileId=file_id,
                body={"type": "anyone", "role": "reader"}
            ).execute()

            link = f"https://drive.google.com/uc?export=download&id={file_id}"
            print(f"    Uploaded: {filename}")
            return link

        except Exception as e:
            if attempt < 2:
                wait = 5 * (attempt + 1)
                print(f"    Upload retry {attempt + 1}/3 for {filename}: {e}")
                time.sleep(wait)
            else:
                print(f"    Drive upload failed after 3 attempts: {filename}: {e}")
                return None


# ─── Face references ─────────────────────────────────────────────────

def get_face_references():
    """Load ALL face reference images from the face_references folder."""
    patterns = ["*.jpg", "*.jpeg", "*.png", "*.webp"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(FACE_REFS_DIR, p)))

    if not files:
        print("WARNING: No face references found in face_references/ folder!")
        return []

    refs = []
    for f in sorted(files):
        with open(f, "rb") as img_file:
            data = base64.b64encode(img_file.read()).decode("utf-8")
            ext = f.lower().rsplit(".", 1)[-1]
            mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
            refs.append({"mime_type": mime, "data": data, "path": f})

    print(f"Loaded {len(refs)} face references: {[os.path.basename(r['path']) for r in refs]}")
    return refs


# ─── Viral thumbnails from Airtable ─────────────────────────────────

def get_viral_thumbnails(count=None):
    """Fetch top viral thumbnail images from Mate OS, sorted by Outlier Score.
    Filters out thumbnails already marked as used."""
    count = count or NUM_OPTIONS
    ensure_thumbnail_used_field()
    filter_formula = urllib.parse.quote("NOT({Thumbnail Used})")
    url = (
        f"https://api.airtable.com/v0/{CONTENT_MATE_BASE}/{VIRAL_VIDEOS_TABLE}"
        f"?fields[]=Thumbnail&fields[]=Title&fields[]=Outlier%20Score"
        f"&sort[0][field]=Outlier%20Score&sort[0][direction]=desc&maxRecords=20"
        f"&filterByFormula={filter_formula}"
    )
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AIRTABLE_TOKEN}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    candidates = []
    for rec in data.get("records", []):
        f = rec["fields"]
        attachments = f.get("Thumbnail", [])
        if attachments:
            candidates.append({
                "record_id": rec["id"],
                "title": f.get("Title", ""),
                "url": attachments[0]["url"],
                "score": f.get("Outlier Score", 0),
            })

    if not candidates:
        print("WARNING: No unused viral thumbnails found. All may be marked as used.")
        print("  Tip: Uncheck 'Thumbnail Used' in Viral Videos table to reuse thumbnails.")
        return []

    top = candidates[:10]
    selected = random.sample(top, min(count, len(top)))

    # Download thumbnails in parallel
    print(f"Downloading {len(selected)} viral thumbnails ({len(candidates)} unused available)...")

    def _download(item):
        try:
            with urllib.request.urlopen(item["url"], timeout=15) as resp:
                raw = resp.read()
            return {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(raw).decode("utf-8"),
                "title": item["title"],
                "record_id": item["record_id"],
            }
        except Exception as e:
            print(f"  Warning: Failed to download {item['title'][:40]}: {e}")
            return None

    refs = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(_download, item): item for item in selected}
        for future in as_completed(futures):
            result = future.result()
            if result:
                refs.append(result)
                print(f"  Got: {result['title'][:60]}")

    return refs


# ─── Source image loading ────────────────────────────────────────────

def load_source_image(path_or_url):
    """Load a single source image from a local file path or URL."""
    if path_or_url.startswith(("http://", "https://")):
        print(f"Downloading source image from URL...")
        with urllib.request.urlopen(path_or_url, timeout=30) as resp:
            raw = resp.read()
    else:
        path = os.path.expanduser(path_or_url)
        if not os.path.exists(path):
            print(f"ERROR: Source image not found: {path}")
            sys.exit(1)
        with open(path, "rb") as f:
            raw = f.read()

    ext = path_or_url.lower().rsplit(".", 1)[-1]
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
    return {
        "mime_type": mime,
        "data": base64.b64encode(raw).decode("utf-8"),
        "title": os.path.basename(path_or_url),
    }


# ─── Core generation ─────────────────────────────────────────────────

def generate_single(viral_ref, face_refs, model=None, custom_prompt=None):
    """Generate a single thumbnail inspired by a viral thumbnail with your face."""
    model = model or NANO_BANANA_PRO_MODEL
    prompt = custom_prompt or "Remake the YouTube thumbnail with my face. Output must be 16:9 aspect ratio (1920x1080)."

    parts = [
        {"text": prompt},
        {"inline_data": {"mime_type": viral_ref["mime_type"], "data": viral_ref["data"]}},
    ]
    for ref in face_refs:
        parts.append({"inline_data": {"mime_type": ref["mime_type"], "data": ref["data"]}})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    data = json.dumps(payload).encode("utf-8")

    for attempt in range(4):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code == 503 and attempt < 3:
                wait = 15 * (attempt + 1)
                print(f"  503 capacity error, retrying in {wait}s (attempt {attempt + 1}/4)...")
                time.sleep(wait)
            else:
                raise
        except (ConnectionError, OSError, urllib.error.URLError, http.client.RemoteDisconnected) as e:
            if attempt < 3:
                wait = 15 * (attempt + 1)
                print(f"  Connection error, retrying in {wait}s (attempt {attempt + 1}/4): {e}")
                time.sleep(wait)
            else:
                raise

    for candidate in result.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
            elif "text" in part:
                print(f"  AI note: {part['text'][:100]}")

    return None


def save_and_upscale(img_bytes, output_path):
    """Save image and upscale to 1920x1080."""
    raw_path = output_path.replace(".png", "_raw.png")
    with open(raw_path, "wb") as f:
        f.write(img_bytes)

    img = Image.open(raw_path)
    if img.size != (OUTPUT_WIDTH, OUTPUT_HEIGHT):
        img = img.resize((OUTPUT_WIDTH, OUTPUT_HEIGHT), Image.LANCZOS)

    img.save(output_path, "PNG", quality=95)
    os.remove(raw_path)
    return output_path


# ─── Main generation pipeline ────────────────────────────────────────

def generate_thumbnails(title, model=None, source_image=None, source_url=None, count=None, skip_airtable=False):
    """Generate multiple thumbnail options for a video title.

    Args:
        title: Video title for the Airtable record
        model: Gemini model to use (default: Nano Banana Pro)
        source_image: Path to a local image to use as source for ALL options
        source_url: URL to download an image to use as source for ALL options
        count: Number of options to generate (default: NUM_OPTIONS from config)
        skip_airtable: If True, skip creating Airtable record and Drive uploads
    """
    num = count or NUM_OPTIONS
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)[:50].strip()
    session_dir = os.path.join(OUTPUT_DIR, f"{timestamp}_{safe_title}")
    os.makedirs(session_dir, exist_ok=True)

    model = model or NANO_BANANA_PRO_MODEL

    print(f"\nThumbnail Mate v2.0 - Fast Parallel Generator")
    print(f"Title: {title}")
    print(f"Output: {session_dir}")
    print(f"Model: {model}")
    print(f"Options: {num}")

    t0 = time.time()

    # Load face references (ALL of them)
    face_refs = get_face_references()

    # Load source images — either a single source or viral thumbnails
    if source_image or source_url:
        src = load_source_image(source_image or source_url)
        viral_refs = [src] * num  # same source for all options
        source_label = src["title"]
        print(f"Source: {source_label}")
    else:
        viral_refs = get_viral_thumbnails(count=num)
        source_label = "Viral Videos (top by Outlier Score)"
        if not viral_refs:
            print("ERROR: No viral thumbnails available. Check Viral Videos table.")
            return [], session_dir

    # Save source thumbnails for paper trail
    source_paths = {}
    for i in range(min(num, len(viral_refs))):
        label = chr(65 + i)
        source_path = os.path.join(session_dir, f"source_{label}.png")
        raw_bytes = base64.b64decode(viral_refs[i]["data"])
        with open(source_path, "wb") as f:
            f.write(raw_bytes)
        source_paths[label] = source_path
    print(f"Saved {len(source_paths)} source thumbnails for paper trail")

    # Mark viral thumbnails as used in Airtable (so next run picks fresh ones)
    if not (source_image or source_url):
        used_ids = list(dict.fromkeys(
            ref.get("record_id") for ref in viral_refs if ref.get("record_id")
        ))
        if used_ids:
            print(f"Marking {len(used_ids)} viral thumbnails as used...")
            mark_thumbnails_used(used_ids)

    print(f"\nGenerating {num} options in parallel ({GENERATION_WORKERS} workers)...")

    # ── Parallel generation ──────────────────────────────────────
    def _generate_one(i):
        label = chr(65 + i)
        viral_ref = viral_refs[i % len(viral_refs)]
        source_title = viral_ref.get("title", "source")[:50]
        print(f"  Starting Option {label} (from: {source_title})...")
        t_start = time.time()
        try:
            img_bytes = generate_single(viral_ref, face_refs, model)
            if img_bytes:
                output_path = os.path.join(session_dir, f"option_{label}.png")
                save_and_upscale(img_bytes, output_path)
                elapsed = time.time() - t_start
                print(f"  Option {label} done ({elapsed:.0f}s, {len(img_bytes):,} bytes)")
                return {"label": label, "path": output_path, "size": len(img_bytes), "inspired_by": source_title}
            else:
                print(f"  Option {label} failed: no image returned")
                return None
        except Exception as e:
            print(f"  Option {label} error: {e}")
            return None

    options = []
    with ThreadPoolExecutor(max_workers=GENERATION_WORKERS) as pool:
        futures = {pool.submit(_generate_one, i): i for i in range(num)}
        for future in as_completed(futures):
            result = future.result()
            if result:
                options.append(result)

    # Sort by label so they're in order A, B, C...
    options.sort(key=lambda o: o["label"])

    gen_time = time.time() - t0
    print(f"\nGeneration complete: {len(options)}/{num} succeeded in {gen_time:.0f}s")

    # ── Airtable record + Drive uploads ────────────────────────
    if options and not skip_airtable:
        # Ensure Source A-F fields exist in Airtable (one-time setup)
        ensure_source_fields()

        face_ref_names = [os.path.basename(r["path"]) for r in face_refs]
        inspired_by = ", ".join(o["inspired_by"][:40] for o in options)
        record = airtable_create_gen({
            "Video Title": title,
            "Prompt Used": "Remake the YouTube thumbnail with my face.",
            "Face Refs Used": ", ".join(face_ref_names),
            "Template Used": f"Viral: {inspired_by}"[:100],
            "Status": "Awaiting Review",
        })
        record_id = record["records"][0]["id"]

        drive_service = _get_drive_service()

        # Upload generated thumbnails
        print(f"\nUploading {len(options)} generated thumbnails to Drive...")
        attachment_fields = {}
        for opt in options:
            drive_url = upload_to_drive(opt["path"], drive_service)
            if drive_url:
                attachment_fields[f"Option {opt['label']}"] = [{"url": drive_url}]

        # Upload source thumbnails (paper trail)
        print(f"Uploading {len(source_paths)} source thumbnails to Drive...")
        for label, source_path in source_paths.items():
            # Only upload source if we successfully generated that option
            if any(o["label"] == label for o in options):
                src_drive_url = upload_to_drive(source_path, drive_service)
                if src_drive_url:
                    attachment_fields[f"Source {label}"] = [{"url": src_drive_url}]

        if attachment_fields:
            generated_count = sum(1 for k in attachment_fields if k.startswith("Option"))
            source_count = sum(1 for k in attachment_fields if k.startswith("Source"))
            for attempt in range(3):
                try:
                    airtable_update_gen(record_id, attachment_fields)
                    print(f"Airtable updated: {generated_count} generated + {source_count} sources")
                    break
                except Exception as e:
                    if attempt < 2:
                        wait = 5 * (attempt + 1)
                        print(f"  Airtable retry {attempt + 1}/3: {e}")
                        time.sleep(wait)
                    else:
                        print(f"Warning: Airtable update failed after 3 attempts: {e}")
                        print(f"  Record ID: {record_id} — update manually if needed")
    elif options and skip_airtable:
        print(f"\n  Skipping Airtable/Drive (skip_airtable=True)")

    total_time = time.time() - t0
    print(f"\n{'='*60}")
    print(f"Generated {len(options)} thumbnails in {total_time:.0f}s")
    print(f"Output: {session_dir}")
    for opt in options:
        print(f"  Option {opt['label']}: {opt['path']}")

    return options, session_dir


# ─── CLI ─────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate YouTube thumbnails (v2.0 — parallel)")
    parser.add_argument("title", type=str, help="Video title")
    parser.add_argument("--model", type=str, choices=["flash", "pro"], default="pro",
                        help="Model: flash or pro (default: pro)")
    parser.add_argument("--source-image", type=str, default=None,
                        help="Local image file to use as source for all options")
    parser.add_argument("--source-url", type=str, default=None,
                        help="URL of image to use as source for all options")
    parser.add_argument("--count", type=int, default=None,
                        help=f"Number of options to generate (default: {NUM_OPTIONS})")
    args = parser.parse_args()

    model = NANO_BANANA_MODEL if args.model == "flash" else NANO_BANANA_PRO_MODEL

    generate_thumbnails(
        title=args.title,
        model=model,
        source_image=args.source_image,
        source_url=args.source_url,
        count=args.count,
    )


if __name__ == "__main__":
    main()
