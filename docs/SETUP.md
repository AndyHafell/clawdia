# Clawdia — Full Setup Guide

## Prerequisites

| Tool | Required | How to Get It |
|------|----------|---------------|
| Python 3.10+ | Yes | `brew install python` or [python.org](https://python.org) |
| Claude Code CLI | Yes | [docs.anthropic.com/claude-code](https://docs.anthropic.com/en/docs/claude-code) |
| Google Cloud account | Yes | [console.cloud.google.com](https://console.cloud.google.com) |
| Airtable account | Yes | [airtable.com](https://airtable.com) (free tier works) |
| Google AI Studio API key | Yes | [aistudio.google.com](https://aistudio.google.com) |
| Telegram bot (optional) | No | For daily notifications |

---

## Step 1: Clone and Install

```bash
git clone https://github.com/YOUR_USERNAME/clawdia.git
cd clawdia

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Google Cloud Setup

### Create a Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (e.g., "Clawdia")
3. Note the project ID

### Enable APIs
1. Go to **APIs & Services > Library**
2. Enable **YouTube Data API v3**
3. Enable **Google Drive API**

### Create OAuth Credentials
1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth 2.0 Client ID**
3. Application type: **Desktop app**
4. Download the JSON file
5. Rename it to `client_secrets.json` and place it in the project root

### First Run (OAuth Consent)
The first time you run any script that uses YouTube or Drive, it will open a browser for OAuth consent. After approving:
- A `youtube_token.pickle` file is created
- Subsequent runs use this token automatically
- Delete `youtube_token.pickle` to force re-authentication

### Scopes Needed
- `https://www.googleapis.com/auth/youtube.upload` — Upload videos
- `https://www.googleapis.com/auth/drive` — Read/write Google Drive files

---

## Step 3: Airtable Setup

### Create a Base
1. Go to [Airtable](https://airtable.com) and create a new base
2. Create these tables:

| Table Name | Key Fields |
|-----------|------------|
| **Content Long-Form** | Title (text), Status (single select), YouTube URL (URL), Thumbnail (attachment) |
| **Viral Videos** | Title (text), Outlier Score (number), Thumbnail (attachment), Thumbnail Used (checkbox), Views (number), Published Date (date), Channel (text), URL (URL) |
| **Thumbnail Generations** | Title (text), Session (text), Option A-F (attachment fields) |
| **Show Docs** | Title (text), Date (date), Google Doc URL (URL), Status (single select) |

### Status Field Options (Content Long-Form)
- Draft
- Generating Thumbnail
- Ready to Upload
- Uploading
- Published
- Error

### Get Your IDs
1. **Base ID**: Open your base, look at the URL — it starts with `app...`
2. **Table IDs**: Use the Airtable API docs or URL — table IDs start with `tbl...`
3. **Personal Access Token**: Go to [airtable.com/create/tokens](https://airtable.com/create/tokens)

### Update Config
Add your IDs to:
- `.env` — `AIRTABLE_PERSONAL_ACCESS_TOKEN`
- `thumbnail_system/config.py` — Base ID and table IDs
- `CLAUDE.md` — Reference IDs for Claude Code

See [AIRTABLE_SETUP.md](AIRTABLE_SETUP.md) for detailed schema.

---

## Step 4: Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
# Required
Google_AI_Studio=your_gemini_api_key
AIRTABLE_PERSONAL_ACCESS_TOKEN=your_airtable_pat

# Required for YouTube upload
Youtube_data_key=your_youtube_api_key

# Optional
Telegram_access_token=your_telegram_bot_token
Telegram_chat_id=your_chat_id
n8n_API_KEY=your_n8n_key
```

---

## Step 5: Face References (for Thumbnails)

The thumbnail system needs face-only reference images of you:

1. Record yourself on camera from 3+ angles
2. Extract frames using FFmpeg:
   ```bash
   ffmpeg -i video.mp4 -vf "fps=1" face_references_new/frame_%04d.png
   ```
3. Run the face cropper:
   ```bash
   python3 pipeline/crop_faces.py
   ```
4. Review the crops in `face_references/` — they should show face only (hair to chin, ear to ear)
5. Delete bad crops, keep 5-10 good ones

See `skills/FACE_REFERENCE_EXTRACTION_SOP.md` for the full process.

---

## Step 6: Test It

### Test Thumbnail Generation
```bash
python3 thumbnail_system/generate_thumbnail.py "Test Video Title"
```

### Test YouTube Upload
```bash
# Set SSL first
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
export REQUESTS_CA_BUNDLE=$SSL_CERT_FILE

python3 pipeline/youtube_publisher.py --local-file "test_video.mp4"
```

### Test with Claude Code
```bash
cd clawdia
claude
# Then say: "Generate thumbnails for 'Test Video'"
```

---

## Step 7: Daily Automation (Optional)

To run show docs automatically every morning:

### macOS (launchd)
1. Edit `scripts/run_showdoc.sh` with your paths
2. Copy the plist to LaunchAgents:
   ```bash
   cp scripts/com.clawdia.showdoc.plist ~/Library/LaunchAgents/
   ```
3. Load it:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.clawdia.showdoc.plist
   ```
4. Set wake schedule:
   ```bash
   sudo pmset repeat wakeorpoweron MTWRFSU 06:55:00
   ```

### Linux (cron)
```bash
crontab -e
# Add: 0 7 * * * cd /path/to/clawdia && bash scripts/run_showdoc.sh
```

See `skills/DAILY_SHOWDOC_AUTOMATION_SOP.md` for details.

---

## Troubleshooting

### SSL Certificate Errors
```bash
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
export REQUESTS_CA_BUNDLE=$SSL_CERT_FILE
```

### OAuth Token Expired
```bash
rm youtube_token.pickle
# Run any script — it will re-authenticate
```

### Gemini 503 Errors
The Pro model occasionally returns 503. The scripts retry automatically (4 attempts). If it persists, use `--model flash` as fallback.

### Airtable Rate Limits
Airtable allows 5 requests/second. The scripts handle this with built-in delays. If you hit limits, add `time.sleep(0.3)` between calls.
