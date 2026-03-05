#!/usr/bin/env python3
"""
YouTube Publisher - Content Mate (Long-Form)

Publishes videos to YouTube with AI-generated thumbnails and metadata.

Usage:
    python3 youtube_publisher.py --drive-url "https://drive.google.com/..."
    python3 youtube_publisher.py --local-file "/path/to/video.mp4"
    python3 youtube_publisher.py --local-file "..." --title "My Video" --channel "YOUR_CHANNEL_NAME"
"""

import urllib.request
import json
import os
import sys
import re
import subprocess
from datetime import datetime
from pathlib import Path
import pickle

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# YouTube API imports
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    print("⚠️  YouTube API libraries not installed. Install with: pip install google-api-python-client google-auth-oauthlib")

# Project root (one level up from pipeline/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Import from thumbnail system
sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'thumbnail_system'))
from generate_thumbnail import generate_thumbnails

# === Configuration ===
AIRTABLE_TOKEN = os.getenv('AIRTABLE_PERSONAL_ACCESS_TOKEN')
MATE_OS_BASE = 'YOUR_AIRTABLE_BASE_ID'
CONTENT_MATE_TABLE = 'YOUR_CONTENT_TABLE_ID'
GEMINI_API_KEY = os.getenv('Google_AI_Studio')
YOUTUBE_API_KEY = os.getenv('Youtube_data_key')
YOUTUBE_CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')
BLOTATO_API_KEY = os.getenv('BLOTATO_API_KEY')
BLOTATO_ACCOUNT_ID = os.getenv('BLOTATO_ACCOUNT_ID')

# YouTube OAuth2 settings
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/drive.file',  # For creating shareable links
    'https://www.googleapis.com/auth/drive.readonly'  # For finding files in Drive
]
CLIENT_SECRETS_FILE = os.path.join(_PROJECT_ROOT, 'client_secrets.json')
TOKEN_FILE = os.path.join(_PROJECT_ROOT, 'youtube_token.pickle')


def get_youtube_service():
    """Get authenticated YouTube API service using OAuth2."""
    if not YOUTUBE_API_AVAILABLE:
        raise ImportError("YouTube API libraries not installed")

    creds = None

    # Load saved credentials if they exist
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing YouTube credentials...")
            creds.refresh(Request())
        else:
            print("🔐 Starting YouTube OAuth2 authentication...")
            print("  A browser window will open for you to authorize.")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            print("  ✅ Authentication successful!")

        # Save credentials for future use
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build('youtube', 'v3', credentials=creds)


def get_drive_shareable_link(file_path):
    """Get Google Drive shareable link for a file in the synced Google Drive folder.

    Since the Claude Folder is synced with Google Drive, files automatically upload.
    This function searches for the file in Drive and returns a shareable link.

    Args:
        file_path: Local path to the file

    Returns:
        Shareable Google Drive URL, or None if not found
    """
    try:
        # Check if Google Drive API is available
        if not YOUTUBE_API_AVAILABLE:
            print(f"    ⚠️  Google API not available for Drive links")
            return None

        # Get the file name
        filename = os.path.basename(file_path)

        # Use the same OAuth credentials (they include Drive access)
        creds = None
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            print(f"    ⚠️  No valid credentials for Drive API")
            return None

        # Build Drive service
        from googleapiclient.discovery import build
        drive = build('drive', 'v3', credentials=creds)

        # Search for the file in the thumbnail_system folder
        query = f"name='{filename}' and trashed=false"
        results = drive.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, webViewLink)',
            pageSize=10
        ).execute()

        files = results.get('files', [])

        if files:
            file_id = files[0]['id']
            # Make the file publicly accessible
            drive.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()

            # Return direct download link
            download_link = f"https://drive.google.com/uc?export=download&id={file_id}"
            print(f"    ✅ Got Drive link: {filename}")
            return download_link
        else:
            print(f"    ⚠️  File not found in Drive: {filename}")
            return None

    except Exception as e:
        print(f"    ⚠️  Failed to get Drive link: {e}")
        return None


