#!/usr/bin/env python3
"""
Thumbnail Service v3.0 — 5-System Pipeline with Must-Click Score.

Generates 24 thumbnails across 5 creative systems, scores all with
Gemini Flash, selects top 3 with system diversity, uploads to Drive.

Systems:
  1. Viral Videos   — 3 inspirations × 3 variations = 9 thumbnails
  2. Favorites      — 3 random favorite styles remade = 3 thumbnails
  3. AI + Face      — Face refs + text prompt = 3 thumbnails
  4. No Face        — All AI, no face = 3 thumbnails
  5. Triggers       — 6 psychological triggers + YouTube research + logo = 6 thumbnails

Usage (programmatic):
    from thumbnail_service import run_thumbnail_pipeline
    result = run_thumbnail_pipeline("Video Title", ["concept A", "concept B"])

Usage (CLI):
    python3 thumbnail_service.py "Video Title" --concepts "concept A" "concept B"
    python3 thumbnail_service.py "Video Title" --system 5
    python3 thumbnail_service.py "Video Title" --system 2 --concepts "AI automation"
"""

import os
import sys
import json
import base64
import time
import re
import io
import random
import urllib.request
import urllib.error
import urllib.parse
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Auto SSL fix
import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

# Add thumbnail_system to path for imports
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "thumbnail_system"))

from config import (
    GEMINI_API_KEY, AIRTABLE_TOKEN, YOUTUBE_API_KEY,
    NANO_BANANA_PRO_MODEL, GEMINI_FLASH_TEXT_MODEL,
    OUTPUT_DIR, CONTENT_MATE_BASE,
    THUMBNAIL_GENERATIONS_TABLE, FAVORITE_THUMBNAILS_TABLE,
)
from generate_thumbnail import (
    generate_thumbnails, generate_single, get_face_references,
    _get_drive_service, upload_to_drive, save_and_upscale,
    airtable_create_gen, airtable_update_gen, ensure_source_fields,
)
from transform_thumbnail import transform_pipeline
from PIL import Image


# ─── Data structures ─────────────────────────────────────────────────

@dataclass
class ScoredThumbnail:
    """A single scored thumbnail with metadata."""
    label: str              # e.g. "S1_A1_v1" or "S2_B"
    source_label: str       # e.g. "A" (which source within the system)
    score: float            # 1-10 Must-Click Score
    reasoning: str          # One-line explanation
    file_path: str          # Local path to the image
    drive_url: str          # Public Drive URL
    is_variation: bool      # True = transformed, False = source/direct
    system: int             # 1, 2, 3, or 4


@dataclass
class ThumbnailServiceResult:
    """Complete result from the thumbnail service."""
    top_3: List[ScoredThumbnail]
    all_scored: List[ScoredThumbnail]
    thumbnail_concepts: List[str]
    title: str
    session_dir: str
    total_time: float


# ─── Prompts for each system ────────────────────────────────────────

FAVORITES_PROMPT = """Recreate this YouTube thumbnail in the EXACT same style, layout, color scheme,
and visual vibe — but make it about a completely different video.

NEW VIDEO TITLE: {title}
THUMBNAIL CONCEPTS: {concepts}

KEEP from the reference:
- The exact visual style, color palette, and artistic approach
- The layout and composition structure
- The level of polish and professionalism
- The emotional tone

CHANGE:
- Replace the face with my face (see face references)
- Change ALL text to match the new video title/concepts
- Adjust any icons or graphics to match the new topic (AI automation)
- Change the shirt to a plain white t-shirt

CRITICAL LAYOUT RULES:
- Text goes at the TOP of the thumbnail only — never at the bottom
- Keep the composition SIMPLE — maximum 2-3 visual elements total (person + 1-2 graphics)
- Do NOT add extra icons, crossed-out symbols, gear icons, clock icons, or decorative elements
- If there's a screen/device mockup showing content, that's the ONE main graphic — don't add more
- Negative space is your friend — leave breathing room between elements
- Text should be bold, large, in Montserrat Black font with a vertical gradient from bright yellow (#FFD700) at top to deep golden (#E8A800) at bottom
- Text is MAX 4 words (ideally 2-3) — the video title handles the rest
- Background is dark grey/black with a subtle blue tint — not pure black

The result should look like it could be from the same channel series but about a completely different topic.
Output must be 16:9 aspect ratio (1920x1080)."""

AI_FACE_PROMPT = """Create a YouTube thumbnail for the following video.
Use the face reference photos to include this person as the host.

VIDEO TITLE: {title}
THUMBNAIL CONCEPT: {concept}

LAYOUT (follow this exactly):
- The PERSON goes on the RIGHT side of the thumbnail (roughly right 40% of frame)
- BOLD TEXT goes at the TOP of the thumbnail — large, immediately readable
- ONE simple graphic or visual element on the LEFT or BOTTOM-LEFT area
- That's it. Maximum 3 elements total: text + person + one graphic

STYLE RULES:
- Person wears a plain white t-shirt
- Text uses Montserrat Black font with a vertical gradient from bright yellow (#FFD700) at top to deep golden (#E8A800) at bottom
- Text is MAX 4 words (ideally 2-3) — punchy hook, not a sentence
- Background is dark grey/black with a subtle blue tint — not pure black
- High contrast — the text and person should POP against the background
- Leave generous negative space between elements — do NOT crowd the frame

DO NOT:
- Add extra icons, badges, gear icons, clock icons, or decorative symbols
- Put a red X over anything — no "crossed out" elements
- Add text at the bottom of the thumbnail
- Create a busy or overcrowded composition
- Use more than ONE graphic element besides the person and text

The thumbnail must be instantly readable at small size (150px height).
Output must be 16:9 aspect ratio (1920x1080)."""

