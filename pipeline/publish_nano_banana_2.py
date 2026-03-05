#!/usr/bin/env python3
"""Publish the Nano Banana 2 content doc: add tab, insert content, format, upload diagram, Airtable record."""

import pickle, requests, json, re, os, time
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- Config ---
TOKEN_PATH = "youtube_token.pickle"
CONTENT_DOC_ID = "YOUR_CONTENT_DOC_MASTER_ID"
AIRTABLE_BASE = "YOUR_AIRTABLE_BASE_ID"
CONTENT_DOCS_TABLE = "YOUR_CONTENT_DOCS_TABLE_ID"
SHARED_FOLDER_ID = "YOUR_SHARED_DRIVE_FOLDER_ID"
TAB_TITLE = "Nano Banana 2 — Thumbnail & AI Clone Test"

# Load .env
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

# ============================================================
# STEP A: Upload diagram to Google Drive
# ============================================================
print("=" * 60)
print("STEP A: Uploading diagram to Google Drive...")
print("=" * 60)

diagram_path = "diagrams/nano_banana_2_test.excalidraw"
diagram_file_id = None

if os.path.exists(diagram_path):
    import io
    with open(diagram_path, "rb") as f:
        diagram_data = f.read()

    # Create file metadata
    meta = {
        "name": "nano_banana_2_test.excalidraw",
        "parents": [SHARED_FOLDER_ID],
        "mimeType": "application/octet-stream"
    }

    # Multipart upload
    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Type: application/json; charset=UTF-8\r\n\r\n'
        f'{json.dumps(meta)}\r\n'
        f"--{boundary}\r\n"
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + diagram_data + f"\r\n--{boundary}--\r\n".encode()

    upload_resp = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
        headers={
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": f"multipart/related; boundary={boundary}"
        },
        data=body
    )

    if upload_resp.status_code == 200:
        diagram_file_id = upload_resp.json().get("id")
        print(f"  Uploaded! File ID: {diagram_file_id}")

        # Set permission: anyone with link = reader
        perm_resp = requests.post(
            f"https://www.googleapis.com/drive/v3/files/{diagram_file_id}/permissions",
            headers=headers,
            json={"role": "reader", "type": "anyone"}
        )
        print(f"  Permission set: {perm_resp.status_code}")
    else:
        print(f"  ERROR uploading diagram: {upload_resp.status_code}")
        print(upload_resp.text[:500])
else:
    print(f"  Diagram file not found: {diagram_path}")

diagram_url = f"https://drive.google.com/file/d/{diagram_file_id}/view?usp=sharing" if diagram_file_id else ""

# ============================================================
# STEP B: Content blocks with styles
# ============================================================

