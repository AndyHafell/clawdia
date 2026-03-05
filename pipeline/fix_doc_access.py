#!/usr/bin/env python3
"""Share the Google Doc with the user's email."""

import os
import pickle
import certifi

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(_PROJECT_ROOT, 'youtube_token.pickle')

DOC_ID = 'YOUR_DOC_ID'
USER_EMAIL = 'YOUR_EMAIL@gmail.com'

with open(TOKEN_FILE, 'rb') as f:
    creds = pickle.load(f)

if creds and creds.expired and creds.refresh_token:
    from google.auth.transport.requests import Request
    creds.refresh(Request())
    with open(TOKEN_FILE, 'wb') as f:
        pickle.dump(creds, f)

from googleapiclient.discovery import build
drive = build('drive', 'v3', credentials=creds)

# Share with user as editor
permission = {
    'type': 'user',
    'role': 'writer',
    'emailAddress': USER_EMAIL
}

result = drive.permissions().create(
    fileId=DOC_ID,
    body=permission,
    sendNotificationEmail=False,
    transferOwnership=False
).execute()

print(f"✅ Shared with {USER_EMAIL} as editor")

# Also try to transfer ownership
try:
    owner_perm = {
        'type': 'user',
        'role': 'owner',
        'emailAddress': USER_EMAIL
    }
    drive.permissions().create(
        fileId=DOC_ID,
        body=owner_perm,
        transferOwnership=True
    ).execute()
    print(f"✅ Ownership transferred to {USER_EMAIL}")
except Exception as e:
    print(f"⚠️  Could not transfer ownership (editor access still works): {e}")
