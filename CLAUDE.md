# CLAUDE.md - Project Instructions for Claude Code

## Project Overview
This is your **YouTube Automation Pipeline** powered by Clawdia — it uploads videos, generates AI thumbnails, creates show docs, and tracks everything in Airtable.

## Skills-First Directive
Before starting ANY process, pipeline, or multi-step task, ALWAYS search the `skills/` folder first and read any relevant SOP or guide. Follow the documented process exactly — do not improvise or rely on memory if a skill doc exists. Available skills:
- `THUMBNAIL_SYSTEM_GUIDE.md` — Full thumbnail generation + transformation reference
- `FACE_REFERENCE_EXTRACTION_SOP.md` — Face reference extraction + cropping
- `YOUTUBE_PUBLISHER_README.md` — YouTube publisher setup and usage
- `YOUTUBE_UPLOAD_GUIDE.md` — YouTube upload process
- `CONTENT_DOC_PROCESS_SOP.md` — Content document creation process
- `SHOW_DOC_PROCESS_SOP.md` — Show document process
- `FORMAT_SELECTION_SOP.md` — Format selection process
- `VIRAL_RADAR_SOP.md` — Viral radar / video research process
- `HANDOFF_MORNING_AGENT.md` — Morning agent handoff process
- `DAILY_SHOWDOC_AUTOMATION_SOP.md` — Daily show doc automation (launchd + Claude Code)

If a task touches multiple skills, read ALL relevant ones before starting.

## Key Architecture
- `pipeline/` — All Python pipeline scripts (publisher, formatters, deployers)
  - `youtube_publisher.py` — Main script: uploads video to YouTube (OAuth), creates/updates Airtable records
  - `crop_faces.py` — Face reference cropping (OpenCV face detection, face-only crops)
  - `thumbnail_service.py` — 4-system thumbnail pipeline
- `thumbnail_system/` — Thumbnail generation engine (stays in root for import compatibility)
  - `generate_thumbnail.py` — Step 1: Generate 6 thumbnail options from viral inspiration
  - `transform_thumbnail.py` — Step 2: Originality Transformer (makes thumbnails original)
  - `config.py` — Thumbnail system configuration
- `skills/` — SOPs and documentation
- `context/` — Content about your channel, business planning, ideas, goals
- `projects/` — Tools and apps
- `assets/` — Media files, face references, branding
  - `face_references/` → symlinked from root for Python compatibility
- `scripts/` — Automation scripts (showdoc automation, daily cron helpers)

## Google Cloud Project
- **Project**: `YOUR_GCP_PROJECT_ID`
- **OAuth Client ID**: `YOUR_OAUTH_CLIENT_ID`
- **OAuth file**: `client_secrets.json`
- **Token file**: `youtube_token.pickle` (delete to force re-auth)
- **Enabled APIs**: YouTube Data API v3, Google Drive API
- **Scopes**: youtube.upload, drive (full access)

## Airtable (Base ID: `YOUR_AIRTABLE_BASE_ID`)
- **Content Long-Form**: `YOUR_CONTENT_TABLE_ID` — Video records
- **Viral Videos**: `YOUR_VIRAL_VIDEOS_TABLE_ID` — Top-performing thumbnails for inspiration
- **Thumbnail Generations**: `YOUR_THUMBNAIL_GENERATIONS_TABLE_ID` — Generated thumbnail output (Options A-F)
- **Status field options**: `Draft`, `Generating Thumbnail`, `Ready to Upload`, `Uploading`, `Published`, `Error`

### Work In Progress — Quick Access
When the user asks for "work in progress", "what's on my plate", or similar — go **straight to the Airtable API**. No browser needed.
```bash
# Token from .env (AIRTABLE_PERSONAL_ACCESS_TOKEN)
TOKEN="$(grep AIRTABLE_PERSONAL_ACCESS_TOKEN .env | cut -d= -f2)"

# In Progress (active tasks)
curl -s "https://api.airtable.com/v0/YOUR_AIRTABLE_BASE_ID/YOUR_IN_PROGRESS_TABLE_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('records', []):
    f = r.get('fields', {})
    name = f.get('Task Name', 'Untitled')
    shipped = f.get('Shipped', False)
    up_next = f.get('Up Next', False)
    if not shipped:
        tag = ' [Up Next]' if up_next else ' [ACTIVE]'
        print(f'  {name}{tag}')
"

# Up Next (queued tasks)
curl -s "https://api.airtable.com/v0/YOUR_AIRTABLE_BASE_ID/YOUR_UP_NEXT_TABLE_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('records', []):
    f = r.get('fields', {})
    name = f.get('Task Name', 'Untitled')
    print(f'  {name}')
"
```

**Filter logic:** Only show items where `Shipped` is NOT true. Items with `Up Next = True` are queued but not actively being worked on.

