#!/usr/bin/env python3
"""
Add a new content doc as a tab in the Content Doc (Series) master Google Doc.
"""

import pickle, json, requests, os

# --- Config ---
TOKEN_PATH = "youtube_token.pickle"
CONTENT_DOC_ID = "YOUR_CONTENT_DOC_MASTER_ID"
AIRTABLE_BASE = "YOUR_AIRTABLE_BASE_ID"
CONTENT_DOCS_TABLE = "YOUR_CONTENT_DOCS_TABLE_ID"

TAB_TITLE = "Upgrading My Daily AI Show Doc"

CONTENT = """CONTENT DOC — UPGRADING MY DAILY AI SHOW DOC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 ONE-LINER
I'm upgrading the AI agent that writes my daily show doc so I can film 3 videos a day without thinking about what to say.

🏷️ TITLES (pick 1 before filming)
* I Built an AI Agent That Writes My Videos For Me
* How I Film 3 Videos a Day Without a Script
* My AI Agents Do All the Work (I Just Read & Film)
* The $100K System: AI Writes My Show, I Hit Record
* I Automated the Hardest Part of YouTube

🖼️ THUMBNAIL IDEAS
* Concept A — Split screen: left side = messy wall of text/chaos, right side = clean formatted show doc on screen. [Creator] pointing at the doc with a surprised expression. Text overlay: "IT WRITES ITSELF"
* Concept B — [Creator] sitting at desk with arms behind head looking relaxed, laptop open showing the show doc. Multiple video thumbnails floating around him. Text overlay: "3 VIDEOS/DAY"

🎤 SAY THIS (word-for-word intro — read this aloud):
"My AI agents make it so easy to film three videos a day — because every morning, there's a show doc waiting for me. No hunting for ideas, no writing bullet points from scratch, no staring at a blank page. I just wake up, read the document, film, and my work is done. I make six figures a year doing this, and today I'm going to show you exactly how this system works by upgrading it live — fixing the problems as they come."

📊 4P FRAMEWORK (inspiration for the intro — not spoken on camera)
Proof: I film 3 videos per day using an AI-generated show doc and make six figures a year from it.
Promise: You'll see exactly how the daily show doc system works and how I'm upgrading it to run fully automatically every single day.
Problem: Without a system like this, you're spending hours researching, outlining, and prepping — which means you either burn out or don't post enough.
Path: Start with proof that the system works, then walk through the live upgrade process — fixing problems as they appear, not starting from scratch.

📋 OUTLINE (talk through these in order)
1. Show the current show doc system working
2. Explain what it does each morning automatically
3. Reveal the problems that need fixing
4. Walk through each upgrade live on screen
5. Fix issues as they come up in real time
6. Show the finished upgraded pipeline running
7. Results: what the daily output looks like now

💎 BENEFITS (what the viewer gets)
• See a real six-figure AI automation system in action, not a hypothetical
• Learn how to build a daily content pipeline that removes the blank-page problem
• Understand the build-in-public approach — fixing problems live, not hiding them
• Get ideas for automating your own show prep with AI agents

🔒 WHY STAY TO THE END
By the end you'll see the fully upgraded pipeline running — the before and after of a system that went from "kind of working" to completely hands-off, and I'll walk through every fix that got it there.

📎 SOURCES / LINKS
• N/A — this is a first-person walkthrough of [Creator]'s own system
"""

# Load .env
AIRTABLE_TOKEN = ""
with open(".env") as f:
    for line in f:
        if line.startswith("AIRTABLE_PERSONAL_ACCESS_TOKEN="):
            AIRTABLE_TOKEN = line.strip().split("=", 1)[1]

# --- Google Auth ---
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

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

# --- Step 1: Add a new tab to the Content Doc ---
print(f"Step 1: Adding tab '{TAB_TITLE}' to Content Doc (Series)...")

add_tab_request = {
    "requests": [
        {
            "addDocumentTab": {
                "tabProperties": {
                    "title": TAB_TITLE
                }
            }
        }
    ]
}

resp = requests.post(
    f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
    headers=headers,
    json=add_tab_request
)

if resp.status_code != 200:
    print(f"ERROR adding tab: {resp.status_code}")
    print(resp.text[:1000])
    exit(1)

# Get the new tab ID
tab_id = None
replies = resp.json().get("replies", [])
for reply in replies:
    tab_props = (
        reply.get("addDocumentTab", {}).get("tabProperties", {}) or
        reply.get("addTab", {}).get("tabProperties", {})
    )
    tab_id = tab_props.get("tabId", "")

if not tab_id:
    # Fallback: re-read the document to find the tab
    print("Fetching tab ID from document...")
    doc_resp = requests.get(
        f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}?includeTabsContent=true",
        headers={"Authorization": f"Bearer {creds.token}"}
    )
    if doc_resp.status_code == 200:
        tabs = doc_resp.json().get("tabs", [])
        for tab in tabs:
            tp = tab.get("tabProperties", {})
            if tp.get("title", "") == TAB_TITLE:
                tab_id = tp.get("tabId", "")
                break

print(f"New tab ID: {tab_id}")

# --- Step 2: Insert content into the new tab ---
print("\nStep 2: Inserting content into tab...")

insert_request = {
    "requests": [
        {
            "insertText": {
                "location": {
                    "segmentId": "",
                    "index": 1,
                    "tabId": tab_id
                },
                "text": CONTENT
            }
        }
    ]
}

resp = requests.post(
    f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
    headers=headers,
    json=insert_request
)

if resp.status_code == 200:
    print("Content inserted successfully!")
else:
    print(f"ERROR inserting content: {resp.status_code}")
    print(resp.text[:1000])
    exit(1)

# --- Step 3: Create Airtable record ---
print("\nStep 3: Creating Airtable record...")

doc_url = f"https://docs.google.com/document/d/{CONTENT_DOC_ID}/edit"

at_headers = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

at_data = {
    "records": [{
        "fields": {
            "Title": TAB_TITLE,
            "Google Doc URL": doc_url,
            "Status": "Draft"
        }
    }]
}

at_resp = requests.post(
    f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{CONTENT_DOCS_TABLE}",
    headers=at_headers,
    json=at_data
)

if at_resp.status_code == 200:
    print("Airtable record created!")
    record = at_resp.json().get("records", [{}])[0]
    print(f"Record ID: {record.get('id', 'unknown')}")
else:
    print(f"Airtable: {at_resp.status_code}")
    print(at_resp.text[:500])

print(f"\n{'='*60}")
print(f"Content Doc (Series): {doc_url}")
print(f"New tab: {TAB_TITLE}")
print(f"{'='*60}")
