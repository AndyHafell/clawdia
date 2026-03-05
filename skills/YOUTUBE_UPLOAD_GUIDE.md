# 🎬 YouTube Publisher - Complete Guide

## 🎉 What We Built

A complete AI-powered YouTube publishing system that:
- ✅ **Generates AI titles & descriptions** using Gemini
- ✅ **Creates 3 AI-generated thumbnails** (Options A, B, C)
- ✅ **Stores thumbnail paths in Airtable** for easy access
- ✅ **Uploads videos to YouTube** with OAuth2
- ✅ **Auto-compresses thumbnails** to meet YouTube's size limits
- ✅ **Supports Google Drive URLs** - Download and upload automatically
- ✅ **Tracks everything in Airtable** (Content Mate table)
- ✅ **Uploads as "private"** by default (safe for testing)
- ✅ **Ready for YouTube Studio Test & Compare** - 3 thumbnails ready to upload

---

## 🚀 Quick Start

### Upload a Local Video

```bash
./upload-video.sh path/to/video.mp4
```

Or with a custom title:

```bash
./upload-video.sh path/to/video.mp4 "My Custom Title"
```

### Upload from Google Drive

```bash
python3 pipeline/youtube_publisher.py --drive-url "https://drive.google.com/open?id=YOUR_FILE_ID"
```

### 🧪 YouTube Test & Compare Workflow

The system automatically generates **3 AI thumbnails** (A, B, C) for every video and stores their paths in Airtable. To use YouTube's native A/B/C testing:

1. **Upload video** (using commands above)
2. **Check Airtable** - Find the "Thumbnail A/B/C Path" fields
3. **Go to YouTube Studio** → Find your video → "Test & Compare"
4. **Upload 3 thumbnails** from the paths shown in Airtable
5. **YouTube tests them** automatically and picks the winner

### Full Command Options

```bash
python3 pipeline/youtube_publisher.py --local-file path/to/video.mp4
python3 pipeline/youtube_publisher.py --local-file path/to/video.mp4 --title "Custom Title"
python3 pipeline/youtube_publisher.py --drive-url "YOUR_URL"
```

---

## 📋 What Happens When You Upload

1. **Creates Airtable Record** - Tracks the video in your Content Mate table
2. **Generates AI Metadata** - Gemini creates title, description, and tags
3. **Generates 3 Thumbnails** - AI creates 3 thumbnail options (A, B, C)
4. **Downloads from Google Drive** (if using --drive-url)
5. **Uploads to YouTube** - OAuth2 authentication, uploads as **"private"** with Thumbnail A
6. **Compresses & Uploads Thumbnail** - Automatically compresses if needed
7. **Stores Thumbnail Paths in Airtable** - All 3 thumbnail file paths saved:
   - `Thumbnail A Path`
   - `Thumbnail B Path`
   - `Thumbnail C Path`
   - `Thumbnail Folder` (parent folder)
8. **Updates Airtable** - Marks as "Uploaded (Private)" with video ID and URL

### 📂 Airtable Fields Created

Each upload creates these fields:
- **📹 Video Title** - AI-generated or custom title
- **Description** - AI-generated video description
- **Tags** - AI-generated tags
- **Status** - Current status (Draft → Generating → Uploading → Uploaded)
- **YouTube Video ID** - The video's unique ID
- **Published Date** - Upload timestamp
- **Thumbnail A/B/C Path** - File paths to the 3 generated thumbnails
- **Thumbnail Folder** - Parent folder containing all thumbnails
- **Google Drive Path** - Original video source (if from Drive)

---

## ⚙️ Configuration

### Privacy Status

Videos are uploaded as **"private"** by default (safe for testing). To change, edit line ~531 in `pipeline/youtube_publisher.py`:
```python
privacy_status='private'  # Change to 'unlisted' or 'public'
```

### Channel

Uploads to: **Your Channel** (YOUR_YOUTUBE_CHANNEL_ID)

### Thumbnail Selection

- **Uploaded to YouTube**: Option A (automatically compressed if needed)
- **Stored in Airtable**: All 3 options (A, B, C) with file paths
- **For Test & Compare**: Use paths from Airtable to manually upload B & C to YouTube Studio

### Thumbnail Compression

Thumbnails larger than 1.8MB are automatically compressed or converted to JPEG to meet YouTube's 2MB limit. This happens automatically - no configuration needed!

---

## 🎬 Using YouTube Studio's Test & Compare

