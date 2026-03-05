#!/usr/bin/env python3
"""Format the 'Upgrading My Daily AI Show Doc' content doc tab — H3 bold headers, bullets for the rest."""

import pickle, requests, json, re
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

with open("youtube_token.pickle", "rb") as f:
    creds = pickle.load(f)
if not creds.valid:
    creds.refresh(Request())
    with open("youtube_token.pickle", "wb") as f:
        pickle.dump(creds, f)

headers = {
    "Authorization": f"Bearer {creds.token}",
    "Content-Type": "application/json"
}

DOC_ID = "YOUR_CONTENT_DOC_MASTER_ID"
TAB_ID = "YOUR_TAB_ID"

# ===== CONTENT BLOCKS =====
# h1 = doc title, h3 = section headers (bold), bullet = bullet points, plain = no bullet
blocks = [
    ("CONTENT DOC — UPGRADING MY DAILY AI SHOW DOC\n", "h1"),

    ("Title:\n", "h3"),
    ("How I Film 3 Videos a Day Without Writing a Single Script\n", "plain"),

    ("Benefits:\n", "h3"),
    ("No more hunting for video ideas or staring at a blank page every morning\n", "bullet"),
    ("Don't have to write outlines from scratch — the AI does it while you sleep\n", "bullet"),
    ("Free workflow file at the end so you never have to figure out the setup yourself\n", "bullet"),

    ("Steps:\n", "h3"),
    ("1 - Show the system working right now (proof)\n", "plain"),
    ("2 - How the pipeline works under the hood\n", "plain"),
    ("3 - The problems that need fixing\n", "plain"),
    ("4 - Upgrade each piece live on screen\n", "plain"),
    ("5 - Before vs. after results\n", "plain"),
    ("6 - Download the workflow file (free)\n", "plain"),

    ("So by the end of this video:\n", "h3"),
    ("You'll see the fully upgraded pipeline running, understand exactly how it works, and you'll get the actual workflow .md file I use so you can build your own version.\n", "bullet"),

    ("🎯 ONE-LINER\n", "h3"),
    ("I'm upgrading the AI agent that writes my daily show doc so I can film 3 videos a day without thinking about what to say.\n", "bullet"),

    ("🏷️ TITLES (pick 1 before filming)\n", "h3"),
    ("I Built an AI Agent That Writes My Videos For Me\n", "bullet"),
    ("How I Film 3 Videos a Day Without a Script\n", "bullet"),
    ("My AI Agents Do All the Work (I Just Read & Film)\n", "bullet"),
    ("The $100K System: AI Writes My Show, I Hit Record\n", "bullet"),
    ("I Automated the Hardest Part of YouTube\n", "bullet"),

    ("🖼️ THUMBNAIL IDEAS\n", "h3"),
    ("Concept A — Split screen: left side = messy wall of text/chaos, right side = clean formatted show doc on screen. [Creator] pointing at the doc with a surprised expression. Text overlay: \"IT WRITES ITSELF\"\n", "bullet"),
    ("Concept B — [Creator] sitting at desk with arms behind head looking relaxed, laptop open showing the show doc. Multiple video thumbnails floating around him. Text overlay: \"3 VIDEOS/DAY\"\n", "bullet"),

    ("🎤 SAY THIS (word-for-word intro — read this aloud):\n", "h3"),
    ("\"My AI agents make it so easy to film three videos a day — because every morning, there's a show doc waiting for me. No hunting for ideas, no writing bullet points from scratch, no staring at a blank page. I just wake up, read the document, film, and my work is done. I make six figures a year doing this, and today I'm going to show you exactly how this system works by upgrading it live — fixing the problems as they come.\"\n", "bullet"),

    ("📊 4P FRAMEWORK (inspiration for the intro — not spoken on camera)\n", "h3"),
    ("Proof: I film 3 videos per day using an AI-generated show doc and make six figures a year from it.\n", "bullet"),
    ("Promise: You'll see exactly how the daily show doc system works and how I'm upgrading it to run fully automatically every single day.\n", "bullet"),
    ("Problem: Without a system like this, you're spending hours researching, outlining, and prepping — which means you either burn out or don't post enough.\n", "bullet"),
    ("Path: Start with proof that the system works, then walk through the live upgrade process — fixing problems as they appear, not starting from scratch.\n", "bullet"),

    ("💎 BENEFITS\n", "h3"),
    ("Today I'll show you:\n", "bullet"),
    ("How my AI agent writes a full show doc every morning without me touching anything\n", "bullet"),
    ("The exact problems that broke the pipeline — and how I fix them live\n", "bullet"),
    ("How to go from \"kind of automated\" to fully hands-off\n", "bullet"),
    ("The workflow file that powers this entire system (free at the end)\n", "bullet"),

    ("So by the end:\n", "bullet"),
    ("You'll see the fully upgraded pipeline running, understand exactly how it works, and you'll get the actual workflow .md file I use so you can build your own version.\n", "bullet"),

    ("📋 STEPS\n", "h3"),
    ("🎬 The Proof: Show the system working right now\n", "bullet"),
    ("🔍 The Pipeline: How it works under the hood\n", "bullet"),
    ("🔧 The Problems: What's broken and why\n", "bullet"),
    ("🛠️ The Fix: Upgrade each piece live on screen\n", "bullet"),
    ("✅ The Result: Before vs. after\n", "bullet"),
    ("🎁 The Gift: Download the workflow file\n", "bullet"),

    ("Let's get started!\n", "plain"),

    ("🎬 STEP 1 — The Proof: Show the System Working\n", "h3"),
    ("Open with undeniable proof that this system is real and running.\n", "bullet"),
    ("🗣️ Say:\n", "bullet"),
    ("\"Before I touch anything, let me show you what this system already does. Every morning, my AI agent scrapes trending topics, picks the best ones for my niche, writes a full show doc with titles, intros, outlines, and talking points — and sends it to me. All I do is wake up, open the doc, and film. Let me show you today's.\"\n", "bullet"),
    ("🖥️ Show:\n", "bullet"),
    ("Open the master Show Doc Google Doc — show today's tab with all 3 topics fully written\n", "bullet"),
    ("Show the Telegram morning briefing message on your phone\n", "bullet"),
    ("Quick scroll through the doc: titles, SAY THIS intro, walkthrough steps — it's all there\n", "bullet"),
    ("Key point: This is real. It's running. It made this video possible.\n", "bullet"),

    ("🔍 STEP 2 — The Pipeline: How It Works Under the Hood\n", "h3"),
    ("Pull back the curtain. Show the moving parts without overexplaining.\n", "bullet"),
    ("🗣️ Say:\n", "bullet"),
    ("\"Here's what's actually happening behind the scenes. I have an n8n workflow that triggers every morning. It pulls viral videos from Airtable, picks the top trending topics, sends them to Claude, and Claude writes the full show doc — formatted, with intros, with sources. Then it pushes it to Google Docs and pings me on Telegram. The whole thing runs while I'm asleep.\"\n", "bullet"),
    ("🖥️ Show:\n", "bullet"),
    ("Quick tour of the n8n workflow (don't go deep — just show the flow visually)\n", "bullet"),
    ("The Airtable tables: Viral Videos, Show Docs\n", "bullet"),
    ("The Google Doc output with tabs for each day\n", "bullet"),
    ("Key point: n8n triggers it, Claude writes it, Google Docs stores it, Telegram delivers it.\n", "bullet"),

    ("🔧 STEP 3 — The Problems: What's Broken\n", "h3"),
    ("Be honest about what's not working. This is the build-in-public part.\n", "bullet"),
    ("🗣️ Say:\n", "bullet"),
    ("\"Now here's the thing — this system isn't perfect yet. It works, but there are issues. Sometimes the formatting breaks. Sometimes it picks topics I've already covered. Sometimes the intro doesn't sound like me. Today I'm going to go through each problem and fix it live.\"\n", "bullet"),
    ("🖥️ Show:\n", "bullet"),
    ("Examples of the actual problems — broken formatting, duplicate topics, generic intros\n", "bullet"),
    ("Key point: Real systems have real problems. The value is in watching how you fix them.\n", "bullet"),

    ("🛠️ STEP 4 — The Fix: Upgrade Each Piece Live\n", "h3"),
    ("This is the meat of the video. Fix problems as they come, on screen.\n", "bullet"),
    ("🗣️ Say:\n", "bullet"),
    ("\"Alright, let's fix this. I'm going to go through each issue one by one, and you're going to watch me upgrade the pipeline in real time. No cuts, no pre-made solutions. Just me and Claude Code figuring it out.\"\n", "bullet"),
    ("🖥️ Show:\n", "bullet"),
    ("Open Claude Code terminal\n", "bullet"),
    ("Work through each fix live — talk through what you're telling the AI to do\n", "bullet"),
    ("Show the workflow .md file getting updated as you go\n", "bullet"),
    ("Show each improvement landing in the actual output\n", "bullet"),
    ("Key point: The path is the content. Viewers learn by watching you problem-solve.\n", "bullet"),

    ("✅ STEP 5 — The Result: Before vs. After\n", "h3"),
    ("Show the transformation. Side by side if possible.\n", "bullet"),
    ("🗣️ Say:\n", "bullet"),
    ("\"Let me show you the difference. Here's what the show doc looked like before — and here's what it looks like now. The formatting is clean, the topics are fresh, the intros sound like me, and the whole thing runs every single morning without me touching it.\"\n", "bullet"),
    ("🖥️ Show:\n", "bullet"),
    ("Side by side: old output vs new output\n", "bullet"),
    ("Run the upgraded pipeline once to show it working end to end\n", "bullet"),
    ("Key point: From \"kind of working\" to fully hands-off.\n", "bullet"),

    ("🎁 STEP 6 — The Gift: Download the Workflow File\n", "h3"),
    ("Close with the Skool CTA. Give them something real.\n", "bullet"),
    ("🗣️ Say:\n", "bullet"),
    ("\"If you want the exact workflow file I use — the .md document that powers this entire system — I put it in my free Skool community. You can literally copy-paste it into your own setup and start using it today. Link is in the description.\"\n", "bullet"),
    ("🖥️ Show:\n", "bullet"),
    ("Open the Skool community page briefly\n", "bullet"),
    ("Show the workflow file sitting there ready to download\n", "bullet"),
    ("Key point: Real value, free, no catch.\n", "bullet"),

    ("🔒 WHY STAY TO THE END\n", "h3"),
    ("By the end you'll see the fully upgraded pipeline running — the before and after of a system that went from \"kind of working\" to completely hands-off. And at the very end, I'm giving you the actual workflow file I use — the exact .md document that powers this entire system — so you can copy-paste it into your own setup. It's free inside my Skool community.\n", "bullet"),

    ("🎁 END-OF-VIDEO GIFT (Skool CTA)\n", "h3"),
    ("What: The Content Doc Process SOP — the actual workflow .md file that powers this system\n", "bullet"),
    ("Where: Free inside the Skool community (link in description)\n", "bullet"),
    ("Safety note: The public version has the process + output template only. No API keys, no table IDs, no script names, no internal doc IDs.\n", "bullet"),

    ("📎 SOURCES / LINKS\n", "h3"),
    ("Supporting diagram — https://drive.google.com/file/d/YOUR_DIAGRAM_FILE_ID/view?usp=sharing\n", "bullet"),
    ("Skool community — [link in description]\n", "bullet"),
]

