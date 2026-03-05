# Skool Livestream to YouTube — Standard Operating Procedure

## Purpose
Take a completed Skool livestream recording and publish it to YouTube as a long-form video, with AI-generated thumbnails, optimized metadata, and multiple title/thumbnail options for A/B testing.

## When to Use
- After completing a live stream on Skool
- The raw recording has been saved to `Raw Clips 26/Livestreams 26/`
- You want to repurpose it as a YouTube video on your channel

## System Components

| Component | Location |
|-----------|----------|
| Raw livestream files | `Raw Clips 26/Livestreams 26/` (Google Drive) |
| YouTube Publisher | `pipeline/youtube_publisher.py` |
| Thumbnail Generator (Step 1) | `thumbnail_system/generate_thumbnail.py` |
| Thumbnail Transformer (Step 2) | `thumbnail_system/transform_thumbnail.py` |
| Content Mate table | `YOUR_CONTENT_TABLE_ID` in Mate OS |
| Thumbnail Generations table | `YOUR_THUMBNAIL_GENERATIONS_TABLE_ID` in Mate OS |
| Viral Videos table | `YOUR_VIRAL_VIDEOS_TABLE_ID` in Mate OS |
| Channel | Your Channel (`YOUR_YOUTUBE_CHANNEL_ID`) |

## Inputs Required

1. **Video file** — the latest `.mp4` in `Raw Clips 26/Livestreams 26/`
2. **Content doc / inspiration** — user provides the livestream topic, outline, talking points, or show doc. This drives title, description, tags, and thumbnail direction.

## Process (5 Steps)

### Step 1: Identify the Latest Livestream
```bash
ls -lt "Raw Clips 26/Livestreams 26/" | head -5
```
Pick the most recent file. Confirm with user if multiple files from the same day.

### Step 2: Craft Metadata from Content Doc
Using the user's content doc / outline:
- **Title**: Create a primary title + 6-8 alternatives for A/B testing
- **Description**: Write a full YouTube description including:
  - Hook (first 2 lines visible in search)
  - Content breakdown with emoji bullets
  - Step-by-step outline matching the livestream flow
  - Call to action (Skool community link)
  - Hashtags
- **Tags**: Extract relevant keywords from the content doc

**Key difference from regular uploads**: Skool livestreams already have a topic and outline. Don't use AI auto-generation for the title/description — instead, craft them from the content doc the user provides. The content doc IS the source of truth.

### Step 3: Upload to YouTube (Background)
```bash
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
export REQUESTS_CA_BUNDLE=$SSL_CERT_FILE

python3 pipeline/youtube_publisher.py \
  --local-file "path/to/livestream.mp4" \
  --title "Primary Title Here" \
  --description "Crafted description here"
```
- Uploads as **private** by default
- Creates Airtable record in Content Mate
- Run in background (large files take several minutes)

### Step 4: Generate Thumbnails (Parallel with Upload)
Run the full 2-step thumbnail pipeline while the upload runs:

**Step 4a — Generate 6 options from viral inspiration:**
```bash
python3 thumbnail_system/generate_thumbnail.py "Video Title"
```
- Pulls top unused viral thumbnails, remakes with your face
- ~80-120 seconds, produces Options A-F

**Step 4b — Transform into original variations:**
```bash
python3 thumbnail_system/transform_thumbnail.py "Video Title" --latest
```
- Creates 3 variations per source (18 originals + 6 sources = 24 images)
- White shirt, orange gradient text, simplified backgrounds
- Packaged output: `A0_source.png`, `A1_v1.png`, `A2_v2.png`, `A3_v3.png`, etc.

### Step 5: Deliver Results
Present to user:
1. **YouTube video URL** (private, ready to review)
2. **Title options table** (8+ alternatives for A/B testing)
3. **Thumbnail options** (24 packaged images in output folder)
4. **Airtable records** (Content Mate + Thumbnail Generations)
5. **Next steps**: Review thumbnails, pick favorites, set video to public/unlisted

## Key Differences from Regular Upload Workflow

| Aspect | Regular Upload | Skool Livestream |
|--------|---------------|-----------------|
| **Source** | Pre-edited video | Raw livestream recording |
| **Metadata** | AI auto-generated | Crafted from user's content doc |
| **Thumbnails** | Publisher's basic 3 (A/B/C) | Full pipeline: 6 sources + 18 variations |
| **Title options** | Single AI title | 8+ alternatives for testing |
| **File size** | Varies | Typically 1-2+ GB (long livestreams) |
| **Upload time** | Minutes | 5-10+ minutes (run in background) |

## Tips
- Always run upload and thumbnail generation **in parallel** — they're independent
- Use the content doc verbatim for description hooks — the user's words resonate with their audience
- Livestream titles work best with curiosity/paradox hooks (e.g., "Without X" when you actually use X)
- Keep the video **private** until the user has reviewed thumbnails and picked a title
- The output folder sorts alphabetically — open it and scroll through packages of 4 to compare
