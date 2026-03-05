# 📹 YouTube Publisher - Content Mate (Long-Form)

Automated YouTube video publishing system that handles:
- ✅ AI-generated titles and descriptions
- ✅ AI-generated thumbnails (using your existing Thumbnail_System)
- ✅ Airtable tracking in "Content Mate (Long-Form)" table
- ⚠️  YouTube upload (requires OAuth2 setup - see below)

## Quick Start

### Option 1: Use the wrapper script (easiest)

```bash
./publish-youtube.sh "https://drive.google.com/open?id=YOUR_FILE_ID"
```

### Option 2: Use the Python script directly

```bash
python3 pipeline/youtube_publisher.py --drive-url "https://drive.google.com/open?id=YOUR_FILE_ID"
```

### Option 3: Just ask Claude!

Simply say:
> "Hey, publish this video: https://drive.google.com/open?id=..."

## What It Does

1. **Creates Airtable Record** - Adds entry to "📹 Content Mate (Long-Form)" table
2. **Generates Metadata** - AI creates title, description, and tags
3. **Generates Thumbnails** - Creates 3 thumbnail options using Nano Banana
4. **Downloads Video** - Pulls video from Google Drive
5. **Uploads to YouTube** - Publishes to your channel (requires setup)
6. **Updates Airtable** - Marks as published with video ID

## Airtable Table

The system uses the **"📹 Content Mate (Long-Form)"** table in your Mate OS:

https://airtable.com/YOUR_AIRTABLE_BASE_ID/YOUR_CONTENT_TABLE_ID

### Fields:
- **📹 Video Title** - Main title
- **Description** - Full YouTube description
- **Google Drive Path** - Original video URL
- **Status** - Current state (Draft → Generating Thumbnail → Ready → Uploading → Published)
- **YouTube Video ID** - Video ID after upload
- **Thumbnail Path** - Local path to selected thumbnail
- **Tags** - Comma-separated YouTube tags
- **Channel** - Target channel (defaults to "Your Channel")
- **Published Date** - When it went live

## Next Steps (YouTube OAuth Setup)

To enable actual YouTube uploads, you need to:

1. **Enable YouTube Data API v3**
   - Go to: https://console.cloud.google.com/
   - Create a new project or select existing
   - Enable "YouTube Data API v3"

2. **Create OAuth Credentials**
   - Navigate to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
   - Application type: Desktop app
   - Download the JSON file as `client_secrets.json`

3. **Install Google API Client**
   ```bash
   pip install google-api-python-client google-auth-oauthlib
   ```

4. **Update pipeline/youtube_publisher.py**
   - Uncomment the YouTube upload implementation
   - Add OAuth2 flow using `client_secrets.json`

## Usage Examples

### Simple publish (auto-generate everything)
```bash
./publish-youtube.sh "https://drive.google.com/open?id=YOUR_GOOGLE_DRIVE_FILE_ID"
```

### Custom title
```bash
./publish-youtube.sh "https://drive.google.com/open?id=..." "My Custom Video Title"
```

### From Python with custom metadata
```bash
python3 pipeline/youtube_publisher.py \
  --drive-url "https://drive.google.com/open?id=..." \
  --title "Custom Title" \
  --description "Custom description" \
  --channel "Your Channel"
```

## Files

- `pipeline/youtube_publisher.py` - Main publishing script
- `publish-youtube.sh` - Simple wrapper for easy use
- `thumbnail_system/` - Existing thumbnail generation system (integrated)
- `.env` - API keys and tokens

## Dependencies

Required Python packages:
```bash
pip install gdown  # For Google Drive downloads
```

Optional (for YouTube upload):
```bash
pip install google-api-python-client google-auth-oauthlib
```

## Troubleshooting

### "gdown not installed"
```bash
pip install gdown
```

### "Could not extract file ID"
Make sure your Google Drive URL includes the file ID parameter

### Thumbnail generation fails
Check that `thumbnail_system/config.py` has valid GEMINI_API_KEY

## Future Enhancements

- [ ] Complete YouTube OAuth2 implementation
- [ ] Interactive thumbnail selection (choose from A/B/C options)
- [ ] Scheduled publishing (upload as draft, publish later)
- [ ] Batch processing (upload multiple videos)
- [ ] Enhanced title/description templates
- [ ] Auto-update Mate OS "Ready" task when done
- [ ] n8n workflow integration for Telegram triggers
