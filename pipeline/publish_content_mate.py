#!/usr/bin/env python3
"""
Publish Content Mate Setup content doc tab to the master Content Doc (Series).
Reads content_doc_draft_content_mate.md, classifies each line, creates a new tab,
inserts content, formats it (H1/H3 bold, bullets), and creates an Airtable record.
"""

import pickle, requests, json, re, os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- Config ---
TOKEN_PATH = "youtube_token.pickle"
CONTENT_DOC_ID = "YOUR_CONTENT_DOC_MASTER_ID"
AIRTABLE_BASE = "YOUR_AIRTABLE_BASE_ID"
CONTENT_DOCS_TABLE = "YOUR_CONTENT_DOCS_TABLE_ID"
TAB_TITLE = "Content Mate Setup (Claude Code)"
DRAFT_FILE = "content_doc_draft_content_mate.md"

# --- Load .env ---
AIRTABLE_TOKEN = ""
with open(".env") as f:
    for line in f:
        if line.startswith("AIRTABLE_PERSONAL_ACCESS_TOKEN="):
            AIRTABLE_TOKEN = line.strip().split("=", 1)[1]

# --- Google Auth ---
with open(TOKEN_PATH, "rb") as f:
    creds = pickle.load(f)
if not creds.valid:
    creds.refresh(Request())
    with open(TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)

headers = {
    "Authorization": f"Bearer {creds.token}",
    "Content-Type": "application/json"
}


# --- Parse draft into blocks ---
def classify_line(raw_line):
    """Returns (type, text) or None for empty lines."""
    stripped = raw_line.rstrip('\n').strip()
    if not stripped:
        return None  # skip empty lines

    # H1
    if stripped.startswith("CONTENT DOC"):
        return ("h1", stripped)

    # H3 exact matches
    h3_exact = ["Title:", "Benefits:", "Steps:", "So by the end of this video:"]
    for exact in h3_exact:
        if stripped == exact:
            return ("h3", stripped)

    # H3 emoji section headers (main sections)
    h3_emoji = ["🎯", "🏷️", "🏷", "🖼️", "🖼", "🎤", "📊", "📋", "💎", "🔒", "📎", "🎁"]
    for emoji in h3_emoji:
        if stripped.startswith(emoji):
            return ("h3", stripped)

    # H3 step headers (e.g., "📥 STEP 1 — Grab the Base")
    if re.match(r'.+ STEP \d+', stripped):
        return ("h3", stripped)

    # Plain (no bullet disc)
    if stripped == "Let's get started!":
        return ("plain", stripped)
    if re.match(r'^\d+ —', stripped):
        return ("plain", stripped)

    # Bullet: strip leading "* " if present
    if stripped.startswith("* "):
        return ("bullet", stripped[2:])

    # Default: bullet
    return ("bullet", stripped)


with open(DRAFT_FILE) as f:
    raw_lines = f.readlines()

blocks = []
for raw_line in raw_lines:
    result = classify_line(raw_line)
    if result:
        block_type, text = result
        blocks.append((text + "\n", block_type))

print(f"Parsed {len(blocks)} blocks from draft.")


# ============================================================
# STEP 1: Add a new tab to the Content Doc
# ============================================================
print(f"\nStep 1: Adding tab '{TAB_TITLE}' to Content Doc (Series)...")

add_tab_request = {
    "requests": [{
        "addDocumentTab": {
            "tabProperties": {"title": TAB_TITLE}
        }
    }]
}

resp = requests.post(
    f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
    headers=headers,
    json=add_tab_request
)

if resp.status_code != 200:
    print(f"ERROR adding tab: {resp.status_code}\n{resp.text[:1000]}")
    exit(1)

# Get the new tab ID
tab_id = None
for reply in resp.json().get("replies", []):
    tab_props = reply.get("addDocumentTab", {}).get("tabProperties", {})
    if tab_props.get("tabId"):
        tab_id = tab_props["tabId"]
        break

