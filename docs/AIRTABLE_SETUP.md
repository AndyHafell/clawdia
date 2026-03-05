# Airtable Setup Guide

Clawdia uses Airtable as its content management database. This guide walks you through setting up the required tables.

## Base Structure

Create one Airtable base (e.g., "Content Hub") with these tables:

---

## Table 1: Content Long-Form

Tracks every video from idea to published.

| Field Name | Type | Notes |
|-----------|------|-------|
| Title | Single line text | Video title |
| Status | Single select | Draft, Generating Thumbnail, Ready to Upload, Uploading, Published, Error |
| YouTube URL | URL | Filled after upload |
| YouTube Video ID | Single line text | Filled after upload |
| Thumbnail | Attachment | Selected thumbnail |
| Description | Long text | AI-generated description |
| Tags | Long text | Comma-separated tags |
| Google Drive URL | URL | Source video location |
| Published Date | Date | When uploaded to YouTube |

---

## Table 2: Viral Videos

Your inspiration library — top-performing videos in your niche.

| Field Name | Type | Notes |
|-----------|------|-------|
| Title | Single line text | Video title |
| Channel | Single line text | Creator name |
| URL | URL | YouTube video URL |
| Views | Number | View count |
| Outlier Score | Number | How much it outperformed the channel average (e.g., 5.2x) |
| Thumbnail | Attachment | Video thumbnail image |
| Thumbnail Used | Checkbox | Marked true after used for generation |
| Published Date | Date | When the video was published |
| Niche | Single select | Topic category |

**How to populate**: Use `pipeline/deploy_viral_radar.py` to automatically scan channels and calculate outlier scores, or add manually.

---

## Table 3: Thumbnail Generations

Stores generated thumbnail batches.

| Field Name | Type | Notes |
|-----------|------|-------|
| Title | Single line text | "Video Title — Session timestamp" |
| Session | Single line text | Timestamp identifier |
| Option A | Attachment | Generated thumbnail A |
| Option B | Attachment | Generated thumbnail B |
| Option C | Attachment | Generated thumbnail C |
| Option D | Attachment | Generated thumbnail D |
| Option E | Attachment | Generated thumbnail E |
| Option F | Attachment | Generated thumbnail F |
| Source Thumbnails | Link to Viral Videos | Which viral thumbnails were used |
| Model | Single select | gemini-3-pro, gemini-2.5-flash |

---

## Table 4: Show Docs

Tracks daily filming outlines.

| Field Name | Type | Notes |
|-----------|------|-------|
| Title | Single line text | "Show Doc — YYYY-MM-DD" |
| Date | Date | Show date |
| Google Doc URL | URL | Link to the Google Doc |
| Status | Single select | Draft, Ready, Filmed, Published |
| Topic 1 | Single line text | First topic name |
| Topic 2 | Single line text | Second topic name |
| Topic 3 | Single line text | Third topic name |

---

## Table 5: Hall of Fame (Optional)

Proven video formats that work.

| Field Name | Type | Notes |
|-----------|------|-------|
| Format Name | Single line text | e.g., "New Tool Build-Along" |
| Description | Long text | What this format is about |
| Structure | Long text | Step/act/point template |
| Best For | Single line text | When to use this format |
| Example Videos | URL | Links to successful examples |

---

## Getting Your IDs

### Base ID
1. Open your base in Airtable
2. Look at the URL: `https://airtable.com/appXXXXXXXXXXXX/...`
3. The `app...` part is your base ID

### Table IDs
1. Click on a table tab
2. Look at the URL: `https://airtable.com/appXXX/tblYYYYYYYYYYYY/...`
3. The `tbl...` part is your table ID

### Personal Access Token
1. Go to [airtable.com/create/tokens](https://airtable.com/create/tokens)
2. Create a new token with these scopes:
   - `data.records:read`
   - `data.records:write`
   - `schema.bases:read`
3. Give it access to your base
4. Copy the token to your `.env` file

---

## Where to Put Your IDs

After getting your IDs, update these files:

1. **`.env`** — Your Personal Access Token
2. **`thumbnail_system/config.py`** — Base ID and all table IDs
3. **`CLAUDE.md`** — Reference IDs so Claude Code knows where to look

Replace all `YOUR_*` placeholders with your actual IDs.
