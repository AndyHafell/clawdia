#!/usr/bin/env python3
"""
Create a Google Doc from a content doc markdown file and set up Airtable tracking.
"""

import os
import sys
import json
import pickle
import urllib.request
from dotenv import load_dotenv

load_dotenv()

# Paths (project root is one level up from pipeline/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(_PROJECT_ROOT, 'youtube_token.pickle')

# Airtable config
AIRTABLE_TOKEN = os.getenv('AIRTABLE_PERSONAL_ACCESS_TOKEN')
MATE_OS_BASE = 'YOUR_AIRTABLE_BASE_ID'

# ============================================================
# PART 1: Create Google Doc
# ============================================================

def create_google_doc(title, html_content):
    """Create a Google Doc using Drive API with HTML import."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaInMemoryUpload

    # Load OAuth creds
    if not os.path.exists(TOKEN_FILE):
        print("❌ No youtube_token.pickle found. Run youtube_publisher.py first to authenticate.")
        sys.exit(1)

    with open(TOKEN_FILE, 'rb') as f:
        creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            with open(TOKEN_FILE, 'wb') as f:
                pickle.dump(creds, f)
        else:
            print("❌ Credentials expired. Delete youtube_token.pickle and re-auth.")
            sys.exit(1)

    drive = build('drive', 'v3', credentials=creds)

    # Upload HTML as Google Doc
    media = MediaInMemoryUpload(
        html_content.encode('utf-8'),
        mimetype='text/html',
        resumable=False
    )

    file_metadata = {
        'name': title,
        'mimeType': 'application/vnd.google-apps.document'
    }

    doc = drive.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    doc_url = doc.get('webViewLink', f"https://docs.google.com/document/d/{doc['id']}/edit")
    print(f"✅ Google Doc created: {title}")
    print(f"   URL: {doc_url}")

    # Share with user's email
    USER_EMAIL = 'YOUR_EMAIL@gmail.com'
    try:
        drive.permissions().create(
            fileId=doc['id'],
            body={'type': 'user', 'role': 'writer', 'emailAddress': USER_EMAIL},
            sendNotificationEmail=False
        ).execute()
        print(f"   Shared with {USER_EMAIL}")
    except Exception as e:
        print(f"   ⚠️  Could not share: {e}")

    return doc['id'], doc_url


def markdown_to_html(md_content):
    """Convert the content doc markdown to styled HTML for Google Docs."""
    lines = md_content.strip().split('\n')
    html_parts = ['<html><body style="font-family: Arial, sans-serif;">']

    for line in lines:
        stripped = line.strip()

        # Skip separator lines
        if stripped.startswith('━'):
            html_parts.append('<hr>')
            continue

        # Empty lines
        if not stripped:
            html_parts.append('<br>')
            continue

        # Section headers (all caps, no prefix)
        if stripped in ['ONE-LINER', 'OUTLINE', 'BENEFITS', 'WHY STAY TO THE END', 'SOURCES / LINKS']:
            html_parts.append(f'<h2 style="color: #1a73e8; margin-top: 24px;">{stripped}</h2>')
            continue

        # Title line (CONTENT DOC —)
        if stripped.startswith('CONTENT DOC'):
            html_parts.append(f'<h1 style="color: #202124; font-size: 24px;">{stripped}</h1>')
            continue

        # Numbered list items
        if stripped and stripped[0].isdigit() and '. ' in stripped:
            html_parts.append(f'<p style="margin-left: 20px;">{stripped}</p>')
            continue

        # Bullet points
        if stripped.startswith('- '):
            content = stripped[2:]
            # Make URLs clickable
            if 'http' in content:
                parts = content.split(' — ', 1)
                if len(parts) == 2 and parts[0].startswith('http'):
                    content = f'<a href="{parts[0]}">{parts[0]}</a> — {parts[1]}'
            html_parts.append(f'<p style="margin-left: 20px;">• {content}</p>')
            continue

        # Regular text
        html_parts.append(f'<p>{stripped}</p>')

    html_parts.append('</body></html>')
    return '\n'.join(html_parts)


# ============================================================
# PART 2: Create Airtable table + first record
# ============================================================

def airtable_request(method, url, data=None):
    """Make an Airtable API request."""
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            'Authorization': f'Bearer {AIRTABLE_TOKEN}',
            'Content-Type': 'application/json'
        }
    )
    if data:
        req.data = json.dumps(data).encode('utf-8')

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f"❌ Airtable API error ({e.code}): {body}")
        return None


def create_content_docs_table():
    """Create the Content Docs table in Mate OS base."""
    url = f'https://api.airtable.com/v0/meta/bases/{MATE_OS_BASE}/tables'

    data = {
        "name": "Content Docs",
        "fields": [
            {
                "name": "Title",
                "type": "singleLineText"
            },
            {
                "name": "Status",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "📝 Draft", "color": "yellowLight2"},
                        {"name": "✅ Ready", "color": "greenLight2"},
                        {"name": "🎬 Filmed", "color": "blueLight2"},
                        {"name": "🎉 Published", "color": "purpleLight2"}
                    ]
                }
            },
            {
                "name": "Google Doc Link",
                "type": "url"
            }
        ]
    }

    result = airtable_request('POST', url, data)
    if result:
        table_id = result.get('id')
        print(f"✅ Airtable table 'Content Docs' created: {table_id}")
        return table_id
    return None


def add_content_doc_record(table_id, title, status, doc_url):
    """Add a record to the Content Docs table."""
    url = f'https://api.airtable.com/v0/{MATE_OS_BASE}/{table_id}'

    data = {
        "records": [
            {
                "fields": {
                    "Title": title,
                    "Status": status,
                    "Google Doc Link": doc_url
                }
            }
        ]
    }

    result = airtable_request('POST', url, data)
    if result:
        record_id = result['records'][0]['id']
        print(f"✅ Record created: {title} ({record_id})")
        return record_id
    return None


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    # Set SSL certs
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

    # Read the content doc
    content_doc_path = os.path.join(SCRIPT_DIR, 'content doc', 'Why I Changed From N8N to Claude Code.md')
    with open(content_doc_path, 'r') as f:
        md_content = f.read()

    title = "Why I Changed From N8N to Claude Code"

    # Step 1: Create Google Doc
    print("\n📄 Creating Google Doc...")
    html_content = markdown_to_html(md_content)
    doc_id, doc_url = create_google_doc(title, html_content)

    # Step 2: Create Airtable table
    print("\n📊 Creating Airtable table...")
    table_id = create_content_docs_table()

    # Step 3: Add first record
    if table_id:
        print("\n📝 Adding first record...")
        add_content_doc_record(table_id, title, "📝 Draft", doc_url)

    print("\n✅ Done!")
    print(f"   Google Doc: {doc_url}")
    if table_id:
        print(f"   Airtable table ID: {table_id}")