if not tab_id:
    print("Fetching tab ID from document (fallback)...")
    doc_resp = requests.get(
        f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}?includeTabsContent=true",
        headers={"Authorization": f"Bearer {creds.token}"}
    )
    for tab in doc_resp.json().get("tabs", []):
        tp = tab.get("tabProperties", {})
        if tp.get("title") == TAB_TITLE:
            tab_id = tp.get("tabId", "")
            break

print(f"  Tab ID: {tab_id}")


# ============================================================
# STEP 2: Insert all content
# ============================================================
print("\nStep 2: Inserting content...")
all_text = "".join(text for text, _ in blocks)

insert_resp = requests.post(
    f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
    headers=headers,
    json={"requests": [{
        "insertText": {
            "location": {"index": 1, "tabId": tab_id},
            "text": all_text
        }
    }]}
)
if insert_resp.status_code != 200:
    print(f"ERROR: {insert_resp.status_code}\n{insert_resp.text[:500]}")
    exit(1)
print(f"  Inserted {len(all_text)} chars.")


# ============================================================
# STEP 3: Apply text styles + collect bullet ranges
# ============================================================
print("\nStep 3: Applying text styles...")
style_requests = []
bullet_ranges = []
current_index = 1

for text, block_type in blocks:
    start = current_index
    end = start + len(text)

    if block_type == "h1":
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": tab_id},
                "paragraphStyle": {"alignment": "CENTER"},
                "fields": "alignment"
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": tab_id},
                "textStyle": {"bold": True},
                "fields": "bold"
            }
        })
    elif block_type == "h3":
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": tab_id},
                "textStyle": {"bold": True},
                "fields": "bold"
            }
        })
    elif block_type == "bullet":
        bullet_ranges.append((start, end))

    current_index = end

if style_requests:
    print(f"  Applying {len(style_requests)} style requests...")
    resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": style_requests}
    )
    if resp.status_code != 200:
        print(f"  ERROR: {resp.status_code}\n{resp.text[:500]}")
        exit(1)


# ============================================================
# STEP 4: Apply bullets
# ============================================================
print(f"\nStep 4: Applying bullets to {len(bullet_ranges)} paragraphs...")
bullet_requests = [
    {
        "createParagraphBullets": {
            "range": {"startIndex": s, "endIndex": e, "tabId": tab_id},
            "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
        }
    }
    for s, e in bullet_ranges
]
if bullet_requests:
    resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": bullet_requests}
    )
    if resp.status_code != 200:
        print(f"  ERROR: {resp.status_code}\n{resp.text[:500]}")
        exit(1)
    print("  Done.")


# ============================================================
# STEP 5: Re-read doc, apply H1/H3 heading styles by actual position
# ============================================================
print("\nStep 5: Applying heading styles by actual positions...")

H1_PREFIXES = ["CONTENT DOC"]
H3_EMOJI_PREFIXES = ["🎯", "🏷", "🖼", "🎤", "📊", "📋", "💎", "🔒", "📎", "🎁"]
H3_EXACT_MATCHES = ["Title:", "Benefits:", "Steps:", "So by the end of this video:"]

doc_resp = requests.get(
    f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}?includeTabsContent=true",
    headers={"Authorization": f"Bearer {creds.token}"}
)

heading_requests = []
heading_ranges = []

for tab in doc_resp.json().get("tabs", []):
    if tab.get("tabProperties", {}).get("tabId") == tab_id:
        content = tab.get("documentTab", {}).get("body", {}).get("content", [])
        for elem in content:
            para = elem.get("paragraph", {})
            full_text = "".join(
                pe.get("textRun", {}).get("content", "")
                for pe in para.get("elements", [])
            ).strip()
            if not full_text:
                continue

            start_idx = elem.get("startIndex", 0)
            end_idx = elem.get("endIndex", 0)
            if start_idx >= end_idx:
                continue

            target = None
            for p in H1_PREFIXES:
                if full_text.startswith(p):
                    target = "HEADING_1"
                    break
            if not target:
                for p in H3_EMOJI_PREFIXES:
                    if full_text.startswith(p):
                        target = "HEADING_3"
                        break
            if not target:
                for exact in H3_EXACT_MATCHES:
                    if full_text == exact:
                        target = "HEADING_3"
                        break
            if not target:
                # Step headers: match "STEP N" pattern
                if re.search(r'STEP \d+', full_text):
                    target = "HEADING_3"

            if target:
                heading_requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": start_idx, "endIndex": end_idx, "tabId": tab_id},
                        "paragraphStyle": {"namedStyleType": target},
                        "fields": "namedStyleType"
                    }
                })
                heading_ranges.append({"startIndex": start_idx, "endIndex": end_idx})
        break

