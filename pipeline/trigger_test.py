#!/usr/bin/env python3
"""
One-off test: Psychological Trigger Thumbnail System
Generates 6 thumbnails using 6 different psychological triggers.
No viral reference needed — originality comes from the strategy.
"""

import os
import sys
import time
import base64
import json

# Project root (one level up from pipeline/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add thumbnail_system to path
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "thumbnail_system"))

from config import GEMINI_API_KEY, NANO_BANANA_PRO_MODEL, AIRTABLE_TOKEN, CONTENT_MATE_BASE, THUMBNAIL_GENERATIONS_TABLE
from generate_thumbnail import get_face_references, _get_drive_service, upload_to_drive, airtable_create_gen, airtable_update_gen

# Reuse the generation function from thumbnail_service
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "pipeline"))
from thumbnail_service import _generate_from_text, _ensure_thumbnails_field

TITLE = "Claude Code for Beginners"

# ─── 6 Psychological Triggers ────────────────────────────────────────

TRIGGERS = {
    "T1_forbidden_knowledge": {
        "name": "Forbidden Knowledge",
        "prompt": f"""Create a YouTube thumbnail for: "{TITLE}"

PSYCHOLOGICAL TRIGGER: FORBIDDEN KNOWLEDGE
The viewer should feel like they're about to see something secret or hidden that most people don't know about.

VISUAL DIRECTION:
- Show the person looking directly at the camera with a knowing, slightly mischievous expression — like they're about to reveal a secret
- A laptop or code editor screen slightly angled away or partially blurred — suggesting hidden content
- Text at the TOP: something like "they don't teach this" or "the secret tool" — short, punchy
- Dark, moody background — feels exclusive and insider

STYLE RULES:
- Person wears a plain white t-shirt
- Text is Montserrat Black font, flat solid color #f5c200 (golden yellow) — NO gradient
- Dark background for contrast
- Maximum 3 elements: person + screen/graphic + text
- Must be readable at 150px height

Output 16:9 aspect ratio (1920x1080)."""
    },

    "T2_contrast_of_scale": {
        "name": "Contrast of Scale",
        "prompt": f"""Create a YouTube thumbnail for: "{TITLE}"

PSYCHOLOGICAL TRIGGER: CONTRAST OF SCALE
Show something impossibly large next to something small to create visual drama and curiosity.

VISUAL DIRECTION:
- A MASSIVE Claude/Anthropic logo or terminal window taking up most of the frame — oversized, dominant
- The person small in the corner, looking up at it in awe or excitement
- Text at the TOP: short punchy phrase about the power of this tool
- The scale difference should be dramatic — the viewer thinks "wow, this thing is huge/powerful"

STYLE RULES:
- Person wears a plain white t-shirt
- Text is Montserrat Black font, flat solid color #f5c200 (golden yellow) — NO gradient
- Dark background for contrast
- Maximum 3 elements: person + giant graphic + text
- Must be readable at 150px height

Output 16:9 aspect ratio (1920x1080)."""
    },

    "T3_specificity": {
        "name": "Specificity",
        "prompt": f"""Create a YouTube thumbnail for: "{TITLE}"

PSYCHOLOGICAL TRIGGER: SPECIFICITY
A concrete, specific number or result makes the viewer trust the content is real and valuable.

VISUAL DIRECTION:
- Person with confident, direct expression — looking at camera
- One LARGE specific number or stat prominently displayed: "10x FASTER" or "100 HOURS SAVED" — big, bold, impossible to miss
- Clean, minimal layout — the number IS the thumbnail
- Text at the TOP with the video hook

STYLE RULES:
- Person wears a plain white t-shirt
- ALL text is Montserrat Black font, flat solid color #f5c200 (golden yellow) — NO gradient
- Dark background for contrast
- Maximum 3 elements: person + big number + title text
- Must be readable at 150px height

Output 16:9 aspect ratio (1920x1080)."""
    },

    "T4_before_after": {
        "name": "Before/After Tension",
        "prompt": f"""Create a YouTube thumbnail for: "{TITLE}"

PSYCHOLOGICAL TRIGGER: BEFORE/AFTER TENSION
Show two contrasting states in one frame — the viewer needs to know what changed.

VISUAL DIRECTION:
- LEFT side: messy, chaotic code or a frustrated person (the "before" — struggling, manual, slow)
- RIGHT side: clean, elegant terminal or a happy confident person (the "after" — automated, fast, powerful)
- A clear visual split or dividing line between the two halves
- Text at the TOP bridging both sides

STYLE RULES:
- Person wears a plain white t-shirt (on the "after" side)
- Text is Montserrat Black font, flat solid color #f5c200 (golden yellow) — NO gradient
- Left side slightly darker/red-toned, right side brighter/blue-toned
- Must be readable at 150px height

Output 16:9 aspect ratio (1920x1080)."""
    },

    "T5_identity_mirror": {
        "name": "Identity Mirror",
        "prompt": f"""Create a YouTube thumbnail for: "{TITLE}"

PSYCHOLOGICAL TRIGGER: IDENTITY MIRROR
The viewer should see THEMSELVES in the thumbnail — a beginner sitting at their desk, about to discover something amazing.

VISUAL DIRECTION:
- Person at a desk/laptop, leaning in with wide eyes and an excited expression — the "aha moment"
- The screen glowing with something impressive (code running, terminal active)
- Text at the TOP: inviting, beginner-friendly hook — makes them feel "this is for ME"
- Warm, inviting feel — not intimidating

STYLE RULES:
- Person wears a plain white t-shirt
- Text is Montserrat Black font, flat solid color #f5c200 (golden yellow) — NO gradient
- Dark but warm background
- Maximum 3 elements: person at desk + screen glow + text
- Must be readable at 150px height

Output 16:9 aspect ratio (1920x1080)."""
    },

    "T6_authority_proof": {
        "name": "Authority/Proof",
        "prompt": f"""Create a YouTube thumbnail for: "{TITLE}"

PSYCHOLOGICAL TRIGGER: AUTHORITY & PROOF
Show undeniable proof that this works — real output, real results, real credibility.

VISUAL DIRECTION:
- Person with arms crossed or hands together, confident expert pose — "I know what I'm talking about"
- Behind them: a real-looking terminal or code output showing Claude Code actually running — visible text, real commands
- Text at the TOP: bold authority claim
- Clean, professional, credible — this person is the expert guide

STYLE RULES:
- Person wears a plain white t-shirt
- Text is Montserrat Black font, flat solid color #f5c200 (golden yellow) — NO gradient
- Dark background for contrast
- Maximum 3 elements: person + terminal/proof + text
- Must be readable at 150px height

Output 16:9 aspect ratio (1920x1080)."""
    },
}