NO_FACE_PROMPT = """Create a YouTube thumbnail with NO person or face.

VIDEO TITLE: {title}
THUMBNAIL CONCEPT: {concept}

LAYOUT:
- BOLD TEXT at the TOP — large, immediately readable, Montserrat Black font, vertical gradient from bright yellow (#FFD700) at top to deep golden (#E8A800) at bottom
- Text is MAX 4 words (ideally 2-3) — punchy hook, not a sentence
- ONE main visual element in the center or center-left — this is the focal point
- That's it. The viewer should focus on exactly 2 things: the text and one graphic

WHAT THE VISUAL ELEMENT SHOULD BE (pick ONE):
- A recognizable software logo or tool icon (large, clean)
- A simple device mockup (laptop or phone showing a screen)
- A single bold statistic or number
- A clean, minimal icon or symbol

STYLE:
- Dark background — mostly dark grey/black with a subtle blue tint (not pure black)
- High contrast — the graphic and text must pop
- Professional, modern, minimal aesthetic
- LOTS of negative space — the thumbnail should feel clean, not busy
- Maximum 2-3 colors total

DO NOT:
- Add more than ONE main graphic element
- Create workflow diagrams with many steps or arrows
- Include robot hands, AI brain icons, gear icons, or cliche tech imagery
- Add crossed-out symbols or red X marks
- Put text at the bottom
- Make it look overcrowded or busy in any way

Think SIMPLE. Think BOLD. Think: one glance = one message.
Output must be 16:9 aspect ratio (1920x1080)."""

def _load_feedback_rules(system_key=None):
    """Load feedback memory rules from JSON and format for prompt injection.

    The feedback_memory.json file stores learned rules from user feedback.
    These rules get appended to generation prompts so the AI improves over time.
    """
    memory_path = os.path.join(_PROJECT_ROOT, "thumbnail_system", "feedback_memory.json")
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


SCORING_PROMPT = """You are a YouTube thumbnail scoring expert for the channel "YOUR_CHANNEL_NAME".

TARGET AUDIENCE:
Aspiring AI creators and entrepreneurs aged 25-45 who want to automate their business or content workflow without coding. They scroll YouTube looking for practical, achievable AI automation tutorials. They click on thumbnails that promise clear outcomes, show real systems, or trigger curiosity about unexpected mechanisms.

VIDEO TITLE: {title}

{concepts_section}

TASK: Score each of the following {count} thumbnails on a "Must-Click Score" from 1 to 10.

A "Must-Click" thumbnail for this audience has:
- CLARITY: Can you tell what the video is about in under 1 second?
- EMOTION: Does the facial expression trigger curiosity or excitement?
- CONTRAST: Do the colors pop — would this stand out in a feed of other thumbnails?
- BENEFIT SIGNAL: Does the text/imagery promise a specific outcome or reveal?
- BRAND FIT: Does this feel like it belongs on an AI automation channel?
- TITLE-THUMBNAIL SYNERGY: Does the thumbnail complement the title (not repeat it)?

Score 1-3 = would scroll past. 4-6 = might click. 7-8 = strong click. 9-10 = can't NOT click.

The thumbnails are labeled: {labels}. For each, provide a score and a one-line reason.

Respond in this EXACT JSON format (no markdown, no code fences):
{{"scores": [{{"label": "S1_A1", "score": 7, "reason": "Strong curiosity gap but text is hard to read at small size"}}, {{"label": "S2_A", "score": 8, "reason": "Clean layout, white shirt pops, yellow text readable"}}]}}
"""


# ─── System 1: Viral Videos ────────────────────────────────────────

def system_1_viral(title, session_dir, model):
    """System 1: Generate 3 from viral videos, transform each 3× = 9 thumbnails.

    Uses existing generate_thumbnails() + transform_pipeline() with count=3.
    """
    print(f"\n{'─'*50}")
    print(f"SYSTEM 1 — Viral Videos (3 inspirations × 3 variations)")
    print(f"{'─'*50}")

    # Step A: Generate 3 options from viral videos (skip per-system Airtable)
    print(f"\n  [1A] Generating 3 thumbnails from viral videos...")
    options, gen_dir = generate_thumbnails(title, model=model, count=3, skip_airtable=True)

    if not options:
        print("  WARNING: System 1 failed — no viral thumbnails generated")
        return []

    # Step B: Transform each (3 variations per source = 9 total, skip per-system Airtable)
    print(f"\n  [1B] Transforming to originals (3 variations each)...")
    results, packaged_dir = transform_pipeline(title, latest=True, model=model, variations=3, skip_airtable=True)

    if not results:
        print("  WARNING: System 1 transform failed — using generated thumbnails directly")
        # Fall back to scoring the raw generated options
        thumbnails = []
        for opt in options:
            thumbnails.append({
                "label": f"S1_{opt['label']}",
                "source_label": opt["label"],
                "file_path": opt["path"],
                "is_variation": False,
                "system": 1,
            })
        return thumbnails

    # Step C: Collect ALL thumbnails (sources + 9 variations)
    # Sources are included for Airtable reference but flagged to skip scoring
    thumbnails = []
    for fname in sorted(os.listdir(packaged_dir)):
        if fname.endswith(".png"):
            is_source = "_source" in fname
            thumbnails.append({
                "label": f"S1_{fname.replace('.png', '')}",
                "source_label": fname[0],  # A, B, C
                "file_path": os.path.join(packaged_dir, fname),
                "is_variation": not is_source,
                "is_source_ref": is_source,  # True = viral source, skip scoring
                "system": 1,
            })

    print(f"  System 1 complete: {len(thumbnails)} thumbnails")
    return thumbnails


# ─── System 2: Favorite Thumbnails ─────────────────────────────────

def _fetch_favorite_thumbnails(count=3):
    """Fetch random favorite thumbnails from the Favorites table."""
    url = (
        f"https://api.airtable.com/v0/{CONTENT_MATE_BASE}/{FAVORITE_THUMBNAILS_TABLE}"
        f"?fields[]=Video%20Title&fields[]=Final"
    )
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AIRTABLE_TOKEN}"})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ERROR fetching favorites: {e}")
        return []

    candidates = []
    for rec in data.get("records", []):
        f = rec.get("fields", {})
        attachments = f.get("Final", [])
        if attachments:
            candidates.append({
                "record_id": rec["id"],
                "title": f.get("Video Title", ""),
                "url": attachments[0]["url"],
            })

    if not candidates:
        print("  WARNING: No favorite thumbnails found in Favorites table")
        return []

    selected = random.sample(candidates, min(count, len(candidates)))
    print(f"  Selected {len(selected)} favorites from {len(candidates)} available")

    # Download in parallel
    def _download(item):
        try:
            with urllib.request.urlopen(item["url"], timeout=30) as resp:
                raw = resp.read()
            return {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(raw).decode("utf-8"),
                "title": item["title"],
                "record_id": item["record_id"],
            }
        except Exception as e:
            print(f"    Warning: Failed to download favorite '{item['title'][:40]}': {e}")
            return None

    refs = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(_download, item): item for item in selected}
        for future in as_completed(futures):
            result = future.result()
            if result:
                refs.append(result)
                print(f"    Got favorite: {result['title'][:60]}")

    return refs


