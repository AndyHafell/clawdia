#!/usr/bin/env python3
"""
Score the 11 locally-generated thumbnails, select top 3 with system diversity,
upload to Google Drive, and embed in the Content Mate content doc tab.
"""
import sys, os, pickle, requests, base64, json

# Add thumbnail_system to path
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "thumbnail_system"))

# Auto SSL
import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

from thumbnail_service import score_thumbnails, select_top_3

# --- Config ---
TOKEN_PATH = "youtube_token.pickle"
CONTENT_DOC_ID = "YOUR_CONTENT_DOC_MASTER_ID"
TAB_ID = "YOUR_TAB_ID"
DRIVE_FOLDER_ID = "YOUR_SHARED_DRIVE_FOLDER_ID"
TITLE = "Claude Code + n8n + Airtable makes insane AI Clone Videos (NEW Skill)"

OUTPUT_BASE = "thumbnail_system/output/20260305_121747_Claude Code  n8n  Airtable makes insane AI Clone V"

thumbnails = [
    {"label": "S3_A", "system": 3, "file_path": f"{OUTPUT_BASE}/system3_ai_face/S3_A.png"},
    {"label": "S3_B", "system": 3, "file_path": f"{OUTPUT_BASE}/system3_ai_face/S3_B.png"},
    {"label": "S3_C", "system": 3, "file_path": f"{OUTPUT_BASE}/system3_ai_face/S3_C.png"},
    {"label": "S4_A", "system": 4, "file_path": f"{OUTPUT_BASE}/system4_no_face/S4_A.png"},
    {"label": "S4_B", "system": 4, "file_path": f"{OUTPUT_BASE}/system4_no_face/S4_B.png"},
    {"label": "S4_C", "system": 4, "file_path": f"{OUTPUT_BASE}/system4_no_face/S4_C.png"},
    {"label": "S5_A", "system": 5, "file_path": f"{OUTPUT_BASE}/system5_trigger/S5_A.png"},
    {"label": "S5_B", "system": 5, "file_path": f"{OUTPUT_BASE}/system5_trigger/S5_B.png"},
    {"label": "S5_D", "system": 5, "file_path": f"{OUTPUT_BASE}/system5_trigger/S5_D.png"},
    {"label": "S5_E", "system": 5, "file_path": f"{OUTPUT_BASE}/system5_trigger/S5_E.png"},
    {"label": "S5_F", "system": 5, "file_path": f"{OUTPUT_BASE}/system5_trigger/S5_F.png"},
]

concepts = [
    "[Creator]'s face duplicated side-by-side (cloned), text overlay AI CLONE CONTENT in bright yellow gradient, shocked excited expression, dark background with subtle blue tint",
    "Claude Code terminal open on screen, [Creator]'s face in corner with 5 VIDEOS PER DAY text in yellow, look what I built energy, techy but approachable"
]

# --- Google Auth ---
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

with open(TOKEN_PATH, "rb") as f:
    creds = pickle.load(f)
if not creds.valid:
    creds.refresh(Request())
    with open(TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)

drive = build("drive", "v3", credentials=creds)
doc_headers = {
    "Authorization": f"Bearer {creds.token}",
    "Content-Type": "application/json"
}

# ============================================================
# STEP 1: Score thumbnails
# ============================================================
print(f"Scoring {len(thumbnails)} thumbnails...")
scored = score_thumbnails(thumbnails, TITLE, concepts)

# Print all scores
print("\nAll scores:")
for s in sorted(scored, key=lambda x: x.score, reverse=True):
    print(f"  [{s.label}] {s.score}/10 — {s.reasoning[:60]}")

# ============================================================
# STEP 2: Select top 3 with system diversity
# ============================================================
top3 = select_top_3(scored)

print(f"\nTop 3 selected:")
for s in top3:
    print(f"  [{s.label}] {s.score}/10 — system: {s.system}")

# ============================================================
# STEP 3: Upload top 3 to Google Drive
# ============================================================
print("\nUploading top 3 to Google Drive...")
for s in top3:
    meta = {
        "name": f"content_mate_thumb_{s.label}.png",
        "parents": [DRIVE_FOLDER_ID]
    }
    media = MediaFileUpload(s.file_path, mimetype="image/png")
    uploaded = drive.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()
    file_id = uploaded["id"]
    drive.permissions().create(fileId=file_id, body={"role": "reader", "type": "anyone"}).execute()
    s.drive_url = f"https://lh3.googleusercontent.com/d/{file_id}"
    print(f"  Uploaded {s.label}: {file_id}")

# ============================================================
# STEP 4: Find THUMBNAIL IDEAS section end index in the doc
# ============================================================
print("\nLocating THUMBNAIL IDEAS section in doc...")
doc_resp = requests.get(
    f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}?includeTabsContent=true",
    headers={"Authorization": f"Bearer {creds.token}"}
)

insert_index = None
thumbnail_section_found = False
for tab in doc_resp.json().get("tabs", []):
    if tab.get("tabProperties", {}).get("tabId") == TAB_ID:
        content = tab.get("documentTab", {}).get("body", {}).get("content", [])
        for i, elem in enumerate(content):
            para = elem.get("paragraph", {})
            full_text = "".join(
                pe.get("textRun", {}).get("content", "")
                for pe in para.get("elements", [])
            ).strip()

            if "THUMBNAIL IDEAS" in full_text:
                thumbnail_section_found = True
                continue

            if thumbnail_section_found and full_text.startswith("🎤"):
                # Found the next section after thumbnail ideas
                insert_index = elem.get("startIndex", None)
                break
        break

print(f"  Thumbnail section found: {thumbnail_section_found}, insert before index: {insert_index}")

# ============================================================
# STEP 5: Embed thumbnails in reverse order at insert_index
# ============================================================
if insert_index:
    print("\nEmbedding thumbnails...")

    # Insert in reverse order so they appear in correct visual order
    for s in reversed(top3):
        img_url = s.drive_url
        score_text = f"Must-Click Score: {s.score}/10 — {s.reasoning[:80]}"

        batch = [
            # Separator newline before image
            {"insertText": {
                "location": {"index": insert_index, "tabId": TAB_ID},
                "text": "\n"
            }},
            # Image
            {"insertInlineImage": {
                "location": {"index": insert_index, "tabId": TAB_ID},
                "uri": img_url,
                "objectSize": {
                    "height": {"magnitude": 200, "unit": "PT"},
                    "width": {"magnitude": 356, "unit": "PT"}
                }
            }},
            # Newline after image
            {"insertText": {
                "location": {"index": insert_index, "tabId": TAB_ID},
                "text": "\n"
            }},
            # Score text
            {"insertText": {
                "location": {"index": insert_index, "tabId": TAB_ID},
                "text": score_text + "\n"
            }},
        ]

        resp = requests.post(
            f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
            headers=doc_headers,
            json={"requests": batch}
        )
        if resp.status_code == 200:
            print(f"  Embedded {s.label} ({s.score}/10)")
        else:
            print(f"  ERROR embedding {s.label}: {resp.status_code} {resp.text[:200]}")

print(f"\n{'='*60}")
print("DONE!")
print(f"View doc: https://docs.google.com/document/d/{CONTENT_DOC_ID}/edit")
print(f"{'='*60}")