def main():
    print("=" * 60)
    print("PSYCHOLOGICAL TRIGGER TEST — 6 Thumbnails")
    print(f"Title: {TITLE}")
    print("=" * 60)

    # Load face refs
    face_refs = get_face_references()
    print(f"Loaded {len(face_refs)} face references\n")

    # Create output dir
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(_PROJECT_ROOT, "thumbnail_system", "output",
                           f"{timestamp}_TRIGGER_TEST_{TITLE}")
    os.makedirs(out_dir, exist_ok=True)

    # Generate all 6 in parallel
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = {}
    start = time.time()

    def generate_one(key, trigger):
        t0 = time.time()
        print(f"  Generating {key} ({trigger['name']})...")
        img_data = _generate_from_text(trigger["prompt"], face_refs, NANO_BANANA_PRO_MODEL)
        elapsed = int(time.time() - t0)
        if img_data:
            file_path = os.path.join(out_dir, f"{key}.png")
            with open(file_path, "wb") as f:
                f.write(img_data)
            print(f"  ✅ {key} done ({elapsed}s)")
            return key, {"file_path": file_path, "trigger": trigger["name"], "prompt": trigger["prompt"]}
        else:
            print(f"  ❌ {key} failed ({elapsed}s)")
            return key, None

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(generate_one, k, v): k for k, v in TRIGGERS.items()}
        for fut in as_completed(futures):
            key, result = fut.result()
            if result:
                results[key] = result

    elapsed_total = int(time.time() - start)
    print(f"\nGenerated {len(results)}/6 thumbnails in {elapsed_total}s")
    print(f"Output: {out_dir}\n")

    # ── Upload to Drive + Airtable ──
    if not results:
        print("No thumbnails generated — skipping upload")
        return

    print("=" * 60)
    print(f"UPLOADING {len(results)} THUMBNAILS → Drive + Airtable")
    print("=" * 60)

    _ensure_thumbnails_field()
    drive_service = _get_drive_service()
    face_ref_names = [os.path.basename(r["path"]) for r in face_refs]

    record_title = f"🧠 Trigger Test: {TITLE}"[:100]
    fields = {
        "Video Title": record_title,
        "Prompt Used": "Psychological Trigger System — 6 triggers, no viral reference",
        "Face Refs Used": ", ".join(face_ref_names),
        "Status": "Awaiting Review",
        "Generation Prompt": "\n\n---\n\n".join(
            f"[{v['trigger']}]\n{v['prompt'][:500]}" for v in results.values()
        )[:100000],
    }

    record = airtable_create_gen(fields)
    record_id = record["records"][0]["id"]
    print(f"\n  Record: {record_id} — {record_title}")

    attachments = []
    for key in sorted(results.keys()):
        r = results[key]
        drive_url = upload_to_drive(r["file_path"], drive_service)
        if drive_url:
            attachments.append({"url": drive_url})
            r["drive_url"] = drive_url
            print(f"    Uploaded: {key}.png ({r['trigger']})")

    if attachments:
        airtable_update_gen(record_id, {"Thumbnails": attachments})
        print(f"    → {len(attachments)} images attached")

    print(f"\n✅ Done! Check Airtable for the record: {record_title}")
    print(f"   Session folder: {out_dir}")


if __name__ == "__main__":
    main()