blocks = [
    ("CONTENT DOC — NANO BANANA 2 THUMBNAIL & AI CLONE TEST\n", "h1"),

    ("Title:\n", "h3"),
    ("I Tested Google's New AI on My Face — Nano Banana 2 Review\n", "plain"),

    ("Benefits:\n", "h3"),
    ("Never wonder which AI image model actually works for thumbnails — see real results head-to-head\n", "bullet"),
    ("Don't waste hours testing yourself — watch me break it with 3 real creator workflows\n", "bullet"),
    ("Get the exact prompts that produced the best results (free in the community)\n", "bullet"),

    ("Steps:\n", "h3"),
    ("1 — The News (What Just Dropped)\n", "plain"),
    ("2 — Thumbnail Generation Test\n", "plain"),
    ("3 — Face Consistency Stress Test\n", "plain"),
    ("4 — AI Clone Creator Test\n", "plain"),
    ("5 — The Verdict (Pro vs 2)\n", "plain"),

    ("So by the end of this video:\n", "h3"),
    ("You'll know exactly whether Nano Banana 2 is good enough to replace your current thumbnail and AI image workflow — and you'll have seen real side-by-side results with my actual face to prove it.\n", "bullet"),

    ("🎯 ONE-LINER\n", "h3"),
    ("I test Google's brand new Nano Banana 2 on the three things AI creators actually care about — thumbnails, face consistency, and building a full AI clone of yourself.\n", "bullet"),

    ("🏷️ TITLES (pick 1 before filming)\n", "h3"),
    ("I Tested Google's New AI on My Face — Nano Banana 2 Review\n", "bullet"),
    ("Google's New AI Makes Thumbnails With YOUR Face (Nano Banana 2)\n", "bullet"),
    ("Nano Banana 2 Just Dropped — I Tested It For Thumbnails & AI Clones\n", "bullet"),
    ("This $0.05 AI Makes YouTube Thumbnails With My Face\n", "bullet"),
    ("Google's New Image AI vs My Face — Who Wins?\n", "bullet"),

    ("🖼️ THUMBNAIL IDEAS\n", "h3"),
    ("Concept A — Split screen: [Creator]'s real face on the left, AI-generated version on the right (slightly off but impressive), shocked expression, bold text \"MY AI CLONE?!\", Nano Banana 2 logo in corner, dark background with blue/purple gradient\n", "bullet"),
    ("Concept B — [Creator] pointing at a laptop screen showing multiple AI-generated thumbnails of himself, exaggerated surprised face, text overlay \"$0.05 THUMBNAILS\", Google/Gemini branding visible\n", "bullet"),

    ("🎤 SAY THIS (word-for-word intro — read this aloud):\n", "h3"),
    ("\"Google just dropped Nano Banana 2 — literally yesterday — and it's supposed to be 5x faster, half the cost, and 4K resolution. But here's what I actually want to know: can it make thumbnails with MY face? Can it clone ME into different scenarios? I ran three real tests — thumbnails, face consistency, and a full AI clone workflow — and the results genuinely surprised me. Let me show you.\"\n", "bullet"),

    ("📊 4P FRAMEWORK (inspiration for the intro — not spoken on camera)\n", "h3"),
    ("Proof: Nano Banana 2 launched Feb 26 2026, 5-10x faster than Pro, 50% cheaper, 4K output, available right now in AI Studio\n", "bullet"),
    ("Promise: See real results of the new model on three creator-specific tests — thumbnails, face consistency, and AI clone generation\n", "bullet"),
    ("Problem: If you don't test this now, you'll keep using slower and more expensive tools while everyone else upgrades — or you'll waste time testing it yourself on the wrong prompts\n", "bullet"),
    ("Path: Three progressively harder tests — start with thumbnails (practical), then face consistency (stress test), then full AI clone (the dream)\n", "bullet"),

    ("💎 BENEFITS\n", "h3"),
    ("Today I'll show you:\n", "bullet"),
    ("The actual results when I feed Nano Banana 2 my face references and ask it to make YouTube thumbnails — no cherry-picking, every attempt shown\n", "bullet"),
    ("A face consistency stress test — same face, 10 wildly different scenarios — to see if it can actually maintain my likeness\n", "bullet"),
    ("A full AI clone workflow — me holding a camera, filming in different locations, UGC-style content — built entirely with AI\n", "bullet"),
    ("The exact prompts and settings that produced the best results (free in the community)\n", "bullet"),

    ("So by the end:\n", "bullet"),
    ("You'll know whether Nano Banana 2 is ready for your thumbnail and content workflow — with real proof, not just hype.\n", "bullet"),

    ("📋 STEPS\n", "h3"),
    ("📰 The News — What Just Dropped\n", "bullet"),
    ("🖼️ Thumbnail Generation Test\n", "bullet"),
    ("🔍 Face Consistency Stress Test\n", "bullet"),
    ("🤖 AI Clone Creator Test\n", "bullet"),
    ("⚖️ The Verdict — Pro vs 2\n", "bullet"),

    ("Let's get started!\n", "plain"),

    ("📰 STEP 1 — The News (What Just Dropped)\n", "h3"),
    ("Quick context on what Nano Banana 2 is and why it matters for creators.\n", "bullet"),
    ("🗣️ Say:\n", "bullet"),
    ("\"So Nano Banana 2 just launched yesterday — February 26th. The official model name is Gemini 3.1 Flash Image, but everyone calls it Nano Banana 2. It's basically the successor to Nano Banana Pro, which I've been using for months. The big claims: 5 to 10x faster, half the price, and native 4K resolution. It's live right now in AI Studio — I'm going to open it up and test it on the things that actually matter to us as creators.\"\n", "bullet"),
    ("🖥️ Show:\n", "bullet"),
    ("AI Studio interface with the model selected\n", "bullet"),
    ("Side-by-side spec comparison: Nano Banana Pro vs Nano Banana 2 (speed, cost, resolution)\n", "bullet"),
    ("Quick generation to show it works — any simple prompt\n", "bullet"),
    ("Key point: Nano Banana 2 is live right now, dramatically faster and cheaper than Pro, and we're about to stress-test it on real creator workflows.\n", "bullet"),

    ("🖼️ STEP 2 — Thumbnail Generation Test\n", "h3"),
    ("The main event — can this model generate YouTube thumbnails with my face that actually look good enough to use?\n", "bullet"),
    ("🗣️ Say:\n", "bullet"),
    ("\"This is what I really care about. I already use Nano Banana Pro to generate my thumbnails — I feed it my face references and a viral thumbnail as inspiration, and it remakes it with my face. The question is: can Nano Banana 2 do the same thing faster and cheaper? Let's find out. I'm going to take three viral thumbnails from my niche and generate versions with my face using both Pro and Nano Banana 2, side by side.\"\n", "bullet"),
    ("🖥️ Show:\n", "bullet"),
    ("Upload face reference images into AI Studio\n", "bullet"),
    ("Pick 3 viral thumbnails as style inspiration\n", "bullet"),
    ("Generate with Nano Banana 2 — show the prompt, the loading time, and the result\n", "bullet"),
    ("Generate the same prompt with Nano Banana Pro for comparison\n", "bullet"),
    ("Side-by-side results for each of the 3 thumbnails\n", "bullet"),
    ("Rate each on: face accuracy, composition, and \"would you click?\"\n", "bullet"),
    ("Show the generation time difference (4-6 seconds vs 20-60 seconds)\n", "bullet"),
    ("Key point: Show real results — don't cherry-pick. If it fails, show the failure. Audiences trust honesty.\n", "bullet"),

    ("🔍 STEP 3 — Face Consistency Stress Test\n", "h3"),
    ("Push the model harder — can it keep my face consistent across wildly different scenarios?\n", "bullet"),
    ("🗣️ Say:\n", "bullet"),
    ("\"Thumbnails are one thing, but what if you want to use AI for more than just thumbnails? What if you want to create an AI version of yourself that looks consistent across different images? This is where it gets interesting. I'm going to generate myself in 10 completely different scenarios — same face references, wildly different prompts — and see if Nano Banana 2 can keep my face looking like me.\"\n", "bullet"),
    ("🖥️ Show:\n", "bullet"),
    ("Generate 10 scenarios: astronaut on the moon, cooking in a kitchen, on a magazine cover, teaching a class, at the Oscars, in a medieval painting, on a billboard in Times Square, as an anime character, in an action movie poster, surfing at the beach\n", "bullet"),
    ("Show all 10 results in a grid\n", "bullet"),
    ("Point out where the face holds up and where it breaks down\n", "bullet"),
    ("Compare a few of the same scenarios with Nano Banana Pro\n", "bullet"),
    ("Honest assessment: percentage that actually look like you\n", "bullet"),
    ("Key point: Face consistency is the hardest challenge in AI image generation — this test reveals the real ceiling of the model.\n", "bullet"),

    ("🤖 STEP 4 — AI Clone Creator Test\n", "h3"),
    ("The use case every creator wants — generating yourself as a content creator in different scenarios. Think AI UGC, AI influencer, your digital twin holding a camera.\n", "bullet"),
    ("🗣️ Say:\n", "bullet"),
    ("\"Now this is the test I'm most excited about. Imagine you could generate images of yourself filming content — holding a camera, sitting at a desk, walking through a city — without ever leaving your house. That's the AI clone dream. I've been trying to build a pipeline for this, and Nano Banana 2 might be the missing piece. Let me show you what happens when I ask it to generate me as a content creator in different real-world scenarios.\"\n", "bullet"),
    ("🖥️ Show:\n", "bullet"),
    ("Generate: [Creator] holding a camera and filming in a studio setup\n", "bullet"),
    ("Generate: [Creator] walking through Tokyo vlogging with a camera\n", "bullet"),
    ("Generate: [Creator] at a desk with a mic and monitor (podcast/YouTube setup)\n", "bullet"),
    ("Generate: [Creator] holding a product and talking to camera (UGC-style ad)\n", "bullet"),
    ("Generate: [Creator] pointing at a whiteboard explaining something\n", "bullet"),
    ("Show the best results as potential social media posts or B-roll\n", "bullet"),
    ("Test the multi-turn editing: start with one image, then change the background, then change the outfit, then add text — see how the face holds up through edits\n", "bullet"),
    ("Key point: AI clone generation for UGC and content creation is the next frontier — this shows exactly how close we are to fully automated AI content.\n", "bullet"),

    ("⚖️ STEP 5 — The Verdict (Pro vs 2)\n", "h3"),
    ("Honest comparison and final recommendation.\n", "bullet"),
    ("🗣️ Say:\n", "bullet"),
    ("\"Alright, after running all three tests, here's my honest take. Nano Banana 2 is insanely fast — we're talking 5 seconds versus 30 to 60 seconds for Pro. It's half the price. And the quality is genuinely close. But there's a catch — and I'll tell you exactly what it is. If you're making thumbnails, here's what I'd recommend. If you're building an AI clone, here's what I'd do differently.\"\n", "bullet"),
    ("🖥️ Show:\n", "bullet"),
    ("Final comparison grid: all results from all three tests\n", "bullet"),
    ("Speed comparison: actual generation times recorded during tests\n", "bullet"),
    ("Cost breakdown: what each test run cost in API credits\n", "bullet"),
    ("Scorecard: Face accuracy, speed, quality, text rendering — Pro vs 2\n", "bullet"),
    ("Final recommendation based on use case\n", "bullet"),
    ("Key point: Give a clear, honest recommendation — not just \"it depends.\" Tell them exactly which model to use for which workflow.\n", "bullet"),

    ("🔒 WHY STAY TO THE END\n", "h3"),
    ("In the verdict, I'll share which model actually won each test and my exact recommendation for which one to use depending on your workflow — plus the full prompt library I used for every test is free in the community.\n", "bullet"),

    ("🎁 END-OF-VIDEO GIFT (Skool CTA)\n", "h3"),
    ("What: The complete prompt library — every prompt used in every test (thumbnail generation, face consistency, AI clone), plus the face reference tips that get the best results\n", "bullet"),
    ("Where: Free inside the Skool community (link in description)\n", "bullet"),
    ("Safety note: Strip any API keys, internal file paths, or Airtable IDs. Share only the prompts, the model settings, and the face reference guidelines.\n", "bullet"),

    ("📎 SOURCES / LINKS\n", "h3"),
    (f"Supporting diagram — {diagram_url}\n" if diagram_url else "Supporting diagram — [pending upload]\n", "bullet"),
    ("Google's official Nano Banana 2 announcement — https://blog.google/innovation-and-ai/technology/ai/nano-banana-2/\n", "bullet"),
    ("The Decoder independent comparison — https://the-decoder.com/googles-nano-banana-2-brings-pro-level-image-generation-to-flash-speeds-at-up-to-40-lower-api-cost/\n", "bullet"),
    ("Google AI Studio image generation docs — https://ai.google.dev/gemini-api/docs/image-generation\n", "bullet"),
    ("How Nano Banana got its name — https://blog.google/products-and-platforms/products/gemini/how-nano-banana-got-its-name/\n", "bullet"),
    ("Skool community — link in description\n", "bullet"),
]

