# Thumbnail System Guide (v2.0)

## What It Does

A **2-step pipeline** that generates original YouTube thumbnails:

**Step 1 — Generate** (`generate_thumbnail.py`): Creates 6 thumbnail options inspired by top-performing viral thumbnails, using your face references.

**Step 2 — Transform** (`transform_thumbnail.py`): Takes those 6 thumbnails and creates original variations — white shirt, yellow gradient text, simplified backgrounds, text replaced with new video title.

Both steps upload results to Google Drive and attach to Airtable records.

## Quick Start — Full Pipeline

```bash
# Step 1: Generate 6 thumbnails from viral inspiration
python3 thumbnail_system/generate_thumbnail.py "Your Video Title Here"

# Step 2: Transform to make them original (auto-finds latest session)
python3 thumbnail_system/transform_thumbnail.py "Your Video Title Here" --latest
```

That's it! No SSL exports needed — both scripts handle that automatically.

## Step 1: Generate (`generate_thumbnail.py`)

```bash
# Standard run — pulls viral thumbnails automatically
python3 thumbnail_system/generate_thumbnail.py "Your Video Title Here"

# Use a specific source image for all 6 options
python3 thumbnail_system/generate_thumbnail.py "Title" --source-image path/to/thumbnail.png

# Use a source image from URL
python3 thumbnail_system/generate_thumbnail.py "Title" --source-url "https://i.ytimg.com/vi/XXX/maxresdefault.jpg"

# Use Flash model (faster, lower quality)
python3 thumbnail_system/generate_thumbnail.py "Title" --model flash

# Generate only 3 options instead of 6
python3 thumbnail_system/generate_thumbnail.py "Title" --count 3
```

### What Happens

1. Auto-configures SSL certificates
2. Loads ALL face references from `face_references/` (currently 9 face-only crops)
3. **Source selection**:
   - Default: Fetches top 10 **unused** viral videos from Mate OS (filtered by `NOT({Thumbnail Used})`), sorted by Outlier Score, picks 6 at random
   - With `--source-image`: Uses one local image as source for all 6 options
   - With `--source-url`: Downloads one image from URL as source for all 6 options
4. Marks selected viral thumbnails as `Thumbnail Used = True` (so next run picks fresh ones)
5. **Parallel generation** (3 workers): Sends to Nano Banana Pro with prompt + source + all face refs
6. Saves locally to `thumbnail_system/output/{timestamp}_{title}/`
7. Uploads to Google Drive (with 3x retry)
8. Creates Airtable record in Thumbnail Generations table with Options A-F + Source A-F attached

## Step 2: Transform (`transform_thumbnail.py`)

```bash
# Transform the most recent generation session (3 variations each)
python3 thumbnail_system/transform_thumbnail.py "Your Video Title Here" --latest

# Transform a specific session
python3 thumbnail_system/transform_thumbnail.py "Title" --session-dir path/to/session

# Use Flash model for faster (lower quality) transforms
python3 thumbnail_system/transform_thumbnail.py "Title" --latest --model flash

# Override number of variations (default: 3)
python3 thumbnail_system/transform_thumbnail.py "Title" --latest --variations 1
```

### What It Changes
- **Shirt**: Always changed to **plain white t-shirt** (never black or any other color)
- **Text**: REPLACED with new video title phrases, styled with **yellow gradient** (bright yellow to gold)
- **Background**: Simplified — more minimal, professional, less crowded
- **Logos/Icons**: Slightly altered (different shade, shape) — NOT exact copies
- **Clutter removed**: Extra icons, gear/clock icons, crossed-out symbols stripped out
- **Keeps**: Same face, expression, position, layout, composition, and overall vibe

### Packaged Output Folder
Each thumbnail comes as a **package of 4** (1 source + 3 variations). Files are named so they sort together when you open the folder:

```
A0_source.png   ← original viral thumbnail
A1_v1.png       ← variation 1 (white shirt, yellow text, clean bg)
A2_v2.png       ← variation 2
A3_v3.png       ← variation 3
B0_source.png   ← next original viral thumbnail
B1_v1.png       ← variation 1
B2_v2.png       ← variation 2
B3_v3.png       ← variation 3
...
```