# ===== STEP 1: Clear existing content =====
print("Step 1: Clearing existing content...")
doc_resp = requests.get(
    f"https://docs.googleapis.com/v1/documents/{DOC_ID}?includeTabsContent=true",
    headers=headers
)
doc_data = doc_resp.json()

for tab in doc_data.get("tabs", []):
    if tab.get("tabProperties", {}).get("tabId") == TAB_ID:
        tab_content = tab.get("documentTab", {}).get("body", {}).get("content", [])
        last_elem = tab_content[-1]
        end_index = last_elem.get("endIndex", 1)
        if end_index > 2:
            requests.post(
                f"https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate",
                headers=headers,
                json={"requests": [{
                    "deleteContentRange": {
                        "range": {"startIndex": 1, "endIndex": end_index - 1, "tabId": TAB_ID}
                    }
                }]}
            )
            print(f"  Cleared {end_index - 1} characters.")
        break

# ===== STEP 2: Insert all text =====
print("Step 2: Inserting text...")
all_text = "".join(text for text, _ in blocks)

insert_resp = requests.post(
    f"https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate",
    headers=headers,
    json={"requests": [{
        "insertText": {
            "location": {"index": 1, "tabId": TAB_ID},
            "text": all_text
        }
    }]}
)
if insert_resp.status_code != 200:
    print(f"ERROR: {insert_resp.status_code}\n{insert_resp.text[:500]}")
    exit(1)