def system_2_favorites(title, concepts, face_refs, out_dir, model):
    """System 2: Remake 3 favorite thumbnails in new video's style.

    Downloads 3 random favorites, sends each with face refs + remix prompt.
    """
    print(f"\n{'─'*50}")
    print(f"SYSTEM 2 — Favorite Thumbnails (3 remakes)")
    print(f"{'─'*50}")

    favorites = _fetch_favorite_thumbnails(count=3)
    if not favorites:
        print("  WARNING: System 2 failed — no favorites available")
        return []

    concepts_text = "; ".join(concepts) if concepts else title

    os.makedirs(out_dir, exist_ok=True)
    thumbnails = []

    def _generate_one(i, fav):
        label = chr(65 + i)  # A, B, C
        fav_title = fav.get("title", "unknown")[:40]
        print(f"  Generating S2_{label} (from favorite: {fav_title})...")
        t_start = time.time()

        prompt = FAVORITES_PROMPT.format(title=title, concepts=concepts_text)
        prompt += _load_feedback_rules("system_2_favorites")

        try:
            # Use the favorite as the viral_ref (style reference)
            viral_ref = {"mime_type": fav["mime_type"], "data": fav["data"]}
            img_bytes = generate_single(viral_ref, face_refs, model, custom_prompt=prompt)

            if img_bytes:
                output_path = os.path.join(out_dir, f"S2_{label}.png")
                save_and_upscale(img_bytes, output_path)
                elapsed = time.time() - t_start
                print(f"  S2_{label} done ({elapsed:.0f}s)")
                return {
                    "label": f"S2_{label}",
                    "source_label": label,
                    "file_path": output_path,
                    "is_variation": False,
                    "system": 2,
                    "inspired_by": fav_title,
                    "generation_prompt": prompt,
                }
            else:
                print(f"  S2_{label} failed: no image returned")
                return None
        except Exception as e:
            print(f"  S2_{label} error: {e}")
            return None

    # Generate in parallel (3 workers)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(_generate_one, i, fav): i for i, fav in enumerate(favorites)}
        for future in as_completed(futures):
            result = future.result()
            if result:
                thumbnails.append(result)

    thumbnails.sort(key=lambda t: t["label"])

    print(f"  System 2 complete: {len(thumbnails)} thumbnails")
    return thumbnails


# ─── System 3: AI + Face ───────────────────────────────────────────

def system_3_ai_face(title, concepts, face_refs, out_dir, model):
    """System 3: Generate 3 unique thumbnails from text prompt + face refs.

    No reference image — purely from concept descriptions.
    """
    print(f"\n{'─'*50}")
    print(f"SYSTEM 3 — AI + Face (3 unique from text + face refs)")
    print(f"{'─'*50}")

    os.makedirs(out_dir, exist_ok=True)

    # Build 3 concept variations
    concept_prompts = _build_concept_prompts(concepts, count=3)
    thumbnails = []

    def _generate_one(i, concept):
        label = chr(65 + i)  # A, B, C
        print(f"  Generating S3_{label} (concept: {concept[:60]}...)...")
        t_start = time.time()

        prompt = AI_FACE_PROMPT.format(title=title, concept=concept)
        prompt += _load_feedback_rules("system_3_ai_face")

        try:
            # No viral_ref — text prompt with face refs, no source image
            img_bytes = _generate_from_text(prompt, face_refs, model)

            if img_bytes:
                output_path = os.path.join(out_dir, f"S3_{label}.png")
                save_and_upscale(img_bytes, output_path)
                elapsed = time.time() - t_start
                print(f"  S3_{label} done ({elapsed:.0f}s)")
                return {
                    "label": f"S3_{label}",
                    "source_label": label,
                    "file_path": output_path,
                    "is_variation": False,
                    "system": 3,
                    "generation_prompt": prompt,
                }
            else:
                print(f"  S3_{label} failed: no image returned")
                return None
        except Exception as e:
            print(f"  S3_{label} error: {e}")
            return None

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(_generate_one, i, c): i for i, c in enumerate(concept_prompts)}
        for future in as_completed(futures):
            result = future.result()
            if result:
                thumbnails.append(result)

    thumbnails.sort(key=lambda t: t["label"])

    print(f"  System 3 complete: {len(thumbnails)} thumbnails")
    return thumbnails


# ─── System 4: No Face ─────────────────────────────────────────────

def system_4_no_face(title, concepts, out_dir, model):
    """System 4: Generate 3 thumbnails with no face — all AI graphics.

    No face refs, no reference image. Pure text prompt.
    """
    print(f"\n{'─'*50}")
    print(f"SYSTEM 4 — No Face (3 all-AI thumbnails)")
    print(f"{'─'*50}")

    os.makedirs(out_dir, exist_ok=True)

    concept_prompts = _build_concept_prompts(concepts, count=3)
    thumbnails = []

    def _generate_one(i, concept):
        label = chr(65 + i)  # A, B, C
        print(f"  Generating S4_{label} (concept: {concept[:60]}...)...")
        t_start = time.time()

        prompt = NO_FACE_PROMPT.format(title=title, concept=concept)
        prompt += _load_feedback_rules("system_4_no_face")

        try:
            # No face refs, no source image — text prompt only
            img_bytes = _generate_from_text(prompt, [], model)

            if img_bytes:
                output_path = os.path.join(out_dir, f"S4_{label}.png")
                save_and_upscale(img_bytes, output_path)
                elapsed = time.time() - t_start
                print(f"  S4_{label} done ({elapsed:.0f}s)")
                return {
                    "label": f"S4_{label}",
                    "source_label": label,
                    "file_path": output_path,
                    "is_variation": False,
                    "system": 4,
                    "generation_prompt": prompt,
                }
            else:
                print(f"  S4_{label} failed: no image returned")
                return None
        except Exception as e:
            print(f"  S4_{label} error: {e}")
            return None

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(_generate_one, i, c): i for i, c in enumerate(concept_prompts)}
        for future in as_completed(futures):
            result = future.result()
            if result:
                thumbnails.append(result)

    thumbnails.sort(key=lambda t: t["label"])

    print(f"  System 4 complete: {len(thumbnails)} thumbnails")
    return thumbnails