def prepare_airtable_attachments(thumbnail_paths):
    """Prepare thumbnail attachments for Airtable with Google Drive links.

    Args:
        thumbnail_paths: List of local file paths to thumbnails

    Returns:
        Dict with attachment field names and Airtable attachment format values
    """
    attachments = {}
    labels = ['A', 'B', 'C']

    print("\n  📎 Preparing Airtable attachments...")

    for i, path in enumerate(thumbnail_paths[:3]):
        if path and os.path.exists(path):
            label = labels[i]

            # Store file path as text
            attachments[f"Thumbnail {label} Path"] = path

            # Try to get Google Drive shareable link
            drive_url = get_drive_shareable_link(path)

            if drive_url:
                # Airtable attachment format: [{"url": "https://..."}]
                attachments[f"Thumbnail {label}"] = [{"url": drive_url}]
            else:
                # No Drive link available - user will add manually
                print(f"    ℹ️  Thumbnail {label}: Will need manual upload to Airtable")

    return attachments


def compress_thumbnail(thumbnail_path, max_size_bytes=1800000):
    """Compress thumbnail to stay under YouTube's size limit.

    Args:
        thumbnail_path: Path to thumbnail image
        max_size_bytes: Maximum file size in bytes (default 1.8MB to be safe)

    Returns:
        Path to compressed thumbnail (same path, file is modified in place)
    """
    try:
        from PIL import Image
        import io

        # Check current size
        current_size = os.path.getsize(thumbnail_path)
        if current_size <= max_size_bytes:
            return thumbnail_path

        print(f"    Compressing thumbnail ({current_size / (1024*1024):.2f} MB -> target < {max_size_bytes / (1024*1024):.2f} MB)")

        # Load and compress
        img = Image.open(thumbnail_path)

        # Start with quality 85 and reduce if needed
        quality = 85
        while quality > 20:
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True, quality=quality)
            size = buffer.tell()

            if size <= max_size_bytes:
                # Save compressed version
                with open(thumbnail_path, 'wb') as f:
                    f.write(buffer.getvalue())
                print(f"    ✅ Compressed to {size / (1024*1024):.2f} MB (quality: {quality})")
                return thumbnail_path

            quality -= 5

        # If still too large, try JPEG
        buffer = io.BytesIO()
        rgb_img = img.convert('RGB')
        rgb_img.save(buffer, format='JPEG', optimize=True, quality=85)

        # Save as JPEG
        jpeg_path = thumbnail_path.replace('.png', '.jpg')
        with open(jpeg_path, 'wb') as f:
            f.write(buffer.getvalue())

        final_size = os.path.getsize(jpeg_path)
        print(f"    ✅ Converted to JPEG: {final_size / (1024*1024):.2f} MB")
        return jpeg_path

    except Exception as e:
        print(f"    ⚠️  Compression failed: {e}")
        return thumbnail_path


