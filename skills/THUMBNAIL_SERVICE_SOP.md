# Thumbnail Service v2.0 — Standard Operating Procedure

## Purpose
Generate 21 thumbnails across 4 creative systems, score all with "Must-Click Score", select top 3 with system diversity, and create 6 Airtable records for easy review. Each system takes a different creative approach to maximize variety. A feedback memory system learns from your feedback over time.

## When to Use
- During the **Content Doc Process** (Step 8.5, after text approval)
- During the **Show Doc Process** (future integration)
- Anytime you need thumbnails for a video

## Quick Start

```bash
# Full pipeline — all 4 systems (21 thumbnails → 6 Airtable records)
python3 pipeline/thumbnail_service.py "Video Title" --concepts "concept A description" "concept B description"

# Single system only (for testing)
python3 pipeline/thumbnail_service.py "Video Title" --system 1
python3 pipeline/thumbnail_service.py "Video Title" --system 2 --concepts "AI automation"
python3 pipeline/thumbnail_service.py "Video Title" --system 3 --concepts "concept"
python3 pipeline/thumbnail_service.py "Video Title" --system 4 --concepts "concept"

# Flash model (faster, lower quality)
python3 pipeline/thumbnail_service.py "Video Title" --model flash --concepts "concept"
```

## The 4 Systems

| System | Source | Face Refs? | Transform? | Output |
|--------|--------|-----------|------------|--------|
| **1 — Viral Videos** | 3 viral thumbnails from Airtable | Yes | Yes (yellow gradient) | 12 (3 sources + 9 variations) |
| **2 — Favorite Thumbnails** | 3 random from Favorites table | Yes | No | 3 |
| **3 — AI + Face** | Text prompt + concepts only | Yes | No | 3 |
| **4 — No Face** | Text prompt only | No | No | 3 |
| | | | | **21 total (18 scored)** |

### System 1 — Viral Videos (12 images, 9 scored)
- Pulls 3 unused viral thumbnails from the Viral Videos table (sorted by Outlier Score)
- Generates 3 options via Gemini Pro (face refs + viral inspiration)
- Transforms each into 3 original variations (white shirt, yellow gradient text, simplified background)
- **Text is REPLACED** with new video title phrases (not kept from the viral source)
- Includes source thumbnails in Airtable for reference comparison
- Sources are excluded from scoring (only variations are scored)
- Total: 3 sources + 9 variations = 12 images (9 scored)
- Marks used viral thumbnails as `Thumbnail Used = True`

### System 2 — Favorite Thumbnails (3 thumbnails)
- Fetches all records from the Favorites table
- Randomly selects 3 favorites
- Downloads the `Final` attachment from each
- Remakes each in the EXACT same style but about the new video
- **Layout rules**: text at TOP only, max 2-3 elements, no extra icons
- Keeps: style, color palette, layout, polish. Changes: face, text, topic, shirt to white
- Total: 3 thumbnails

### System 3 — AI + Face (3 thumbnails)
- No reference image — purely from text prompt + face references
- Uses thumbnail concepts from the content doc as creative direction
- **Layout**: person RIGHT (~40%), text TOP, one graphic LEFT/BOTTOM-LEFT
- Yellow gradient text, dark background, generous negative space
- Each of the 3 uses a different concept angle
- Total: 3 thumbnails

### System 4 — No Face (3 thumbnails)
- No face references, no reference image — all AI graphics
- **ONE focal graphic element** — logo, device mockup, or single stat
- Yellow gradient text at TOP, dark background, minimal design
- Maximum 2-3 colors, lots of negative space
- Designed to test: would someone click even without seeing a face?
- Total: 3 thumbnails

## Feedback Memory System

The service includes a **self-improving feedback memory** stored in `thumbnail_system/feedback_memory.json`. Rules learned from user feedback are automatically injected into every generation prompt.