# ─── System 5: Psychological Triggers (YouTube research + logo) ────

# The 6 psychological triggers
TRIGGER_CONFIGS = [
    {
        "key": "forbidden_knowledge",
        "name": "Forbidden Knowledge",
        "direction": "The viewer should feel like they're about to see something secret that most people don't know. Person has a knowing, slightly mischievous expression. A laptop or code screen partially visible. Feels exclusive and insider.",
    },
    {
        "key": "contrast_of_scale",
        "name": "Contrast of Scale",
        "direction": "Show something IMPOSSIBLY LARGE next to the person who looks small — creates visual drama. A giant logo, terminal, or graphic dominates the frame. The person reacts with awe or excitement. The scale difference must be dramatic.",
    },
    {
        "key": "specificity",
        "name": "Specificity",
        "direction": "One HUGE specific number or stat displayed prominently: like '10X FASTER' or '100 HRS SAVED'. The number IS the thumbnail. Person has a confident, direct expression. Clean, minimal layout — the stat is the star.",
    },
    {
        "key": "before_after",
        "name": "Before/After Tension",
        "direction": "Split the frame into two contrasting halves. LEFT: chaotic, messy, struggling (dark/red tones). RIGHT: clean, elegant, successful (bright/blue tones). A clear visual dividing line. The viewer NEEDS to know what changed.",
    },
    {
        "key": "identity_mirror",
        "name": "Identity Mirror",
        "direction": "The viewer sees THEMSELVES — person at a desk/laptop, leaning in with wide eyes, the 'aha moment'. Screen glowing with something impressive. Warm, inviting, beginner-friendly feel — not intimidating. 'This is for ME.'",
    },
    {
        "key": "authority_proof",
        "name": "Authority/Proof",
        "direction": "Person with confident expert pose — arms crossed or hands together. Behind them: a real-looking terminal showing actual code/output as proof. Clean, professional, credible. This person IS the expert guide.",
    },
]