def upload_to_youtube_oauth(video_path, title, description, tags, thumbnail_path=None, privacy_status='unlisted'):
    """Upload video to YouTube using OAuth2.

    Args:
        video_path: Path to local video file
        title: Video title
        description: Video description
        tags: Comma-separated tags or list of tags
        thumbnail_path: Optional path to thumbnail image
        privacy_status: 'private', 'unlisted', or 'public'
    """
    print(f"\n⬆️  Uploading to YouTube with OAuth2...")
    print(f"  Video: {video_path}")
    print(f"  Title: {title}")
    print(f"  Privacy: {privacy_status}")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Get authenticated YouTube service
    youtube = get_youtube_service()

    # Parse tags
    if isinstance(tags, str):
        tag_list = [t.strip() for t in tags.split(',')]
    else:
        tag_list = tags

    # Prepare video metadata
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tag_list,
            'categoryId': '28'  # Science & Technology category
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }

    # Upload the video
    print(f"  📤 Uploading video file ({os.path.getsize(video_path) / (1024*1024):.1f} MB)...")
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/*')

    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"    Uploaded {int(status.progress() * 100)}%")

    video_id = response['id']
    video_url = f"https://youtube.com/watch?v={video_id}"

    print(f"  ✅ Video uploaded successfully!")
    print(f"  📺 Video ID: {video_id}")
    print(f"  🔗 URL: {video_url}")

    # Upload thumbnail if provided
    if thumbnail_path and os.path.exists(thumbnail_path):
        print(f"  🖼️  Uploading thumbnail: {thumbnail_path}")

        # Compress if needed
        thumbnail_path = compress_thumbnail(thumbnail_path)

        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
        print(f"  ✅ Thumbnail uploaded!")

    return {
        'video_id': video_id,
        'url': video_url,
        'status': privacy_status
    }


def airtable_create(fields):
    """Create a record in Content Mate (Long-Form) table."""
    url = f"https://api.airtable.com/v0/{MATE_OS_BASE}/{CONTENT_MATE_TABLE}"
    payload = json.dumps({"records": [{"fields": fields}]}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def airtable_update(record_id, fields):
    """Update a record in Content Mate table."""
    url = f"https://api.airtable.com/v0/{MATE_OS_BASE}/{CONTENT_MATE_TABLE}/{record_id}"
    payload = json.dumps({"fields": fields}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    }, method='PATCH')
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_drive_id(drive_url):
    """Extract file ID from Google Drive URL."""
    patterns = [
        r'id=([a-zA-Z0-9_-]+)',
        r'/d/([a-zA-Z0-9_-]+)',
        r'/file/d/([a-zA-Z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, drive_url)
        if match:
            return match.group(1)
    return None


def generate_metadata(video_info=None):
    """Generate YouTube title and description using Gemini."""
    print("\n🤖 Generating video metadata with AI...")

    try:
        # Simple prompt for now - can be enhanced later
        prompt = """Generate a compelling YouTube video title and description for a video about AI automation and AI Mates.

The channel is "YOUR_CHANNEL_NAME" which teaches people how to build AI automation systems.

Provide a response in this EXACT format:
TITLE: [Your title here - max 70 characters, engaging and clickable]
DESCRIPTION: [Your description here - 2-3 paragraphs explaining what viewers will learn]
TAGS: [Comma-separated tags related to AI, automation, productivity]"""

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        # Parse response
        text = result['candidates'][0]['content']['parts'][0]['text']

        title_match = re.search(r'TITLE:\s*(.+?)(?:\n|$)', text)
        desc_match = re.search(r'DESCRIPTION:\s*(.+?)(?=TAGS:|$)', text, re.DOTALL)
        tags_match = re.search(r'TAGS:\s*(.+?)$', text, re.DOTALL)

        title = title_match.group(1).strip() if title_match else "AI Automation Tutorial"
        description = desc_match.group(1).strip() if desc_match else "Learn about AI automation."
        tags = tags_match.group(1).strip() if tags_match else "AI, automation, productivity"

        print(f"  ✅ Title: {title}")
        print(f"  ✅ Description: {description[:100]}...")
        print(f"  ✅ Tags: {tags}")

        return {
            "title": title,
            "description": description,
            "tags": tags
        }
    except Exception as e:
        print(f"  ⚠️  Gemini API error: {e}")
        print(f"  📝 Using default metadata instead")

        # Fallback to default metadata
        default_title = f"AI Automation Livestream - {datetime.now().strftime('%B %Y')}"
        default_desc = """Welcome to YOUR_CHANNEL_NAME!

In this livestream, we explore cutting-edge AI automation techniques and show you how to build powerful AI systems.

Join our community and learn how to leverage AI to supercharge your productivity!"""
        default_tags = "AI, automation, productivity, AI agents, AI Mates, livestream, tutorial"

        print(f"  ✅ Title: {default_title}")
        print(f"  ✅ Description: {default_desc[:100]}...")
        print(f"  ✅ Tags: {default_tags}")

        return {
            "title": default_title,
            "description": default_desc,
            "tags": default_tags
        }


def download_from_drive(file_id, output_path):
    """Download video from Google Drive."""
    print(f"\n📥 Downloading video from Google Drive...")
    print(f"  File ID: {file_id}")

    # Use gdown for Google Drive downloads (install with: pip install gdown)
    try:
        import gdown
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, output_path, quiet=False)
        print(f"  ✅ Downloaded to: {output_path}")
        return output_path
    except ImportError:
        print("  ⚠️  gdown not installed. Install with: pip install gdown")
        print("  Using direct download URL instead...")

        # Fallback: use curl/wget
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        subprocess.run(['curl', '-L', download_url, '-o', output_path], check=True)
        print(f"  ✅ Downloaded to: {output_path}")
        return output_path


def upload_to_youtube_via_blotato(video_url, title, description, tags, thumbnail_path=None, scheduled_time=None):
    """Upload video to YouTube using Blotato API.

    Args:
        video_url: Public URL to the video (Google Drive, etc.)
        title: Video title
        description: Video description
        tags: Comma-separated tags
        thumbnail_path: Optional path to custom thumbnail (local file path)
        scheduled_time: Optional ISO 8601 timestamp for scheduled publishing
    """
    print(f"\n⬆️  Uploading to YouTube via Blotato...")
    print(f"  Video URL: {video_url}")
    print(f"  Title: {title}")
    print(f"  Account ID: {BLOTATO_ACCOUNT_ID}")

    if not BLOTATO_API_KEY or not BLOTATO_ACCOUNT_ID:
        print("  ❌ Missing Blotato API key or Account ID")
        return None

    # Prepare the request payload (wrap in "post" object as required by API)
    post_data = {
        "accountId": int(BLOTATO_ACCOUNT_ID),
        "content": {
            "platform": "youtube",  # Required field
            "text": f"{title}\n\n{description}",
            "mediaUrls": [video_url]  # Blotato can handle public URLs directly
        },
        "target": {
            "targetType": "VIDEO"  # Try VIDEO for YouTube uploads
        }
    }

    # Add scheduled time if provided
    if scheduled_time:
        post_data["scheduledTime"] = scheduled_time
        print(f"  📅 Scheduled for: {scheduled_time}")

    # Wrap in "post" object as required by Blotato API
    payload = {"post": post_data}

    # Convert to JSON
    data = json.dumps(payload).encode("utf-8")

    # Make the API request
    url = "https://backend.blotato.com/v2/posts"
    req = urllib.request.Request(url, data=data, headers={
        "blotato-api-key": BLOTATO_API_KEY,
        "Content-Type": "application/json"
    })

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"  ✅ Uploaded successfully!")
            print(f"  Response: {json.dumps(result, indent=2)}")

            return {
                "post_id": result.get("id"),
                "status": result.get("status"),
                "blotato_response": result
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"  ❌ Blotato API Error ({e.code}): {error_body}")
        raise
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        raise


def upload_to_youtube(video_path, title, description, tags, thumbnail_path=None):
    """Wrapper function - currently redirects to Blotato upload.

    NOTE: For direct YouTube API upload, OAuth2 setup would be required.
    Currently using Blotato as the upload method.
    """
    # If video_path is a local file, we need to convert it to a public URL
    # For now, assume video_path is already a public URL (Google Drive, etc.)
    if os.path.exists(video_path):
        print(f"  ⚠️  Local file detected: {video_path}")
        print(f"  ⚠️  Blotato requires a public URL - please upload to Google Drive first")
        return {
            "video_id": "ERROR_LOCAL_FILE",
            "url": None,
            "error": "Blotato requires public URL, not local file"
        }

    # Treat video_path as a public URL
    return upload_to_youtube_via_blotato(video_path, title, description, tags, thumbnail_path)


def publish_video(drive_url=None, local_file=None, title=None, channel="YOUR_CHANNEL_NAME", description=None, split_test=False):
    """Main publishing workflow.

    Args:
        split_test: If True, uploads 3 versions with different thumbnails (A, B, C)
    """
    print("="*60)
    print("📹 YouTube Publisher - Content Mate (Long-Form)")
    if split_test:
        print("🧪 A/B/C Split Testing Mode - Will upload 3 versions")
    print("="*60)

    # Validate inputs
    if not drive_url and not local_file:
        print("❌ Must provide either --drive-url or --local-file")
        return None

    # Determine video source
    if local_file:
        video_source = local_file
        source_type = "Local File"
        print(f"\n📁 Using local file: {local_file}")
        if not os.path.exists(local_file):
            print(f"❌ File not found: {local_file}")
            return None
    else:
        file_id = extract_drive_id(drive_url)
        if not file_id:
            print(f"❌ Could not extract file ID from URL: {drive_url}")
            return None
        video_source = drive_url
        source_type = "Google Drive"

    # Create Airtable record
    print("\n📝 Creating Airtable record...")
    record = airtable_create({
        "📹 Video Title": title or "Processing...",
        "Google Drive Path": video_source,
        "Channel": channel,
        "Status": "📝 Draft"
    })
    record_id = record['records'][0]['id']
    print(f"  ✅ Record created: {record_id}")

    try:
        # Generate metadata if not provided
        if not title or not description:
            metadata = generate_metadata()
            title = title or metadata['title']
            description = description or metadata['description']
            tags = metadata['tags']
        else:
            tags = "AI, automation, productivity"

        # Update Airtable with metadata
        airtable_update(record_id, {
            "📹 Video Title": title,
            "Description": description,
            "Tags": tags
        })

        # Generate thumbnails
        airtable_update(record_id, {"Status": "🎨 Generating Thumbnail"})
        print(f"\n🎨 Generating thumbnails for: {title}")
        options, session_dir = generate_thumbnails(title)  # Uses default model from config

        if not options:
            print("  ⚠️  No thumbnails generated, proceeding without thumbnail")
            options = [{'path': None, 'name': 'None'}]

        # Download video if from Google Drive
        video_path = local_file
        if not local_file:
            print(f"\n📥 Downloading from Google Drive...")
            file_id = extract_drive_id(drive_url)
            video_filename = f"video_{file_id}.mp4"
            video_path = os.path.join("/tmp", video_filename)
            download_from_drive(file_id, video_path)

        # Upload to YouTube
        airtable_update(record_id, {"Status": "⬆️ Uploading"})

        results = []

        if split_test and len(options) >= 3:
            # A/B/C Split Testing - Upload 3 versions with different thumbnails
            print(f"\n🧪 Uploading 3 versions for A/B/C split testing...")

            option_labels = ['A', 'B', 'C']
            for i, (option, label) in enumerate(zip(options[:3], option_labels)):
                print(f"\n{'='*60}")
                print(f"📤 Uploading Version {label} (Thumbnail Option {label})")
                print(f"{'='*60}")

                variant_title = f"[Test {label}] {title}"
                variant_desc = f"{description}\n\n[This is thumbnail test variant {label}]"

                result = upload_to_youtube_oauth(
                    video_path,
                    variant_title,
                    variant_desc,
                    tags,
                    thumbnail_path=option['path'],
                    privacy_status='private'  # Private for testing
                )

                result['variant'] = label
                result['thumbnail'] = option['path']
                results.append(result)

                print(f"  ✅ Version {label} uploaded: {result['url']}")

            # Update Airtable with all video IDs
            video_ids = ' | '.join([f"{r['variant']}: {r['video_id']}" for r in results])
            airtable_update(record_id, {
                "Status": "🎉 Published",
                "YouTube Video ID": video_ids,
                "Published Date": datetime.now().isoformat(),
                "Thumbnail Path": f"3 variants: {session_dir}"
            })

            print("\n" + "="*60)
            print("✅ SUCCESS! 3 versions uploaded for split testing")
            print("   All videos are PRIVATE - they won't appear on your channel")
            for r in results:
                print(f"   [{r['variant']}] {r['url']}")
            print(f"   Airtable: https://airtable.com/{MATE_OS_BASE}/{CONTENT_MATE_TABLE}/{record_id}")
            print("="*60)

        else:
            # Standard upload - single version with Option A thumbnail
            thumbnail_path = options[0]['path'] if options else None
            if thumbnail_path:
                print(f"  ✅ Selected thumbnail: {thumbnail_path}")

            result = upload_to_youtube_oauth(
                video_path,
                title,
                description,
                tags,
                thumbnail_path=thumbnail_path,
                privacy_status='private'  # Private to avoid accidental publishing
            )

            results = [result]

            # Update Airtable with success and store all 3 thumbnail paths
            update_fields = {
                "Status": "🎉 Published",
                "YouTube Video ID": result.get('video_id', 'UNKNOWN'),
                "Published Date": datetime.now().isoformat()
            }

            # Store paths to all 3 thumbnail options for manual Test & Compare
            if len(options) >= 3:
                # Get thumbnail paths
                thumbnail_paths = [
                    options[0]['path'] if options[0]['path'] else None,
                    options[1]['path'] if options[1]['path'] else None,
                    options[2]['path'] if options[2]['path'] else None
                ]

                # Prepare attachments with Google Drive links
                attachment_fields = prepare_airtable_attachments(thumbnail_paths)

                # Merge with update fields
                update_fields.update(attachment_fields)
                update_fields["Thumbnail Folder"] = session_dir

                print(f"\n  📁 Thumbnail files saved to: {session_dir}")
                print(f"     Option A: {options[0]['path']}")
                print(f"     Option B: {options[1]['path']}")
                print(f"     Option C: {options[2]['path']}")
                print(f"\n  💡 To use YouTube's Test & Compare feature:")
                print(f"     1. Go to YouTube Studio")
                print(f"     2. Find your video: {result['url']}")
                print(f"     3. Click 'Test & Compare' in the thumbnails section")
                print(f"     4. Upload the 3 thumbnail files from the paths above")
                print(f"     OR download directly from Airtable attachment fields!")

            airtable_update(record_id, update_fields)

            print("\n" + "="*60)
            print("✅ SUCCESS! Video uploaded")
            print(f"   Video is PRIVATE - it won't appear on your channel")
            print(f"   YouTube URL: {result['url']}")
            print(f"   Airtable: https://airtable.com/{MATE_OS_BASE}/{CONTENT_MATE_TABLE}/{record_id}")
            print("="*60)

        return results

    except Exception as e:
        print(f"\n❌ Error: {e}")
        airtable_update(record_id, {"Status": "❌ Error"})
        raise


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Publish videos to YouTube")
    parser.add_argument("--drive-url", help="Google Drive video URL")
    parser.add_argument("--local-file", help="Local video file path")
    parser.add_argument("--title", help="Video title (auto-generated if not provided)")
    parser.add_argument("--description", help="Video description (auto-generated if not provided)")
    parser.add_argument("--channel", default="YOUR_CHANNEL_NAME", help="YouTube channel name")
    parser.add_argument("--split-test", action="store_true", help="Upload 3 versions for A/B/C thumbnail split testing")
    args = parser.parse_args()

    publish_video(
        drive_url=args.drive_url,
        local_file=args.local_file,
        title=args.title,
        channel=args.channel,
        description=args.description,
        split_test=args.split_test
    )


if __name__ == "__main__":
    main()