### How It Works
1. After reviewing generated thumbnails, add feedback to the JSON file
2. `global_rules.always` — rules that apply to ALL systems
3. `global_rules.avoid` — things to NEVER do across all systems
4. `system_specific` — rules for individual systems (e.g., System 4 only)
5. Every future run automatically loads and appends these rules to prompts

### Adding New Feedback
Edit `thumbnail_system/feedback_memory.json`:
```json
{
  "global_rules": {
    "always": [
      "Text at the TOP of the thumbnail",
      "Yellow gradient text (bright yellow to gold)",
      "YOUR NEW RULE HERE"
    ],
    "avoid": [
      "Overcrowded compositions",
      "YOUR NEW AVOID RULE HERE"
    ]
  },
  "system_specific": {
    "system_4_no_face": {
      "notes": ["ONE focal graphic only"]
    }
  }
}
```

## What Happens Under the Hood

```
System 1: VIRAL VIDEOS (sequential)
   Pull 3 unused viral thumbnails → Gemini Pro → 3 options
   Transform 3 → 9 variations (yellow gradient, white shirt, new text)
   Include 3 source thumbnails for reference
   ~3-5 min

Systems 2, 3, 4: RUN IN PARALLEL
   System 2: 3 favorites → Gemini Pro → 3 remakes      (~60-90s)
   System 3: Text + face refs → Gemini Pro → 3 unique   (~60-90s)
   System 4: Text only → Gemini Pro → 3 no-face         (~60-90s)

UPLOAD: All 21 images → Google Drive → 6 Airtable records
   S1-A, S1-B, S1-C (1 source + 3 variations each)
   S2, S3, S4 (3 thumbnails each)

SCORING: 18 thumbnails → Gemini Flash → Must-Click Score (1-10)
   3 source refs excluded from scoring
   Batched if > 12 images, ~5-10s per batch

SELECTION: Top 3 with system diversity preference
   Prefer different systems for picks 2 and 3
```

**Total time**: ~5-8 minutes (System 1 is sequential, then 2-4 run in parallel)

## Must-Click Score Criteria

Each thumbnail is scored 1-10 based on how irresistible the click would be for the target avatar:

| Criteria | What It Measures |
|----------|-----------------|
| **CLARITY** | Can you tell what the video is about in under 1 second? |
| **EMOTION** | Does the facial expression trigger curiosity or excitement? |
| **CONTRAST** | Do the colors pop and stand out in a feed? |
| **BENEFIT SIGNAL** | Does the imagery promise a specific outcome or reveal? |
| **BRAND FIT** | Does this feel like an AI automation channel? |
| **TITLE-THUMBNAIL SYNERGY** | Does it complement (not repeat) the title? |

**Scale**: 1-3 scroll past, 4-6 might click, 7-8 strong click, 9-10 can't NOT click.

## Top 3 Selection Algorithm

1. Sort all 18 by score descending
2. Pick #1: highest score regardless of system
3. Pick #2: prefer different **system** if score gap < 2 points
4. Pick #3: prefer different **system** from both #1 and #2 if score gap < 2
5. Fallback: if system diversity not possible, just take highest scores

The ideal top 3 comes from 3 different creative approaches — giving maximum variety.

## Airtable Records (6 per run)

All records use the **"Thumbnails"** attachment field.

| Record | System | Images | Title Format |
|--------|--------|--------|-------------|
| S1-A | Viral Source A | 4 (1 source + 3 variations) | `S1-A Viral: {title}` |
| S1-B | Viral Source B | 4 (1 source + 3 variations) | `S1-B Viral: {title}` |
| S1-C | Viral Source C | 4 (1 source + 3 variations) | `S1-C Viral: {title}` |
| S2 | Favorites | 3 | `S2 Favorites: {title}` |
| S3 | AI+Face | 3 | `S3 AI+Face: {title}` |
| S4 | NoFace | 3 | `S4 NoFace: {title}` |

## Integration with Content Doc Process

