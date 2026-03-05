#!/usr/bin/env python3
"""
Thumbnail Originality Transformer

Takes generated thumbnails from a previous run and creates 3 original
variations of each — yielding packages of 4 (1 source + 3 ours).

Output folder naming ensures they sort together:
  A0_source.png, A1_v1.png, A2_v2.png, A3_v3.png,
  B0_source.png, B1_v1.png, B2_v2.png, B3_v3.png, ...

Usage:
    python3 transform_thumbnail.py "Video Title" --latest
    python3 transform_thumbnail.py "Video Title" --session-dir path/to/session
    python3 transform_thumbnail.py "Video Title" --latest --variations 1
"""

import http.client
import urllib.request
import urllib.error
import json
import os
import sys
import base64
import shutil
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Auto SSL fix
import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

from config import (
    GEMINI_API_KEY, AIRTABLE_TOKEN,
    NANO_BANANA_MODEL, NANO_BANANA_PRO_MODEL,
    BASE_DIR, FACE_REFS_DIR, OUTPUT_DIR,
    OUTPUT_WIDTH, OUTPUT_HEIGHT,
    CONTENT_MATE_BASE, THUMBNAIL_GENERATIONS_TABLE,
)
from generate_thumbnail import (
    get_face_references,
    generate_single,
    save_and_upscale,
    upload_to_drive,
    _get_drive_service,
    airtable_create_gen,
    airtable_update_gen,
    ensure_source_fields,
)

TRANSFORM_WORKERS = 3
DEFAULT_VARIATIONS = 3  # 3 variations per source thumbnail

TRANSFORM_PROMPT = """Recreate this YouTube thumbnail with changes to make it original and about MY video.

MY VIDEO TITLE: {title}

KEEP EXACTLY THE SAME:
- The person's face, expression, and position
- The overall layout and composition structure
- The general energy and vibe

MAKE THESE SPECIFIC CHANGES:
- Change the person's shirt to a plain white t-shirt (ALWAYS white, never black or any other color)
- REPLACE ALL TEXT with short, catchy phrases about MY video title above — do NOT keep the original text (it's about a different topic)
- Style all text in Montserrat Black font with a vertical gradient from bright yellow (#FFD700) at top to deep golden (#E8A800) at bottom
- Text is MAX 4 words (ideally 2-3) — punchy hook only
- Place text at the TOP of the thumbnail — bold and large
- Background should be dark grey/black with a subtle blue tint — simplify and make cleaner
- Remove any unnecessary icons, badges, gear icons, clock icons, or decorative clutter
- If key logos are present, keep them in the same location but alter them slightly

CRITICAL RULES:
- Maximum 2-3 visual elements total besides the person and text
- Do NOT add red X marks, crossed-out symbols, or 'X over something' elements
- Do NOT add extra decorative icons that weren't essential to the original
- Leave generous negative space — do NOT overcrowd the frame
- The thumbnail must be readable at small size (150px height)

This should look like a polished original thumbnail for MY video, not a copy of the reference.
Output must be 16:9 aspect ratio (1920x1080)."""


def _load_feedback_rules(system_key=None):
    """Load feedback memory rules from JSON and format for prompt injection."""
    memory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feedback_memory.json")
    if not os.path.exists(memory_path):
        return ""

    try:
        with open(memory_path, "r") as f:
            memory = json.load(f)
    except Exception:
        return ""

    rules = memory.get("global_rules", {})
    always_rules = rules.get("always", [])
    avoid_rules = rules.get("avoid", [])

    # Add system-specific notes
    system_notes = []
    if system_key:
        sys_specific = memory.get("system_specific", {}).get(system_key, {})
        system_notes = sys_specific.get("notes", [])

    if not always_rules and not avoid_rules and not system_notes:
        return ""

    text = "\n\nLEARNED RULES FROM PREVIOUS FEEDBACK (follow these strictly):\n"
    if always_rules:
        text += "\nALWAYS:\n"
        for rule in always_rules:
            text += f"- {rule}\n"
    if avoid_rules:
        text += "\nNEVER:\n"
        for rule in avoid_rules:
            text += f"- {rule}\n"
    if system_notes:
        text += "\nSYSTEM-SPECIFIC NOTES:\n"
        for note in system_notes:
            text += f"- {note}\n"

    return text