def _search_youtube_thumbnails(query, max_results=8):
    """Search YouTube for a query and return top thumbnail URLs + titles.

    Uses YouTube Data API v3 to get competitive context.
    Returns list of dicts with 'title', 'thumbnail_url', 'channel', 'views'.
    """
    if not YOUTUBE_API_KEY:
        print("  Warning: No YouTube API key — skipping competitive research")
        return []

    search_url = (
        f"https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&type=video&q={urllib.parse.quote(query)}"
        f"&maxResults={max_results}&order=relevance"
        f"&key={YOUTUBE_API_KEY}"
    )

    try:
        req = urllib.request.Request(search_url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        results = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            thumbs = snippet.get("thumbnails", {})
            # Prefer high quality thumbnail
            thumb_url = (thumbs.get("high") or thumbs.get("medium") or thumbs.get("default", {})).get("url", "")
            results.append({
                "title": snippet.get("title", ""),
                "thumbnail_url": thumb_url,
                "channel": snippet.get("channelTitle", ""),
            })

        return results
    except Exception as e:
        print(f"  Warning: YouTube search failed: {e}")
        return []


def _fetch_logo_image(query):
    """Try to fetch a product/tool logo image via Google search.

    Returns base64-encoded image data and mime_type, or None.
    Uses a simple heuristic: search for "{query} logo png transparent"
    and try to download the first reasonable result.
    """
    # For well-known tools, use direct URLs
    known_logos = {
        "claude": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Claude_AI_logo.svg/200px-Claude_AI_logo.svg.png",
        "claude code": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Claude_AI_logo.svg/200px-Claude_AI_logo.svg.png",
        "anthropic": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Claude_AI_logo.svg/200px-Claude_AI_logo.svg.png",
        "chatgpt": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/ChatGPT_logo.svg/200px-ChatGPT_logo.svg.png",
        "openai": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/ChatGPT_logo.svg/200px-ChatGPT_logo.svg.png",
        "cursor": "https://www.cursor.com/brand/icon.svg",
        "github copilot": "https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png",
        "notion": "https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png",
        "midjourney": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Midjourney_Emblem.png",
    }

    # Check known logos first
    query_lower = query.lower()
    logo_url = None
    for key, url in known_logos.items():
        if key in query_lower:
            logo_url = url
            break

    if not logo_url:
        print(f"  No known logo for '{query}' — generating without logo reference")
        return None

    try:
        req = urllib.request.Request(logo_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            img_data = resp.read()
            content_type = resp.headers.get("Content-Type", "image/png")
            if "svg" in content_type:
                # SVGs can't be sent to Gemini image gen — skip
                print(f"  Logo is SVG format — will describe in prompt instead")
                return None
            mime = "image/png" if "png" in content_type else "image/jpeg"
            return {"data": base64.b64encode(img_data).decode("utf-8"), "mime_type": mime}
    except Exception as e:
        print(f"  Warning: Logo download failed: {e}")
        return None


def system_5_trigger(title, concepts, face_refs, out_dir, model):
    """System 5: Psychological trigger thumbnails with YouTube research + logo.

    1. Search YouTube for competitive context
    2. Fetch the product/tool logo
    3. Generate 6 thumbnails using 6 different psychological triggers
    """
    print(f"\n{'─'*50}")
    print(f"SYSTEM 5 — Psychological Triggers (6 thumbnails)")
    print(f"{'─'*50}")

    os.makedirs(out_dir, exist_ok=True)

    # Step 1: YouTube competitive research
    print(f"  Step 1: Searching YouTube for competitive context...")
    yt_results = _search_youtube_thumbnails(title)
    if yt_results:
        competitive_context = "COMPETITIVE CONTEXT (what's already on YouTube for this topic):\n"
        for i, r in enumerate(yt_results[:5]):
            competitive_context += f"  {i+1}. \"{r['title']}\" by {r['channel']}\n"
        competitive_context += "Use this awareness to DIFFERENTIATE — don't blend in with existing thumbnails.\n"
        print(f"  Found {len(yt_results)} competing videos")
    else:
        competitive_context = ""
        print(f"  No competitive data — generating without research context")

    # Step 2: Fetch product logo
    print(f"  Step 2: Fetching product/tool logo...")
    logo_data = _fetch_logo_image(title)
    logo_instruction = ""
    if logo_data:
        print(f"  Logo fetched — will include as reference image")
        logo_instruction = "\nIMPORTANT: I've included the product/tool logo as a reference image. Include this EXACT logo prominently in the thumbnail — the viewer should instantly recognize the tool.\n"
    else:
        # Extract tool name from title for text-based instruction
        logo_instruction = "\nIMPORTANT: Include the product/tool's recognizable logo or icon in the thumbnail. The viewer should instantly know what tool this video is about.\n"
        print(f"  No logo image — will describe in prompt")

    # Step 3: Generate 6 trigger thumbnails
    print(f"  Step 3: Generating 6 psychological trigger thumbnails...")
    thumbnails = []
    feedback_rules = _load_feedback_rules("system_5_trigger")

    def _generate_one(i, trigger):
        label = chr(65 + i)  # A through F
        print(f"  Generating S5_{label} ({trigger['name']})...")
        t_start = time.time()

        # Build the concept text
        concept_text = ""
        if concepts:
            concept_text = f"\nTHUMBNAIL CONCEPTS FROM CONTENT DOC: {', '.join(concepts[:3])}\n"

        prompt = f"""Create a YouTube thumbnail for: "{title}"
{concept_text}
PSYCHOLOGICAL TRIGGER: {trigger['name'].upper()}
{trigger['direction']}
{logo_instruction}
{competitive_context}
STYLE RULES (follow these EXACTLY):
- Person wears a plain white t-shirt (if person is shown)
- Text uses Montserrat Black font with a vertical gradient from bright yellow (#FFD700) at top to deep golden (#E8A800) at bottom
- Text is MAXIMUM 4 words — ideally 2-3 words. Just a punchy hook. The YouTube title handles the details.
- Background is dark grey/black with a subtle dark blue tint — NOT pure black
- Maximum 3 elements total (text + person + one graphic)
- Must be readable at thumbnail size (150px height)
- Leave generous negative space — do NOT crowd the frame

DO NOT:
- Use more than 4 words of text
- Add extra icons, badges, gears, clocks, or decorative clutter
- Put text at the bottom
- Use orange text — stay in the yellow-to-gold gradient range
- Create busy or overcrowded compositions

Output must be 16:9 aspect ratio (1920x1080)."""

        prompt += feedback_rules

        try:
            # Build refs: face refs + logo (if available)
            refs = list(face_refs) if face_refs else []
            if logo_data:
                refs.append({"data": logo_data["data"], "mime_type": logo_data["mime_type"], "path": "logo_reference.png"})

            img_bytes = _generate_from_text(prompt, refs, model)

            if img_bytes:
                output_path = os.path.join(out_dir, f"S5_{label}.png")
                save_and_upscale(img_bytes, output_path)
                elapsed = time.time() - t_start
                print(f"  S5_{label} done ({elapsed:.0f}s) — {trigger['name']}")
                return {
                    "label": f"S5_{label}",
                    "source_label": label,
                    "file_path": output_path,
                    "is_variation": False,
                    "system": 5,
                    "generation_prompt": prompt,
                    "trigger": trigger["name"],
                }
            else:
                print(f"  S5_{label} failed: no image returned")
                return None
        except Exception as e:
            print(f"  S5_{label} error: {e}")
            return None

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(_generate_one, i, t): i for i, t in enumerate(TRIGGER_CONFIGS)}
        for future in as_completed(futures):
            result = future.result()
            if result:
                thumbnails.append(result)

    thumbnails.sort(key=lambda t: t["label"])

    print(f"  System 5 complete: {len(thumbnails)} thumbnails")
    return thumbnails


# ─── Shared helpers ─────────────────────────────────────────────────

def _build_concept_prompts(concepts, count=3):
    """Build `count` concept prompt variations from the provided concepts.

    If fewer concepts than count, creates hybrid / bonus angles.
    """
    if not concepts:
        concepts = ["AI automation thumbnail"]

    prompts = []
    for i in range(count):
        if i < len(concepts):
            prompts.append(concepts[i])
        elif len(concepts) >= 2:
            # Hybrid: combine first two concepts
            prompts.append(f"Combine elements of: {concepts[0]} AND {concepts[1]}")
        else:
            # Repeat with variation instruction
            prompts.append(f"{concepts[0]} — create a different visual angle")

    return prompts


def _generate_from_text(prompt, face_refs, model):
    """Generate a thumbnail from text prompt + optional face refs (no source image).

    Similar to generate_single() but without a viral_ref image.
    """
    import http.client

    model = model or NANO_BANANA_PRO_MODEL

    parts = [{"text": prompt}]
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
                print(f"    503 capacity error, retrying in {wait}s (attempt {attempt + 1}/4)...")
                time.sleep(wait)
            else:
                raise
        except (ConnectionError, OSError, urllib.error.URLError, http.client.RemoteDisconnected) as e:
            if attempt < 3:
                wait = 15 * (attempt + 1)
                print(f"    Connection error, retrying in {wait}s (attempt {attempt + 1}/4): {e}")
                time.sleep(wait)
            else:
                raise

    for candidate in result.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
            elif "text" in part:
                print(f"    AI note: {part['text'][:100]}")

    return None


_thumbnails_field_ensured = False

def _ensure_thumbnails_field():
    """Create 'Thumbnails' attachment field in Thumbnail Generations table (idempotent)."""
    global _thumbnails_field_ensured
    if _thumbnails_field_ensured:
        return
    url = f"https://api.airtable.com/v0/meta/bases/{CONTENT_MATE_BASE}/tables/{THUMBNAIL_GENERATIONS_TABLE}/fields"
    payload = json.dumps({"name": "Thumbnails", "type": "multipleAttachments"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            json.loads(resp.read().decode("utf-8"))
        print("  Created field: Thumbnails")
    except urllib.error.HTTPError as e:
        if e.code == 422:  # Field already exists — fine
            pass
        else:
            body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
            print(f"  Warning: Could not create Thumbnails field: {e.code} {body[:200]}")
    _thumbnails_field_ensured = True


def _upload_to_airtable_records(title, all_thumbnails, face_refs):
    """Upload thumbnails to Drive and create Airtable records.

    Record structure:
      - System 1 (Viral): 3 records (one per source A/B/C, each with source + 3 variations)
      - System 2 (Favorites): 1 record (all 3 thumbnails)
      - System 3 (AI+Face): 1 record (all 3 thumbnails)
      - System 4 (NoFace): 1 record (all 3 thumbnails)
      - System 5 (Trigger): 1 record (all 6 thumbnails)

    All records use a single "Thumbnails" attachment field.
    """
    _ensure_thumbnails_field()

    face_ref_names = [os.path.basename(r["path"]) for r in face_refs] if face_refs else []
    drive_service = _get_drive_service()

    system_names = {1: "Viral", 2: "Favorites", 3: "AI+Face", 4: "NoFace", 5: "Trigger"}
    record_ids = []

    # ── Group thumbnails by system ──
    by_system = {}
    for t in all_thumbnails:
        sys_num = t.get("system", 0)
        if sys_num not in by_system:
            by_system[sys_num] = []
        by_system[sys_num].append(t)

    # ── System 1: 3 records (one per source label A, B, C) ──
    if 1 in by_system:
        s1_by_source = {}
        for t in by_system[1]:
            src = t.get("source_label", "?")
            if src not in s1_by_source:
                s1_by_source[src] = []
            s1_by_source[src].append(t)

        for src_label in sorted(s1_by_source.keys()):
            thumbs = s1_by_source[src_label]
            record_title = f"S1-{src_label} Viral: {title}"[:100]
            rid = _create_and_upload_record(
                record_title, thumbs, drive_service, face_ref_names,
                f"System 1 Viral — Source {src_label} ({len(thumbs)} images)"
            )
            if rid:
                record_ids.append(rid)

    # ── Systems 2, 3, 4, 5: 1 record each ──
    for sys_num in [2, 3, 4, 5]:
        if sys_num not in by_system:
            continue
        thumbs = by_system[sys_num]
        sys_name = system_names.get(sys_num, "?")
        record_title = f"S{sys_num} {sys_name}: {title}"[:100]
        rid = _create_and_upload_record(
            record_title, thumbs, drive_service, face_ref_names,
            f"System {sys_num} {sys_name} ({len(thumbs)} images)"
        )
        if rid:
            record_ids.append(rid)

    print(f"\n  Created {len(record_ids)} Airtable records total")
    return record_ids


def _create_and_upload_record(record_title, thumbnails, drive_service, face_ref_names, description):
    """Create one Airtable record and upload thumbnails to its 'Thumbnails' field."""
    # Extract generation prompt from first thumbnail (all in same group use the same prompt)
    gen_prompt = ""
    for t in thumbnails:
        if t.get("generation_prompt"):
            gen_prompt = t["generation_prompt"]
            break

    fields = {
        "Video Title": record_title,
        "Prompt Used": description,
        "Face Refs Used": ", ".join(face_ref_names) if face_ref_names else "None",
        "Status": "Awaiting Review",
    }
    if gen_prompt:
        fields["Generation Prompt"] = gen_prompt[:100000]  # Airtable long text limit

    record = airtable_create_gen(fields)
    record_id = record["records"][0]["id"]
    print(f"\n  Record: {record_id} — {record_title}")

    attachments = []
    for thumb in thumbnails:
        drive_url = upload_to_drive(thumb["file_path"], drive_service)
        if drive_url:
            attachments.append({"url": drive_url})
            thumb["drive_url"] = drive_url
            print(f"    Uploaded: {os.path.basename(thumb['file_path'])}")

    if attachments:
        for attempt in range(3):
            try:
                airtable_update_gen(record_id, {"Thumbnails": attachments})
                print(f"    → {len(attachments)} images attached")
                break
            except Exception as e:
                if attempt < 2:
                    wait = 5 * (attempt + 1)
                    print(f"    Airtable retry {attempt + 1}/3: {e}")
                    time.sleep(wait)
                else:
                    print(f"    Warning: Airtable update failed: {e}")

    return record_id


# ─── Upload top 3 to Drive for embedding ─────────────────────────────

def _upload_top3_to_drive(top_3):
    """Upload top 3 thumbnail files to Google Drive for permanent, embeddable URLs."""
    drive_service = _get_drive_service()
    if not drive_service:
        print("  WARNING: Could not get Drive service — URLs will be empty")
        return top_3

    for t in top_3:
        file_path = t.file_path if hasattr(t, "file_path") else t.get("file_path", "")
        if file_path and os.path.exists(file_path):
            url = upload_to_drive(file_path, drive_service)
            if url:
                object.__setattr__(t, "drive_url", url)

    return top_3


# ─── Resize for scoring ──────────────────────────────────────────────

def _resize_for_scoring(image_path, max_width=384):
    """Resize image for scoring to keep API request small."""
    img = Image.open(image_path)
    ratio = max_width / img.width
    new_size = (max_width, int(img.height * ratio))
    img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8"), "image/png"


# ─── Gemini Flash scoring call ───────────────────────────────────────

def _call_gemini_scoring(prompt, images):
    """Single Gemini Flash call to score thumbnails."""
    parts = [{"text": prompt}]
    for img in images:
        parts.append({
            "inline_data": {
                "mime_type": img["mime_type"],
                "data": img["data"],
            }
        })

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json",
        },
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_FLASH_TEXT_MODEL}:generateContent?key={GEMINI_API_KEY}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    text = result["candidates"][0]["content"]["parts"][0]["text"]
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


# ─── Score thumbnails ────────────────────────────────────────────────

def score_thumbnails(thumbnails, title, thumbnail_concepts=None):
    """Score all thumbnails using Gemini Flash.

    If > 12 thumbnails, splits into 2 batches to stay within token limits.
    Returns list of ScoredThumbnail with scores and reasoning.
    """
    if not thumbnails:
        return []

    # Build concepts section
    concepts_section = ""
    if thumbnail_concepts:
        concepts_section = "THUMBNAIL CONCEPT IDEAS FROM THE CONTENT DOC:\n"
        for i, concept in enumerate(thumbnail_concepts):
            concepts_section += f"- Concept {i + 1}: {concept}\n"
        concepts_section += "\nUse these concepts as additional context for how well each thumbnail matches the creator's vision.\n"

    # Split into batches if needed (12 images per batch max for safety)
    BATCH_SIZE = 12
    batches = []
    for i in range(0, len(thumbnails), BATCH_SIZE):
        batches.append(thumbnails[i:i + BATCH_SIZE])

    all_score_entries = []

    for batch_num, batch in enumerate(batches):
        # Prepare images (resized for scoring)
        labels = []
        images = []
        for t in batch:
            b64_data, mime = _resize_for_scoring(t["file_path"])
            labels.append(t["label"])
            images.append({"data": b64_data, "mime_type": mime})

        prompt = SCORING_PROMPT.format(
            title=title,
            concepts_section=concepts_section,
            count=len(batch),
            labels=", ".join(labels),
        )

        # Call Gemini Flash (retry once on failure)
        scores_data = None
        for attempt in range(2):
            try:
                batch_label = f" (batch {batch_num + 1}/{len(batches)})" if len(batches) > 1 else ""
                print(f"  Scoring {len(batch)} thumbnails with Gemini Flash{batch_label} (attempt {attempt + 1})...")
                scores_data = _call_gemini_scoring(prompt, images)
                break
            except Exception as e:
                print(f"  Scoring attempt {attempt + 1} failed: {e}")
                if attempt == 0:
                    time.sleep(5)

        if scores_data and "scores" in scores_data:
            all_score_entries.extend(scores_data["scores"])
        else:
            print(f"  WARNING: Scoring failed for batch {batch_num + 1} — assigning default 5/10")
            for t in batch:
                all_score_entries.append({"label": t["label"], "score": 5, "reason": "Scoring unavailable"})

    # Match scores to thumbnails
    scores_by_label = {s["label"]: s for s in all_score_entries}
    scored = []
    for i, t in enumerate(thumbnails):
        score_entry = scores_by_label.get(t["label"])
        # Fall back to index-based match
        if not score_entry and i < len(all_score_entries):
            score_entry = all_score_entries[i]
        score_entry = score_entry or {}

        scored.append(ScoredThumbnail(
            label=t["label"],
            source_label=t.get("source_label", ""),
            score=float(score_entry.get("score", 5)),
            reasoning=score_entry.get("reason", "No score available"),
            file_path=t["file_path"],
            drive_url=t.get("drive_url", ""),
            is_variation=t.get("is_variation", False),
            system=t.get("system", 0),
        ))

    return scored


# ─── Select top 3 with system diversity ─────────────────────────────

def select_top_3(scored):
    """Select top 3, preferring variety across different systems.

    Algorithm:
    1. Sort all by score descending
    2. Pick highest scoring thumbnail
    3. For picks 2 and 3: prefer different SYSTEM if score gap < 2
    4. Prefer variations over sources (they have branding applied)
    """
    if len(scored) <= 3:
        return sorted(scored, key=lambda s: s.score, reverse=True)

    # Sort: score desc, prefer variations, then alphabetical label
    ranked = sorted(scored, key=lambda s: (-s.score, not s.is_variation, s.label))

    top_3 = [ranked[0]]
    used_systems = {ranked[0].system}

    for candidate in ranked[1:]:
        if len(top_3) >= 3:
            break

        # Prefer different system if close in score
        if candidate.system not in used_systems:
            top_3.append(candidate)
            used_systems.add(candidate.system)
        elif top_3[0].score - candidate.score < 2:
            # Close score but same system — skip to find diversity
            continue
        else:
            # Score gap > 2, just take the best available
            top_3.append(candidate)
            used_systems.add(candidate.system)

    # If we still need more (all from same system or narrow pool), fill remaining
    if len(top_3) < 3:
        for candidate in ranked:
            if candidate not in top_3:
                top_3.append(candidate)
                if len(top_3) >= 3:
                    break

    return top_3


# ─── Main pipeline ───────────────────────────────────────────────────

def run_thumbnail_pipeline(
    title,
    thumbnail_concepts=None,
    model=None,
    system_filter=None,
):
    """Full 5-system thumbnail pipeline.

    Args:
        title: Video title
        thumbnail_concepts: Concept descriptions from the content doc
        model: Gemini model for generation (default: Pro)
        system_filter: Run only this system number (1-5), or None for all

    Returns:
        ThumbnailServiceResult with top 3 picks and all scored thumbnails
    """
    t0 = time.time()

    print(f"\n{'='*60}")
    print(f"THUMBNAIL SERVICE v3.0 — 5-System Pipeline")
    print(f"Title: {title}")
    if thumbnail_concepts:
        print(f"Concepts: {len(thumbnail_concepts)}")
    if system_filter:
        print(f"System filter: System {system_filter} only")
    print(f"{'='*60}")

    gen_model = model or NANO_BANANA_PRO_MODEL
    concepts = thumbnail_concepts or []

    # Create master session directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)[:50].strip()
    session_dir = os.path.join(OUTPUT_DIR, f"{timestamp}_{safe_title}")
    os.makedirs(session_dir, exist_ok=True)

    # Load face refs once (shared by systems 1, 2, 3, 5)
    face_refs = get_face_references()

    all_thumbnails = []
    run_systems = [system_filter] if system_filter else [1, 2, 3, 4, 5]

    # ── System 1: Viral Videos (sequential — generate then transform) ──
    if 1 in run_systems:
        try:
            s1_thumbs = system_1_viral(title, session_dir, gen_model)
            all_thumbnails.extend(s1_thumbs)
        except Exception as e:
            print(f"  ERROR: System 1 failed: {e}")

    # ── Systems 2, 3, 4, 5: Run in parallel ───────────────────────────
    parallel_systems = {}
    if 2 in run_systems:
        parallel_systems[2] = ("system_2_favorites", (title, concepts, face_refs, os.path.join(session_dir, "system2_favorites"), gen_model))
    if 3 in run_systems:
        parallel_systems[3] = ("system_3_ai_face", (title, concepts, face_refs, os.path.join(session_dir, "system3_ai_face"), gen_model))
    if 4 in run_systems:
        parallel_systems[4] = ("system_4_no_face", (title, concepts, os.path.join(session_dir, "system4_no_face"), gen_model))
    if 5 in run_systems:
        parallel_systems[5] = ("system_5_trigger", (title, concepts, face_refs, os.path.join(session_dir, "system5_trigger"), gen_model))

    system_funcs = {
        2: system_2_favorites,
        3: system_3_ai_face,
        4: system_4_no_face,
        5: system_5_trigger,
    }

    if parallel_systems:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {}
            for sys_num, (func_name, args) in parallel_systems.items():
                futures[pool.submit(system_funcs[sys_num], *args)] = sys_num

            for future in as_completed(futures):
                sys_num = futures[future]
                try:
                    result = future.result()
                    if result:
                        all_thumbnails.extend(result)
                except Exception as e:
                    print(f"  ERROR: System {sys_num} failed: {e}")

    if not all_thumbnails:
        print("\nERROR: All systems failed. No thumbnails produced.")
        return ThumbnailServiceResult(
            top_3=[], all_scored=[], thumbnail_concepts=concepts,
            title=title, session_dir=session_dir, total_time=time.time() - t0,
        )

    # ── Upload ALL to Drive + create 6 Airtable records ─────────────
    print(f"\n{'='*60}")
    print(f"UPLOADING {len(all_thumbnails)} THUMBNAILS → Drive + 6 Airtable Records")
    print(f"{'='*60}")

    _upload_to_airtable_records(title, all_thumbnails, face_refs)

    # ── Score all thumbnails (exclude source references) ────────────
    thumbnails_to_score = [t for t in all_thumbnails if not t.get("is_source_ref", False)]
    print(f"\n{'='*60}")
    print(f"SCORING — {len(thumbnails_to_score)} thumbnails across {len(set(t['system'] for t in thumbnails_to_score))} systems")
    if len(all_thumbnails) != len(thumbnails_to_score):
        print(f"  ({len(all_thumbnails) - len(thumbnails_to_score)} source references excluded from scoring)")
    print(f"{'='*60}")

    scored = score_thumbnails(thumbnails_to_score, title, concepts)

    # ── Select top 3 ─────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"SELECTING TOP 3")
    print(f"{'='*60}")

    top_3 = select_top_3(scored)
    # Drive URLs already set by _upload_all_to_single_record, propagate to ScoredThumbnail
    # Match drive_url from all_thumbnails dict to ScoredThumbnail objects
    url_map = {t["file_path"]: t.get("drive_url", "") for t in all_thumbnails}
    for t in top_3:
        if not t.drive_url and t.file_path in url_map:
            object.__setattr__(t, "drive_url", url_map[t.file_path])

    total_time = time.time() - t0

    # ── Print results ─────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"TOP 3 MUST-CLICK THUMBNAILS")
    print(f"{'='*60}")
    system_names = {1: "Viral", 2: "Favorites", 3: "AI+Face", 4: "NoFace", 5: "Trigger"}
    for i, t in enumerate(top_3):
        sys_name = system_names.get(t.system, "?")
        print(f"  #{i+1}: {t.label} (System {t.system}: {sys_name}) — Score: {t.score}/10")
        print(f"       {t.reasoning}")
        if t.drive_url:
            print(f"       {t.drive_url}")
        print(f"       File: {t.file_path}")

    print(f"\nAll scores by system:")
    for sys_num in sorted(set(s.system for s in scored)):
        sys_name = system_names.get(sys_num, "?")
        sys_scored = [s for s in scored if s.system == sys_num]
        sys_scored.sort(key=lambda s: -s.score)
        print(f"\n  System {sys_num} ({sys_name}):")
        for t in sys_scored:
            tag = " <<<" if t in top_3 else ""
            print(f"    {t.label}: {t.score}/10 — {t.reasoning}{tag}")

    print(f"\nTotal pipeline time: {total_time:.0f}s")
    print(f"Thumbnails produced: {len(all_thumbnails)} (scored: {len(scored)})")
    print(f"Session: {session_dir}")
    print(f"{'='*60}")

    return ThumbnailServiceResult(
        top_3=top_3,
        all_scored=scored,
        thumbnail_concepts=concepts,
        title=title,
        session_dir=session_dir,
        total_time=total_time,
    )


# ─── CLI ─────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Thumbnail Service v3.0 — 5-System Pipeline with Must-Click Score"
    )
    parser.add_argument("title", type=str, help="Video title")
    parser.add_argument("--concepts", nargs="*", default=None,
                        help="Thumbnail concept descriptions (from content doc)")
    parser.add_argument("--model", type=str, choices=["flash", "pro"], default="pro",
                        help="Generation model (default: pro)")
    parser.add_argument("--system", type=int, choices=[1, 2, 3, 4, 5], default=None,
                        help="Run only this system (1-5). Default: all systems")
    args = parser.parse_args()

    from config import NANO_BANANA_MODEL
    gen_model = NANO_BANANA_MODEL if args.model == "flash" else None

    result = run_thumbnail_pipeline(
        title=args.title,
        thumbnail_concepts=args.concepts,
        model=gen_model,
        system_filter=args.system,
    )

    if not result.top_3:
        print("\nNo thumbnails produced. Check logs above for errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