if heading_requests:
    print(f"  Applying {len(heading_requests)} heading updates...")
    resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": heading_requests}
    )
    if resp.status_code != 200:
        print(f"  ERROR: {resp.status_code}\n{resp.text[:500]}")
        exit(1)
    print("  Done.")


# ============================================================
# STEP 6: Remove bullets from heading paragraphs
# ============================================================
print(f"\nStep 6: Removing bullets from {len(heading_ranges)} heading paragraphs...")
if heading_ranges:
    delete_bullet_requests = [
        {
            "deleteParagraphBullets": {
                "range": {"startIndex": r["startIndex"], "endIndex": r["endIndex"], "tabId": tab_id}
            }
        }
        for r in heading_ranges
    ]
    resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": delete_bullet_requests}
    )
    if resp.status_code != 200:
        print(f"  ERROR: {resp.status_code}\n{resp.text[:500]}")
        exit(1)
    print("  Done.")


# ============================================================
# STEP 7: Make https:// URLs clickable hyperlinks
# ============================================================
print("\nStep 7: Making URLs clickable...")

doc_resp2 = requests.get(
    f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}?includeTabsContent=true",
    headers={"Authorization": f"Bearer {creds.token}"}
)

url_requests = []
url_pattern = re.compile(r'https?://[^\s\n\]]+')

for tab in doc_resp2.json().get("tabs", []):
    if tab.get("tabProperties", {}).get("tabId") == tab_id:
        content = tab.get("documentTab", {}).get("body", {}).get("content", [])
        for elem in content:
            para = elem.get("paragraph", {})
            para_start = elem.get("startIndex", 0)
            for pe in para.get("elements", []):
                text_run = pe.get("textRun", {})
                run_text = text_run.get("content", "")
                run_start = pe.get("startIndex", 0)
                for match in url_pattern.finditer(run_text):
                    url = match.group(0).rstrip('.,;)')
                    abs_start = run_start + match.start()
                    abs_end = run_start + match.start() + len(url)
                    url_requests.append({
                        "updateTextStyle": {
                            "range": {"startIndex": abs_start, "endIndex": abs_end, "tabId": tab_id},
                            "textStyle": {"link": {"url": url}},
                            "fields": "link"
                        }
                    })
        break

if url_requests:
    print(f"  Making {len(url_requests)} URL(s) clickable...")
    resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": url_requests}
    )
    if resp.status_code != 200:
        print(f"  WARNING: {resp.status_code}\n{resp.text[:300]}")
    else:
        print("  Done.")
else:
    print("  No URLs found.")


# ============================================================
# STEP 8: Create Airtable record
# ============================================================
print("\nStep 8: Creating Airtable record...")

at_resp = requests.post(
    f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{CONTENT_DOCS_TABLE}",
    headers={
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    },
    json={
        "records": [{
            "fields": {
                "Title": TAB_TITLE,
                "Status": "📝 Draft"
            }
        }]
    }
)

if at_resp.status_code in (200, 201):
    record = at_resp.json().get("records", [{}])[0]
    print(f"  Airtable record created: {record.get('id', 'unknown')}")
else:
    print(f"  Airtable: {at_resp.status_code} — {at_resp.text[:300]}")

# Print result IDs for embed step
print(f"\n{'='*60}")
print(f"SUCCESS!")
print(f"Content Doc: https://docs.google.com/document/d/{CONTENT_DOC_ID}/edit")
print(f"Tab: {TAB_TITLE}")
print(f"Tab ID: {tab_id}")
print(f"{'='*60}")
print(f"TAB_ID_FOR_EMBED={tab_id}")