After uploading a video, follow these steps to enable A/B/C thumbnail testing:

1. **Find thumbnail paths in Airtable**
   - Open your Content Mate record
   - Look for "Thumbnail A Path", "Thumbnail B Path", "Thumbnail C Path"
   - Copy these file paths

2. **Go to YouTube Studio**
   - Visit [YouTube Studio](https://studio.youtube.com)
   - Find your uploaded video
   - Click on the video to edit

3. **Enable Test & Compare**
   - In the thumbnail section, click "Test & Compare"
   - Upload Thumbnail B and Thumbnail C
   - YouTube will automatically test all 3 thumbnails

4. **YouTube picks the winner**
   - Tests run for up to 2 weeks
   - Winner is determined by watch time
   - Best performing thumbnail becomes permanent

---

## 🔑 API Keys Used

All configured in `.env`:
- ✅ `Google_AI_Studio` - Gemini for metadata & thumbnails
- ✅ `AIRTABLE_PERSONAL_ACCESS_TOKEN` - Airtable tracking
- ✅ OAuth2 credentials in `client_secrets.json`
- ✅ Saved token in `youtube_token.pickle` (auto-renewed)

---

## 📂 Files Created

- `pipeline/youtube_publisher.py` - Main Python script
- `upload-video.sh` - Simple wrapper for easy uploads
- `client_secrets.json` - OAuth2 credentials
- `youtube_token.pickle` - Saved authentication (renewed automatically)
- `YOUTUBE_PUBLISHER_README.md` - Original documentation

---

## 🎨 Thumbnail System

Generates 3 variations using Gemini's image generation:
- **Option A** - First style
- **Option B** - Second style
- **Option C** - Third style

Add face references to improve thumbnails:
```bash
# Add your photos to this folder:
face_references/
```

---

## 🔧 Troubleshooting

### "YouTube API libraries not installed"
```bash
pip3 install --break-system-packages google-api-python-client google-auth-oauthlib
```

### "Authentication required"
Delete `youtube_token.pickle` and re-run. Browser will open for re-authorization.

### "Video file not found"
Check the file path - use absolute paths or relative from Claude Folder.

---

## 📊 Airtable Integration

View uploaded videos:
https://airtable.com/YOUR_AIRTABLE_BASE_ID/YOUR_CONTENT_TABLE_ID

### Fields Tracked

**Video Information:**
- 📹 Video Title
- Description
- Tags
- Status
- YouTube Video ID
- Published Date
- Google Drive Path

**Thumbnail Information:**
- Thumbnail A Path (file path to Option A)
- Thumbnail B Path (file path to Option B)
- Thumbnail C Path (file path to Option C)
- Thumbnail Folder (parent directory)

### 📎 Adding Thumbnails as Attachments (Optional)

To store thumbnails directly in Airtable as downloadable files:

1. **Create attachment fields** in your Airtable base:
   - Add 3 new fields: "Thumbnail A", "Thumbnail B", "Thumbnail C"
   - Set field type to "Attachment"

2. **Manually upload thumbnails**:
   - Open the record in Airtable
   - Use the file paths from "Thumbnail A/B/C Path" fields
   - Drag & drop the thumbnail files into the attachment fields

3. **Download from Airtable**:
   - Click on any attachment field
   - Click "Download" to save the thumbnail
   - Upload to YouTube Studio's Test & Compare

**Note**: The API requires public URLs to automatically upload attachments. For now, thumbnails are stored locally and paths are saved in Airtable. Manual upload to attachment fields is optional but recommended for easy access.

---

## 🎯 Next Steps

1. **Upload your first video** - Try with a small test video
2. **Check Airtable** - Verify the record was created
3. **Check YouTube** - Video should be uploaded as "unlisted"
4. **Add face references** - For better AI thumbnails
5. **Customize privacy** - Set to private/public as needed

---

## 💡 Tips

- **Test with small videos first** (like walk1.mp4)
- **Videos upload as "unlisted"** - safe for testing
- **AI generates everything** - but you can override with --title and --description
- **Thumbnails are automatic** - Option A is selected by default
- **OAuth2 token auto-renews** - you only authorize once

---

## 🔗 Resources

- [Google Cloud Console](https://console.cloud.google.com)
- [YouTube Studio](https://studio.youtube.com)
- [Airtable Content Mate](https://airtable.com/YOUR_AIRTABLE_BASE_ID/YOUR_CONTENT_TABLE_ID)

---

**You're all set! Happy publishing! 🎬**