6 sources × 3 variations = **24 files total** (6 packages of 4).

### What Happens
1. Finds the input session directory (latest generation, skips transform/packaged folders)
2. Loads all option_A-F.png and source_A-F.png files from that session
3. Loads all face references
4. **Parallel transformation** (3 workers): Generates 3 variations per source (18 total)
5. **Packages output**: Copies source thumbnails with `X0_source.png` naming
6. Saves to `thumbnail_system/output/{timestamp}_packaged_{title}/`
7. Uploads to Drive and creates new Airtable record (title prefixed with "Original:")

## Performance

| Version | 6 thumbnails | Notes |
|---|---|---|
| v1.0 (sequential) | ~4-6 min | One at a time, 2s delay between each |
| v2.0 (parallel) | ~80-120s | 3 workers, no delays needed |

## Where Things Live

| What | Where |
|---|---|
| Generator script (Step 1) | `thumbnail_system/generate_thumbnail.py` |
| Transformer script (Step 2) | `thumbnail_system/transform_thumbnail.py` |
| Config | `thumbnail_system/config.py` |
| Face references (face-only crops) | `face_references/` (9 PNGs, ~400-550px) |
| Full-frame extracts (pre-crop) | `face_references_new/` |
| Face cropping script | `pipeline/crop_faces.py` |
| Local output | `thumbnail_system/output/` |
| Airtable results | Mate OS > Thumbnail Generations (`YOUR_THUMBNAIL_GENERATIONS_TABLE_ID`) |
| Viral inspiration source | Mate OS > Viral Videos (`YOUR_VIRAL_VIDEOS_TABLE_ID`) |
| Face extraction SOP | `skills/FACE_REFERENCE_EXTRACTION_SOP.md` |

## Models

| Model | ID | When to Use |
|---|---|---|
| Nano Banana Pro | `gemini-3-pro-image-preview` | Default. Best face likeness and quality. |
| Flash | `gemini-2.5-flash-image` | Quick drafts, no rate limits. Face won't match well. |

Pro model may return 503 under load. The script auto-retries up to 4 times with 15/30/45s backoff.

## Key Design Decisions

- Viral thumbnails ARE the style reference (no separate templates or competitor folders)
- ALL face references sent every time (more = better likeness)
- Face references must be **FACE ONLY** — no body, shoulders, hands (use `pipeline/crop_faces.py`)
- 16:9 aspect ratio enforced in the prompt
- Final thumbnails always have **plain white t-shirt** (set in transform prompt)
- Text uses **yellow gradient** (bright yellow to gold, set in transform prompt)
- Generation is parallel (3 workers); Drive uploads are sequential (more reliable)
- Viral thumbnails are marked as used after each run to ensure fresh inspiration
- Output goes to Mate OS (not the old Thumbnail Mate base)

## Troubleshooting

**503 errors on Pro model**: Just retry. The script handles this automatically. If it fails all 4 attempts, wait a few minutes and run again.

**Drive upload fails**: Check that `youtube_token.pickle` exists and credentials aren't expired. Delete it and run `pipeline/youtube_publisher.py` once to re-auth. Uploads retry 3x automatically.

**Face doesn't look right**: Ensure face references are FACE ONLY (no body). Pro model is much better than Flash. More face reference variety helps.

**Airtable attachment fails**: Check that Option A-F and Source A-F fields exist as Attachment type in the Thumbnail Generations table. The script auto-creates them on first run.

**Thumbnails look repetitive / same viral sources**: Check the Viral Videos table — all thumbnails may be marked as used. Uncheck `Thumbnail Used` to reuse them, or add new viral inspiration.

**No unused viral thumbnails**: The filter `NOT({Thumbnail Used})` returns empty. Go to Viral Videos table in Mate OS, uncheck `Thumbnail Used` on some rows, or add new high-performing thumbnails.
