#!/usr/bin/env python3
"""Update the existing Google Doc with new content."""

import os
import pickle
import certifi

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(_PROJECT_ROOT, 'youtube_token.pickle')
DOC_ID = 'YOUR_DOC_ID'

# Load creds
with open(TOKEN_FILE, 'rb') as f:
    creds = pickle.load(f)

if creds and creds.expired and creds.refresh_token:
    from google.auth.transport.requests import Request
    creds.refresh(Request())
    with open(TOKEN_FILE, 'wb') as f:
        pickle.dump(creds, f)

from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

# Read the updated markdown
content_doc_path = os.path.join(SCRIPT_DIR, 'content doc', 'Why I Changed From N8N to Claude Code.md')
with open(content_doc_path, 'r') as f:
    md_content = f.read()

# Convert to HTML
lines = md_content.strip().split('\n')
html_parts = ['<html><body style="font-family: Arial, sans-serif;">']

for line in lines:
    stripped = line.strip()

    if stripped.startswith('━'):
        html_parts.append('<hr style="border: 2px solid #333;">')
        continue
    if not stripped:
        html_parts.append('<br>')
        continue

    # Section headers
    section_headers = ['ONE-LINER', 'TITLES (pick 1 before filming)', 'THUMBNAIL IDEAS',
                       'SAY THIS (word-for-word intro — read this aloud):',
                       '4P FRAMEWORK', 'OUTLINE (talk through these in order)',
                       'BENEFITS (what the viewer gets)', 'WHY STAY TO THE END',
                       'SOURCES / LINKS']

    is_header = False
    for h in section_headers:
        if stripped == h or stripped.startswith(h):
            # Map emoji prefixes
            emoji_map = {
                'ONE-LINER': '🎯', 'TITLES': '🏷️', 'THUMBNAIL': '🖼️',
                'SAY THIS': '🎤', '4P FRAME': '📊', 'OUTLINE': '📋',
                'BENEFITS': '💎', 'WHY STAY': '🔒', 'SOURCES': '📎'
            }
            emoji = ''
            for key, val in emoji_map.items():
                if stripped.startswith(key):
                    emoji = val + ' '
                    break
            html_parts.append(f'<h2 style="color: #1a73e8; margin-top: 24px; font-size: 16px;">{emoji}{stripped}</h2>')
            is_header = True
            break
    if is_header:
        continue

    # Title line
    if stripped.startswith('CONTENT DOC'):
        html_parts.append(f'<h1 style="color: #202124; font-size: 22px; text-align: center;">{stripped}</h1>')
        continue

    # SAY THIS quoted text
    if stripped.startswith('"') and stripped.endswith('"'):
        html_parts.append(f'<blockquote style="border-left: 4px solid #1a73e8; padding-left: 16px; margin: 12px 0; font-style: italic; font-size: 15px; color: #333;">{stripped}</blockquote>')
        continue

    # 4P Framework lines
    if stripped.startswith('Proof:') or stripped.startswith('Promise:') or stripped.startswith('Problem:') or stripped.startswith('Path:'):
        label = stripped.split(':')[0]
        rest = stripped[len(label)+1:].strip()
        html_parts.append(f'<p style="margin-left: 20px;"><strong>{label}:</strong> {rest}</p>')
        continue

    # Concept lines
    if stripped.startswith('* Concept'):
        parts = stripped[2:].split(' — ', 1)
        if len(parts) == 2:
            html_parts.append(f'<p style="margin-left: 20px;">• <strong>{parts[0]}</strong> — {parts[1]}</p>')
        else:
            html_parts.append(f'<p style="margin-left: 20px;">• {stripped[2:]}</p>')
        continue

    # Numbered list
    if stripped and stripped[0].isdigit() and '. ' in stripped:
        html_parts.append(f'<p style="margin-left: 20px;">{stripped}</p>')
        continue

    # Bullet points (titles with *)
    if stripped.startswith('* '):
        html_parts.append(f'<p style="margin-left: 20px;">• {stripped[2:]}</p>')
        continue

    # Bullet points with -
    if stripped.startswith('- '):
        content = stripped[2:]
        if 'http' in content:
            parts = content.split(' — ', 1)
            if len(parts) == 2 and parts[0].startswith('http'):
                content = f'<a href="{parts[0]}">{parts[0]}</a> — {parts[1]}'
        html_parts.append(f'<p style="margin-left: 20px;">• {content}</p>')
        continue

    html_parts.append(f'<p>{stripped}</p>')

html_parts.append('</body></html>')
html_content = '\n'.join(html_parts)

# Update the doc by replacing its content via Drive API
drive = build('drive', 'v3', credentials=creds)

media = MediaInMemoryUpload(
    html_content.encode('utf-8'),
    mimetype='text/html',
    resumable=False
)

drive.files().update(
    fileId=DOC_ID,
    media_body=media
).execute()

print(f"✅ Google Doc updated!")
print(f"   URL: https://docs.google.com/document/d/{DOC_ID}/edit")