# ============================================================
# STEP C: Add tab to Content Doc
# ============================================================
print("\n" + "=" * 60)
print("STEP B: Adding tab to Content Doc (Series)...")
print("=" * 60)

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
    print(f"ERROR adding tab: {resp.status_code}")
    print(resp.text[:1000])
    exit(1)

# Get tab ID
tab_id = None
replies = resp.json().get("replies", [])
for reply in replies:
    tab_props = (
        reply.get("addDocumentTab", {}).get("tabProperties", {}) or
        reply.get("addTab", {}).get("tabProperties", {})
    )
    tab_id = tab_props.get("tabId", "")

if not tab_id:
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

# ============================================================
# STEP D: Insert content
# ============================================================
print("\n" + "=" * 60)
print("STEP C: Inserting content...")
print("=" * 60)

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
# STEP E: Apply styles (bold for h1/h3, center for h1)
# ============================================================
print("\n" + "=" * 60)
print("STEP D: Applying text styles...")
print("=" * 60)

style_requests = []
bullet_requests = []
current_index = 1

for text, style in blocks:
    start = current_index
    end = start + len(text)

    if style == "h1":
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
    elif style == "h3":
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": tab_id},
                "textStyle": {"bold": True},
                "fields": "bold"
            }
        })
    elif style == "bullet":
        bullet_requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": start, "endIndex": end, "tabId": tab_id},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
            }
        })

    current_index = end