# ─── Session finder ──────────────────────────────────────────────────

def find_session_dir(session_dir=None, latest=False):
    """Find the input session directory."""
    if session_dir:
        path = os.path.expanduser(session_dir)
        if not os.path.isdir(path):
            print(f"ERROR: Session directory not found: {path}")
            sys.exit(1)
        return path
    if latest:
        try:
            # Find latest session that is NOT an "original_" transform output
            sessions = sorted(
                d for d in os.listdir(OUTPUT_DIR)
                if os.path.isdir(os.path.join(OUTPUT_DIR, d))
                and not d.startswith(".")
                and "_original_" not in d
                and "_packaged_" not in d
            )
        except FileNotFoundError:
            print(f"ERROR: Output directory not found: {OUTPUT_DIR}")
            sys.exit(1)
        if not sessions:
            print("ERROR: No generation sessions found in output directory")
            sys.exit(1)
        return os.path.join(OUTPUT_DIR, sessions[-1])
    print("ERROR: Provide --session-dir or --latest")
    sys.exit(1)


def load_session_thumbnails(session_dir):
    """Load option_A-F.png and source_A-F.png from a session directory."""
    thumbnails = []
    for label in "ABCDEF":
        opt_path = os.path.join(session_dir, f"option_{label}.png")
        src_path = os.path.join(session_dir, f"source_{label}.png")
        if os.path.exists(opt_path):
            with open(opt_path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
            thumbnails.append({
                "label": label,
                "path": opt_path,
                "source_path": src_path if os.path.exists(src_path) else None,
                "data": data,
                "mime_type": "image/png",
            })
    return thumbnails


# ─── Transformation pipeline ────────────────────────────────────────

def transform_thumbnails(thumbnails, face_refs, out_dir, model=None, variations=DEFAULT_VARIATIONS, title=""):
    """Generate multiple original variations for each input thumbnail.

    Creates `variations` transforms per source. Output naming:
        A0_source.png, A1_v1.png, A2_v2.png, A3_v3.png, ...
    """
    model = model or NANO_BANANA_PRO_MODEL

    # Format the transform prompt with title + feedback rules
    formatted_prompt = TRANSFORM_PROMPT.format(title=title or "YouTube Video")
    formatted_prompt += _load_feedback_rules("system_1_transform")

    # Build list of all jobs: (thumb_index, variation_number)
    jobs = []
    for i, thumb in enumerate(thumbnails):
        for v in range(variations):
            jobs.append((i, v))

    total = len(jobs)
    print(f"  Total jobs: {total} ({len(thumbnails)} thumbnails × {variations} variations)")

    def _transform_one(job):
        thumb_idx, var_num = job
        thumb = thumbnails[thumb_idx]
        label = thumb["label"]
        var_label = f"{label}{var_num + 1}_v{var_num + 1}"
        print(f"  Generating {var_label} (from {label})...")
        t_start = time.time()
        try:
            viral_ref = {
                "mime_type": thumb["mime_type"],
                "data": thumb["data"],
            }
            img_bytes = generate_single(viral_ref, face_refs, model, custom_prompt=formatted_prompt)
            if img_bytes:
                output_path = os.path.join(out_dir, f"{label}{var_num + 1}_v{var_num + 1}.png")
                save_and_upscale(img_bytes, output_path)
                elapsed = time.time() - t_start
                print(f"  {var_label} done ({elapsed:.0f}s, {len(img_bytes):,} bytes)")
                return {
                    "label": label,
                    "var_num": var_num + 1,
                    "path": output_path,
                    "size": len(img_bytes),
                    "source_label": label,
                }
            else:
                print(f"  {var_label} failed: no image returned")
                return None
        except Exception as e:
            print(f"  {var_label} error: {e}")
            return None

    results = []
    with ThreadPoolExecutor(max_workers=TRANSFORM_WORKERS) as pool:
        futures = {pool.submit(_transform_one, job): job for job in jobs}
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    results.sort(key=lambda r: (r["label"], r["var_num"]))
    return results


# ─── Package output folder ─────────────────────────────────────────

def package_output(thumbnails, results, out_dir):
    """Copy source thumbnails into the output folder with sorted naming.

    Final folder structure (sorted by filename):
        A0_source.png     ← original viral thumbnail
        A1_v1.png         ← our variation 1
        A2_v2.png         ← our variation 2
        A3_v3.png         ← our variation 3
        B0_source.png
        B1_v1.png
        ...
    """
    source_paths = {}
    for thumb in thumbnails:
        label = thumb["label"]
        # Only include if we have at least one result for this label
        if any(r["label"] == label for r in results):
            source_dest = os.path.join(out_dir, f"{label}0_source.png")
            # Copy the viral source thumbnail (not the generated option)
            if thumb.get("source_path") and os.path.exists(thumb["source_path"]):
                shutil.copy2(thumb["source_path"], source_dest)
            else:
                # Fallback: copy the generated option as source reference
                shutil.copy2(thumb["path"], source_dest)
            source_paths[label] = source_dest
            print(f"  {label}0_source.png ← source")

    return source_paths


# ─── Upload + Airtable ──────────────────────────────────────────────

def upload_and_record(title, results, source_paths, face_refs):
    """Upload to Drive and create Airtable record."""
    ensure_source_fields()

    face_ref_names = [os.path.basename(r["path"]) for r in face_refs]
    labels_used = sorted(set(r["label"] for r in results))

    record = airtable_create_gen({
        "Video Title": f"Original: {title}",
        "Prompt Used": "Originality Transformer (3 variations per source)",
        "Face Refs Used": ", ".join(face_ref_names),
        "Template Used": f"Transformed: {', '.join(labels_used)}"[:100],
        "Status": "Awaiting Review",
    })
    record_id = record["records"][0]["id"]
    print(f"  Airtable record: {record_id}")

    drive_service = _get_drive_service()
    attachment_fields = {}

    # Upload generated originals — group by source label
    # Use Option A for first source's variations, Option B for second, etc.
    for label_idx, label in enumerate(labels_used):
        label_results = [r for r in results if r["label"] == label]
        option_label = chr(65 + label_idx)  # A, B, C...

        # Collect all variation URLs for this option
        urls = []
        for result in label_results:
            drive_url = upload_to_drive(result["path"], drive_service)
            if drive_url:
                urls.append({"url": drive_url})
                print(f"    Uploaded: {os.path.basename(result['path'])}")

        if urls:
            attachment_fields[f"Option {option_label}"] = urls

        # Upload source
        if label in source_paths:
            src_url = upload_to_drive(source_paths[label], drive_service)
            if src_url:
                attachment_fields[f"Source {option_label}"] = [{"url": src_url}]
                print(f"    Uploaded: {os.path.basename(source_paths[label])}")

    if attachment_fields:
        for attempt in range(3):
            try:
                airtable_update_gen(record_id, attachment_fields)
                print(f"Airtable updated with all attachments")
                break
            except Exception as e:
                if attempt < 2:
                    wait = 5 * (attempt + 1)
                    print(f"  Airtable retry {attempt + 1}/3: {e}")
                    time.sleep(wait)
                else:
                    print(f"Warning: Airtable update failed after 3 attempts: {e}")
                    print(f"  Record ID: {record_id} — update manually if needed")

    return record_id


# ─── Main pipeline ──────────────────────────────────────────────────

def transform_pipeline(title, session_dir=None, latest=False, model=None, variations=DEFAULT_VARIATIONS, skip_airtable=False):
    """Full originality transformation pipeline."""
    t0 = time.time()

    print(f"\nThumbnail Originality Transformer")
    print(f"Title: {title}")
    print(f"Variations per source: {variations}")

    # Step 1: Find session
    src_dir = find_session_dir(session_dir, latest)
    print(f"Input session: {src_dir}")

    # Step 2: Load thumbnails
    thumbnails = load_session_thumbnails(src_dir)
    print(f"Found {len(thumbnails)} thumbnails: {[t['label'] for t in thumbnails]}")

    if not thumbnails:
        print("ERROR: No thumbnails found in session directory")
        sys.exit(1)

    # Step 3: Load face references
    face_refs = get_face_references()

    # Step 4: Create packaged output directory
    model = model or NANO_BANANA_PRO_MODEL
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)[:50].strip()
    out_dir = os.path.join(OUTPUT_DIR, f"{timestamp}_packaged_{safe_title}")
    os.makedirs(out_dir, exist_ok=True)
    print(f"Output: {out_dir}")

    # Step 5: Transform (multiple variations per input)
    total_jobs = len(thumbnails) * variations
    print(f"\nGenerating {total_jobs} variations ({len(thumbnails)} sources × {variations} each, {TRANSFORM_WORKERS} workers)...")
    results = transform_thumbnails(thumbnails, face_refs, out_dir, model, variations, title=title)

    if not results:
        print("ERROR: All generation attempts failed. No output produced.")
        sys.exit(1)

    gen_time = time.time() - t0
    print(f"\nTransformation complete: {len(results)}/{total_jobs} succeeded in {gen_time:.0f}s")

    # Step 6: Package — copy source thumbnails with sorted naming
    print(f"\nPackaging output folder...")
    source_paths = package_output(thumbnails, results, out_dir)

    # Step 7: Upload and record
    if skip_airtable:
        print(f"\n  Skipping Airtable/Drive upload (skip_airtable=True)")
        record_id = None
    else:
        print(f"\nUploading to Drive and Airtable...")
        record_id = upload_and_record(title, results, source_paths, face_refs)

    total_time = time.time() - t0
    print(f"\n{'='*60}")
    print(f"Originality Transformer complete: {len(results)}/{total_jobs} in {total_time:.0f}s")
    print(f"Output: {out_dir}")
    print(f"\nPackaged output (open this folder to review):")
    # List all files in sorted order
    for f in sorted(os.listdir(out_dir)):
        if f.endswith(".png"):
            marker = "  ← SOURCE" if "_source" in f else ""
            print(f"  {f}{marker}")

    return results, out_dir


# ─── CLI ─────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Thumbnail Originality Transformer — Create original variations from generated thumbnails"
    )
    parser.add_argument("title", type=str, help="Video title")
    parser.add_argument("--session-dir", type=str, default=None,
                        help="Path to session directory with option_A-F.png files")
    parser.add_argument("--latest", action="store_true",
                        help="Auto-find the most recent generation session in output/")
    parser.add_argument("--model", type=str, choices=["flash", "pro"], default="pro",
                        help="Image generation model (default: pro)")
    parser.add_argument("--variations", type=int, default=DEFAULT_VARIATIONS,
                        help=f"Number of variations per source thumbnail (default: {DEFAULT_VARIATIONS})")
    args = parser.parse_args()

    if not args.session_dir and not args.latest:
        parser.error("Provide --session-dir or --latest")

    model = NANO_BANANA_MODEL if args.model == "flash" else NANO_BANANA_PRO_MODEL

    transform_pipeline(
        title=args.title,
        session_dir=args.session_dir,
        latest=args.latest,
        model=model,
        variations=args.variations,
    )


if __name__ == "__main__":
    main()