The thumbnail service runs as **Step 8.5** in the Content Doc Process.

### Step 8.5: Generate + Score Thumbnails (4 Systems)

1. Extract the **best title** from the TITLES section
2. Extract both **thumbnail concept descriptions** from the THUMBNAIL IDEAS section
3. Run the service:
   ```bash
   python3 pipeline/thumbnail_service.py "Best Title Here" --concepts "Concept A..." "Concept B..."
   ```
4. Pipeline produces 21 thumbnails across 4 systems
5. 18 scored with Must-Click Score (3 sources excluded)
6. Top 3 selected (with system diversity preference)
7. Show the user the top 3 results with scores and system labels
8. Wait for user confirmation (or re-generate if needed)

## Output

### Label Scheme

| System | Labels |
|--------|--------|
| System 1 sources (3) | `S1_A0_source`, `S1_B0_source`, `S1_C0_source` |
| System 1 variations (9) | `S1_A1_v1`, `S1_A2_v2`, `S1_A3_v3`, ... `S1_C3_v3` |
| System 2 (3) | `S2_A`, `S2_B`, `S2_C` |
| System 3 (3) | `S3_A`, `S3_B`, `S3_C` |
| System 4 (3) | `S4_A`, `S4_B`, `S4_C` |

## Programmatic Usage

```python
from thumbnail_service import run_thumbnail_pipeline

result = run_thumbnail_pipeline(
    title="How I Film 3 Videos a Day Without Writing a Script",
    thumbnail_concepts=[
        "Split screen: chaos vs clean doc. Text: IT WRITES ITSELF",
        "Creator relaxed at desk, video thumbnails floating. Text: 3 VIDEOS/DAY"
    ],
)

# result.top_3 = list of 3 ScoredThumbnail objects
# result.all_scored = all 18 scored
# result.session_dir = local output folder
# result.total_time = pipeline time in seconds
```

## Key Rules
- **YELLOW gradient text** in all systems (bright yellow to gold, NOT orange)
- **White shirt** in all thumbnails that show a face (Systems 1, 2, 3)
- **Text at the TOP** — never at the bottom
- **Maximum 2-3 visual elements** — simplify aggressively
- **No crossed-out icons** — no red X marks, no "X over something"
- All face-based systems use ALL 9 face references from `face_references/`
- Viral thumbnails are marked as used after generation to prevent reuse
- Feedback memory rules from `feedback_memory.json` are auto-injected into all prompts

## Files

| File | Purpose |
|------|---------|
| `pipeline/thumbnail_service.py` | Main service (4 systems → score → select top 3) |
| `thumbnail_system/generate_thumbnail.py` | System 1 Step A: Generate from viral inspiration |
| `thumbnail_system/transform_thumbnail.py` | System 1 Step B: Transform to originals |
| `thumbnail_system/config.py` | Configuration, API keys (loaded from .env), table IDs |
| `thumbnail_system/feedback_memory.json` | Self-improving feedback rules |
| `face_references/` | Face-only reference crops (9 PNGs) |

## Tables

| Table | Purpose |
|-------|---------|
| Viral Videos | Source thumbnails for System 1 |
| Favorite Thumbnails | Source thumbnails for System 2 |
| Thumbnail Generations | Output records for all systems (6 per run) |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No unused viral thumbnails | Uncheck `Thumbnail Used` in Viral Videos table |
| System 1 fails entirely | Systems 2-4 still run; score whatever succeeded |
| < 3 favorites in table | Uses however many are available (even 1-2) |
| 503 errors during generation | Auto-retried 4x per image; wait and retry if all fail |
| Scoring returns all 5/10 | Gemini Flash call failed; check API key and quota |
| Thumbnails too cluttered | Add feedback to `feedback_memory.json` avoid rules |
| System 1 keeps wrong text | Ensure transform prompt has `{title}` placeholder |
| One system fails completely | Pipeline continues with remaining systems |