if style_requests:
    print(f"  Applying {len(style_requests)} style requests...")
    fmt_resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": style_requests}
    )
    if fmt_resp.status_code != 200:
        print(f"  ERROR: {fmt_resp.status_code}\n{fmt_resp.text[:500]}")
        exit(1)

# ============================================================
# STEP F: Apply bullets
# ============================================================
if bullet_requests:
    print(f"  Applying {len(bullet_requests)} bullet requests...")
    bul_resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": bullet_requests}
    )
    if bul_resp.status_code != 200:
        print(f"  ERROR: {bul_resp.status_code}\n{bul_resp.text[:500]}")
        exit(1)

# ============================================================
# STEP G: Re-read doc, apply heading styles, remove bullets from headings
# ============================================================
print("\n" + "=" * 60)
print("STEP E: Applying headings + removing bullets from headings...")
print("=" * 60)

H1_PREFIXES = ["CONTENT DOC"]
H3_PREFIXES = ["🎯", "🏷", "🖼", "🎤", "📊", "📋", "💎", "🔒", "📎", "🎁", "📰", "🔍", "🤖", "⚖"]
H3_EXACT = ["Title:", "Benefits:", "Steps:", "So by the end of this video:"]

doc_resp2 = requests.get(
    f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}?includeTabsContent=true",
    headers=headers
)
heading_requests = []
heading_ranges = []