print(f"  Inserted {len(all_text)} chars.")

# ===== STEP 3: Apply styles =====
print("Step 3: Applying styles...")
style_requests = []
bullet_requests = []
current_index = 1

for text, style in blocks:
    start = current_index
    end = start + len(text)

    if style == "h1":
        # Title: bold, centered — heading applied in step 5b
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "paragraphStyle": {"alignment": "CENTER"},
                "fields": "alignment"
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "textStyle": {"bold": True},
                "fields": "bold"
            }
        })

    elif style == "h3":
        # Section header: bold — heading applied in step 5b
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "textStyle": {"bold": True},
                "fields": "bold"
            }
        })

    elif style == "bullet":
        bullet_requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
            }
        })

    current_index = end

# Apply text/paragraph styles first
if style_requests:
    print(f"  Applying {len(style_requests)} style requests...")
    fmt_resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": style_requests}
    )
    if fmt_resp.status_code != 200:
        print(f"  ERROR: {fmt_resp.status_code}\n{fmt_resp.text[:500]}")
        exit(1)

# ===== STEP 4: Apply bullets =====
if bullet_requests:
    print(f"Step 4: Applying {len(bullet_requests)} bullet requests...")
    bul_resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": bullet_requests}
    )
    if bul_resp.status_code != 200:
        print(f"  ERROR: {bul_resp.status_code}\n{bul_resp.text[:500]}")
        exit(1)