## Environment
- Python 3.10+ on macOS (also works on Linux)
- Thumbnail system auto-configures SSL (no manual exports needed)
- Publisher still needs manual SSL exports (see Running the Publisher)
- `.env` file holds API keys (Airtable, Gemini, etc.)

## Running the Publisher
```bash
# Must set SSL env vars first
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
export REQUESTS_CA_BUNDLE=$SSL_CERT_FILE

# Upload a local video
python3 pipeline/youtube_publisher.py --local-file "path/to/video.mp4"

# Upload from Google Drive
python3 pipeline/youtube_publisher.py --drive-url "https://drive.google.com/..."

# Split test (3 versions with different thumbnails)
python3 pipeline/youtube_publisher.py --local-file "video.mp4" --split-test
```

## Thumbnail Pipeline (2-Step Process)

### Step 1: Generate — `generate_thumbnail.py`
- Pulls top **unused** viral thumbnails from Viral Videos table (filtered by `NOT({Thumbnail Used})`, sorted by Outlier Score)
- Sends each to **Gemini Pro** (`gemini-3-pro-image-preview`) with ALL face refs
- Prompt: "Remake the YouTube thumbnail with my face. Output must be 16:9 aspect ratio (1920x1080)."
- Generates 6 options (A-F) in **parallel** (~80-120s), uploads to Drive, attaches to Airtable
- Marks used viral thumbnails as `Thumbnail Used = True`
- Supports `--source-image`, `--source-url`, `--count N`, `--model flash`
```bash
python3 thumbnail_system/generate_thumbnail.py "Video Title"
```

### Step 2: Transform — `transform_thumbnail.py`
- Takes the 6 generated thumbnails from Step 1 and creates **3 original variations each**
- Output is **packages of 4**: 1 source + 3 variations per thumbnail (24 images total)
- Changes shirt to **plain white t-shirt** (always white, never black)
- Applies **vertical gradient (bright yellow #FFD700 → deep gold #E8A800)** text in **Montserrat Black** font
- **Simplifies background** to dark grey/black with subtle blue tint
- Tweaks logos/icons slightly so they're not exact copies
- Keeps same layout, composition, face, and expression
- Run with `--latest` to auto-find the most recent generation session
- Output folder sorts perfectly: `A0_source.png`, `A1_v1.png`, `A2_v2.png`, `A3_v3.png`, `B0_source.png`...
```bash
python3 thumbnail_system/transform_thumbnail.py "Video Title" --latest
```

### Full Pipeline (both steps)
```bash
# Step 1: Generate from viral inspiration
python3 thumbnail_system/generate_thumbnail.py "Video Title"

# Step 2: Transform to make original (3 variations per source, packaged output)
python3 thumbnail_system/transform_thumbnail.py "Video Title" --latest
```

### Face References
- Must be **FACE ONLY** — no body, shoulders, or hands
- Live in `face_references/` (add your own face crops here)
- Extracted via FFmpeg + `pipeline/crop_faces.py`
- Full SOP: `skills/FACE_REFERENCE_EXTRACTION_SOP.md`

### Detailed Guides
- `skills/THUMBNAIL_SYSTEM_GUIDE.md` — Full thumbnail system reference
- `skills/FACE_REFERENCE_EXTRACTION_SOP.md` — Face extraction + cropping SOP

## Conventions
- Videos upload as **private** by default
- AI metadata (title, description, tags) generated via Gemini 2.5 Flash
- 6 thumbnail options (A-F) generated per video from viral inspiration
- Shirt in final thumbnails is always **plain white t-shirt** (customize in transform_thumbnail.py)
- Text styling uses **vertical gradient (bright yellow #FFD700 → deep gold #E8A800)** in **Montserrat Black** font
- Thumbnail text is **max 4 words** (ideally 2-3) — title handles the rest
- Backgrounds are **dark grey/black with subtle blue tint** (never pure black)
- Channel ID: set in `.env` and `thumbnail_system/config.py`

## FIGURE IT OUT DIRECTIVE
You never say "I can't" without first:
1. Searching for a solution independently (web search, docs, related tools)
2. Trying at least 2-3 different approaches
3. Checking if a workaround or alternative path exists
4. Only asking for help when genuinely blocked after exhausting all options
When you encounter an obstacle, your default is to solve it — not report it.
You are resourceful, persistent, and solution-focused.
The phrase "I can't do that" is not in your vocabulary unless you've
exhausted every reasonable option and can explain exactly why.

## NO BROWSER DIRECTIVE
Never use Chrome, a browser, or any browser-based approach to accomplish tasks.
Always use APIs, CLI tools, or direct HTTP requests (curl, python requests, etc.) instead.
If a task seems to require a browser, find the underlying API and use that.