for tab in doc_resp2.json().get("tabs", []):
    if tab.get("tabProperties", {}).get("tabId") == tab_id:
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
            # Also catch STEP headers like "📰 STEP 1", "🖼️ STEP 2", etc.
            if not target and "STEP " in full_text and "—" in full_text:
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
    hdr_resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": heading_requests}
    )
    if hdr_resp.status_code != 200:
        print(f"  ERROR: {hdr_resp.status_code}\n{hdr_resp.text[:500]}")
        exit(1)

if heading_ranges:
    print(f"  Removing bullets from {len(heading_ranges)} heading paragraphs...")
    delete_bullet_requests = []
    for r in heading_ranges:
        delete_bullet_requests.append({
            "deleteParagraphBullets": {
                "range": {"startIndex": r["startIndex"], "endIndex": r["endIndex"], "tabId": tab_id}
            }
        })
    dbul_resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": delete_bullet_requests}
    )
    if dbul_resp.status_code != 200:
        print(f"  ERROR: {dbul_resp.status_code}\n{dbul_resp.text[:500]}")
        exit(1)
    print("  Bullets removed from headings.")

# ============================================================
# STEP H: Make URLs clickable
# ============================================================
print("\n" + "=" * 60)
print("STEP F: Making URLs clickable...")
print("=" * 60)

doc_resp3 = requests.get(
    f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}?includeTabsContent=true",
    headers=headers
)
link_requests = []

for tab in doc_resp3.json().get("tabs", []):
    if tab.get("tabProperties", {}).get("tabId") == tab_id:
        content = tab.get("documentTab", {}).get("body", {}).get("content", [])
        for elem in content:
            para = elem.get("paragraph", {})
            for pe in para.get("elements", []):
                tr = pe.get("textRun", {})
                text_content = tr.get("content", "")
                start_offset = pe.get("startIndex", 0)

                # Find all URLs in this text run
                for match in re.finditer(r'https?://[^\s\n]+', text_content):
                    url = match.group()
                    url_start = start_offset + match.start()
                    url_end = start_offset + match.end()
                    link_requests.append({
                        "updateTextStyle": {
                            "range": {"startIndex": url_start, "endIndex": url_end, "tabId": tab_id},
                            "textStyle": {"link": {"url": url}},
                            "fields": "link"
                        }
                    })
        break

if link_requests:
    print(f"  Making {len(link_requests)} URLs clickable...")
    link_resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{CONTENT_DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": link_requests}
    )
    if link_resp.status_code != 200:
        print(f"  ERROR: {link_resp.status_code}\n{link_resp.text[:500]}")
    else:
        print("  URLs linked!")
else:
    print("  No URLs found to link.")

# ============================================================
# STEP I: Create Airtable record
# ============================================================
print("\n" + "=" * 60)
print("STEP G: Creating Airtable record...")
print("=" * 60)

at_headers = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

at_data = {
    "records": [{
        "fields": {
            "Title": TAB_TITLE,
            "Status": "\U0001f4dd Draft"
        }
    }]
}

at_resp = requests.post(
    f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{CONTENT_DOCS_TABLE}",
    headers=at_headers,
    json=at_data
)

if at_resp.status_code == 200:
    record = at_resp.json().get("records", [{}])[0]
    print(f"  Airtable record created! ID: {record.get('id', 'unknown')}")
else:
    print(f"  Airtable: {at_resp.status_code}")
    print(at_resp.text[:500])

# ============================================================
# DONE
# ============================================================
print("\n" + "=" * 60)
print("ALL DONE!")
print(f"Content Doc: https://docs.google.com/document/d/{CONTENT_DOC_ID}/edit")
print(f"Tab: {TAB_TITLE} (ID: {tab_id})")
if diagram_url:
    print(f"Diagram: {diagram_url}")
print("=" * 60)