# ===== STEP 5b: Apply heading styles by re-reading document =====
print("Step 5: Applying H1 and H3 headings using actual positions...")

H1_PREFIXES = ["CONTENT DOC"]
H3_PREFIXES = ["🎯", "🏷", "🖼", "🎤", "📊", "📋", "💎", "🔒", "📎", "🎁", "🎬", "🔍", "🔧", "🛠", "✅"]
H3_EXACT = ["Title:", "Benefits:", "Steps:", "So by the end of this video:"]

doc_resp2 = requests.get(
    f"https://docs.googleapis.com/v1/documents/{DOC_ID}?includeTabsContent=true",
    headers=headers
)
heading_requests = []
heading_ranges = []  # Track heading positions for bullet removal

for tab in doc_resp2.json().get("tabs", []):
    if tab.get("tabProperties", {}).get("tabId") == TAB_ID:
        content = tab.get("documentTab", {}).get("body", {}).get("content", [])
        for elem in content:
            para = elem.get("paragraph", {})
            text_parts = []
            for pe in para.get("elements", []):
                text_parts.append(pe.get("textRun", {}).get("content", ""))
            full_text = "".join(text_parts).strip()
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
                for p in H3_PREFIXES:
                    if full_text.startswith(p):
                        target = "HEADING_3"
                        break
            if not target:
                for exact in H3_EXACT:
                    if full_text == exact or full_text.startswith(exact):
                        target = "HEADING_3"
                        break

            if target:
                heading_requests.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": start_idx, "endIndex": end_idx, "tabId": TAB_ID},
                        "paragraphStyle": {"namedStyleType": target},
                        "fields": "namedStyleType"
                    }
                })
                heading_ranges.append({"startIndex": start_idx, "endIndex": end_idx})
        break

if heading_requests:
    print(f"  Applying {len(heading_requests)} heading updates...")
    hdr_resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": heading_requests}
    )
    if hdr_resp.status_code != 200:
        print(f"  ERROR: {hdr_resp.status_code}\n{hdr_resp.text[:500]}")
        exit(1)

# ===== STEP 6: Remove bullets from heading paragraphs =====
if heading_ranges:
    print(f"Step 6: Removing bullets from {len(heading_ranges)} heading paragraphs...")
    delete_bullet_requests = []
    for r in heading_ranges:
        delete_bullet_requests.append({
            "deleteParagraphBullets": {
                "range": {"startIndex": r["startIndex"], "endIndex": r["endIndex"], "tabId": TAB_ID}
            }
        })
    dbul_resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": delete_bullet_requests}
    )
    if dbul_resp.status_code != 200:
        print(f"  ERROR: {dbul_resp.status_code}\n{dbul_resp.text[:500]}")
        exit(1)
    print("  Bullets removed from headings.")

print(f"\nDone! H1 title + H3 bold headers (no bullets) + bullets for everything else.")
print(f"View: https://docs.google.com/document/d/{DOC_ID}/edit")
