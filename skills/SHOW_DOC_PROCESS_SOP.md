# Show Doc Creation — Standard Operating Procedure

## Purpose
Create a daily show doc for livestream filming. One Google Doc with 3 topics, each with a complete filming outline: word-for-word intro, titles, hooks, transformation goal, and a unified walkthrough where every step includes what to say, show, type, and open — all in one place.

## System Components

| Component | Location |
|-----------|----------|
| Show Docs Table | `YOUR_SHOW_DOCS_TABLE_ID` in Mate OS base |
| Hall of Fame Table | `YOUR_HALL_OF_FAME_TABLE_ID` in Mate OS base |
| Viral Videos Table | `YOUR_VIRAL_VIDEOS_TABLE_ID` in Mate OS base |
| Google Docs | Created via Drive API, stored in user's Google Drive |
| Format Selection SOP | `skills/FORMAT_SELECTION_SOP.md` |

## Daily Process (7 Steps)

### Step 1: Pull Today's Top Outliers
- Query Viral Videos table for videos published in the last 3 days
- Sort by Outlier Score descending
- Pick the top 3 topics (look at underlying trend, not just the video)
- If topics overlap (e.g., two videos about the same tool), merge them into one topic and pick the next outlier

### Step 2: Match Each Topic to a Hall of Fame Format
- Follow the Format Selection SOP (`skills/FORMAT_SELECTION_SOP.md`)
- Each topic gets one format: New Tool Build-Along, Opportunity Strategy Play, Deep Dive Report, etc.
- Pull the structural template from the Hall of Fame table

### Step 3: Research Each Topic
For each topic, gather:
- **Main source**: The original announcement, blog post, or article
- **Reddit threads**: Search r/singularity, r/ClaudeAI, r/artificial, r/technology, relevant subreddits
- **X/Twitter posts**: Viral tweets, official announcements, hot takes
- **Tech press**: TechCrunch, The Verge, VentureBeat, CNBC, Ars Technica
- **Proof points**: Stats, quotes, data that back up the hook
- **Demos and tools**: Anything the creator can install, test, or show live on screen

### Step 4: Write the 4P Hook
For each topic:
- **Proof**: The undeniable fact or stat that makes this newsworthy
- **Promise**: What you'll show/teach the viewer
- **Problem**: What happens if they don't watch (FOMO, falling behind, missing out)
- **Path**: The journey of the video (numbered steps or overview)

### Step 5: Build the Full Show Doc

Each topic section follows this exact order — designed for minimal friction while filming:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOPIC [N] — [TOPIC NAME]
Format: [Hall of Fame Format Name]
Outlier Score: [Nx] | Source: [Main URL]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📺 SOURCES
* [Creator Name] — "[Video Title]" | [views] views | [publish date] | [clickable URL]
* [Creator Name] — "[Video Title]" | [views] views | [publish date] | [clickable URL]
* [Article/Blog] — "[Title]" | [clickable URL]
(List ALL viral videos and articles used as research for this topic. The creator uses this to cross-reference and check for originality before filming.)

🏷️ TITLES (7 options — pick 1 before filming)
* [Title 1 — primary pick]
* [Title 2]
* [Title 3]
* [Title 4]
* [Title 5]
* [Title 6]
* [Title 7]

🖼️ THUMBNAIL IDEAS
* [Concept A]
* [Concept B]

🎤 SAY THIS (word-for-word intro — read this aloud):
"[2-4 sentences combining Proof + Promise + Problem + Path into a natural spoken script]"

📊 4P FRAMEWORK
Proof: [undeniable stat or fact]
Promise: [what they'll get by the end]
Problem: [why this matters, FOMO angle]
Path: [the journey of the video]

🎣 HOOKS (pick 1 before filming — then go)
* How to: ...
* Statement: ...
* Benefit: ...
* Fact: ...
* Negative: ...
* Personal/Emotional: ...
* Story: ...

🎯 TRANSFORMATION GOAL:
"By the end of this video, you will [specific, concrete outcome — something they can do or have]."

📋 WALKTHROUGH
[Numbered steps, acts, or points depending on format — see format-specific rules below]

Each step uses these markers:
  🗣️ Say: [exact words or close paraphrase — spoken to camera]
  🖥️ Show: [what to open, navigate to, or demonstrate on screen]
  📋 Prompt: [exact copy-paste text to run in Claude, n8n, or other tool]
  🔗 Link: [URL] — "[one line of what to say when opening it]"

Not every step needs all 4 markers. Use whichever apply.

📖 SUMMARY (background only — don't read during stream)
[2-3 paragraph writeup with:]
- The details:
- Why it matters:
- Key stats/quotes:
```

---

## Format-Specific Walkthrough Rules

### New Tool Build-Along
Goal: Viewer builds a working tool or automation live with the creator.

- Number steps: STEP 1, STEP 2, STEP 3...
- Every step must have at least one 🗣️ and one 🖥️
- Include 📋 prompts wherever the viewer will type something into a tool
- End with a "go further" step showing templates or advanced use cases
- Transformation goal = "By the end, you will have a working [X] running in [tool]"

Example structure:
```
STEP 1 — Set the scene (why this tool, why now)
STEP 2 — Open the tool / sign up / show the interface
STEP 3 — Set the trigger or entry point
STEP 4 — Add the AI or processing node (include 📋 prompt here)
STEP 5 — Route or connect the output
STEP 6 — Test it live on screen
STEP 7 — Where to take it next (templates, advanced patterns)
```

### Deep Dive Report
Goal: Viewer fully understands a complex story or product — the full arc, not just one angle.

- Label steps as ACTS: ACT 1, ACT 2, ACT 3...
- After the intro, the creator should be doing something on screen (installing, testing, showing articles)
- Weave article links and on-screen demos throughout — not at the end
- End with a verdict and a clear recommendation
- Transformation goal = "By the end, you will know exactly whether to use [X] — and if so, how"

Example structure:
```
ACT 1 — Open with the most dramatic or surprising news (hook)
ACT 2 — Explain what it actually is (demo or show on screen)
ACT 3 — Install or test it live
ACT 4 — The chaos / controversy / story (open relevant articles)
ACT 5 — The security, cost, or risk angle
ACT 6 — The real cost or hidden truth
ACT 7 — Verdict and the smart alternative
```

### Opportunity Strategy Play
Goal: Viewer identifies a specific niche and has a first action to take this week.

- Label steps as POINTS: POINT 1, POINT 2...
- Each point = one niche. Include the link embedded so the creator can open it while talking.
- Every point should have a 🔗 link to open on screen — no separate link section
- Include at least one live demo (Claude prompt or n8n build) to make it real
- End with a niche selection formula or first-action framework
- Transformation goal = "By the end, you will have picked your niche and have a first action for this week"

Example structure:
```
INTRO MOVE — Show the credibility proof first (industry report, funding news)
POINT 1 — [Niche] + stat + link to open + optional 📋 demo prompt
POINT 2 — [Niche] + stat + link to open
POINT 3 — [Niche] + stat + link to open
POINT 4 — [Niche] + stat + link to open
POINT 5 — [Niche] + stat + link to open + optional demo
LIVE BUILD — Quick live build showing what the niche solution looks like
NICHE SELECTION FORMULA — How to pick yours + business model
```

---

## Section Order Rationale
- **TITLES + THUMBNAIL** → inspiration first, pick before filming, no decisions mid-stream
- **SAY THIS** → gets the creator mentally locked in immediately
- **4P** → reference framework behind the intro
- **HOOKS** → pick 1 before hitting record, never decide mid-stream
- **TRANSFORMATION GOAL** → defines what every step is building toward
- **WALKTHROUGH** → integrated steps: say + show + prompt + link all together per step
- **SUMMARY** → read while prepping, never during filming

---

### Step 6: Add Bonus Section
At the bottom of the doc (after all 3 main topics), add 5-10 extra topic ideas. Use the same black header bar style as the main topics.

Each bonus item uses this format:
```
[Bold title — one-line description of the topic and why it's interesting]
Outlier Score: Nx  |  [views] views  |  [publish date]  |  [link text](URL)
```

- Pull from Viral Radar outliers not used as the top 3
- Also pull from tech news: TechCrunch, The Verge, CNBC, Ars Technica
- Include the publish date so the creator knows how fresh it is
- One-line description should hint at the angle (why it's a good video idea)

### Step 7: Publish and Track
1. Upload to Google Docs via Drive API (HTML with mimeType: application/vnd.google-apps.document)
2. Create a record in the Show Docs Airtable table with:
   - Title, Date, Google Doc URL
   - Status: Draft → Ready → Filmed → Published
   - Topic 1/2/3 names, formats, and outlier scores
   - Source videos
3. Share the Google Doc link in Telegram

---

## Show Doc Quality Checklist
- [ ] SAY THIS is a natural spoken script (not bullet points or framework labels)
- [ ] 7 titles per topic
- [ ] 7 hook variations per topic (all 7 styles present)
- [ ] TRANSFORMATION GOAL is specific — "you will have [X]", not "you will learn about X"
- [ ] WALKTHROUGH uses 🗣️/🖥️/📋/🔗 markers — no separate talking points and links sections
- [ ] Every link has a "say this" note explaining what to do with it on screen
- [ ] At least one on-screen demo per topic (📋 prompt or 🖥️ show)
- [ ] Format-specific structure followed (steps / acts / points)
- [ ] SUMMARY has "The details" + "Why it matters" + key stats/quotes
- [ ] BONUS section has 5+ extra ideas with title, date, and link on each item
- [ ] 📺 SOURCES section under each topic with creator name, video title, views, date, and link
- [ ] All URLs are clickable hyperlinks (not plain text)
- [ ] Google Doc is shared and accessible
- [ ] Airtable record created with correct formats

## Formatting Rules
- **Palette**: Pastel blue minimal — light blue backgrounds, dark blue text, no orange/dark themes
- **Bullet points**: Use actual Google Docs bullets (not text with "•" prefix)
- **All URLs must be clickable hyperlinks** — never leave plain text URLs
- **Sources section**: Every topic gets a 📺 SOURCES section right after the meta line, listing all original creators with their video title, views, publish date, and a clickable link. This lets the creator cross-reference sources and check for originality before filming.
- **H2 topic headers**: Pastel light blue background + dark blue bold text
- **H4 section headers** (emoji-prefixed): Medium blue text with subtle blue bottom border. These appear nested under topics in the sidebar outline.
- **Quote blocks (Say This, Transformation Goal)**: Very light blue background + blue left border, italic
- **4P Framework items**: Very light blue tint background, bold dark blue labels before colon
- **Step/Act/Point titles**: Blue left accent bar + bold blue text
- **Prompt blocks**: Light gray background, monospace font (Roboto Mono)
- **Source items**: Bullets, small gray text, creator name bolded before em dash
- **Document mode**: Set to Pageless in Google Docs (File > Page setup > Pageless) — must be done manually

## Sidebar / Outline Structure
The Google Docs sidebar must show a clean, navigable outline:
- **HEADING_1**: Show Doc title ("SHOW DOC — [Date]")
- **HEADING_2**: Topic headers ("TOPIC 1 — ...", "TOPIC 2 — ...", "TOPIC 3 — ...", "BONUS — ...")
- **HEADING_4**: Emoji section headers only (📺 SOURCES, 🏷️ TITLES, 🖼️ THUMBNAIL IDEAS, 🎤 SAY THIS, 📊 4P FRAMEWORK, 🎣 HOOKS, 🎯 TRANSFORMATION GOAL, 📋 WALKTHROUGH, 📖 SUMMARY)
- **Everything else**: NORMAL_TEXT (must NOT appear in the sidebar)

### Google Docs API Order of Operations
When applying formatting via the API, follow this exact order to prevent heading inheritance bugs:
1. **Insert all text** as a single block
2. **Apply text + paragraph styles** (colors, fonts, spacing, borders, shading)
3. **Apply bullet formatting** (`createParagraphBullets`) — this shifts indices
4. **Apply heading styles** by re-reading the document for actual positions, matching paragraphs by their text content (emoji prefixes for H4, "TOPIC" for H2, "SHOW DOC" for H1)
5. **Apply hyperlinks** by re-reading the document again and scanning text runs for URLs

This order is critical because `createParagraphBullets` shifts document indices, and heading styles applied before bullets will land on wrong paragraphs or get inherited by adjacent empty lines.

## Automation
This process runs **automatically every morning at 7 AM Bangkok time** via macOS launchd + Claude Code headless mode. See `skills/DAILY_SHOWDOC_AUTOMATION_SOP.md` for:
- How the automation works (launchd + pmset + `claude -p`)
- Management commands (pause, resume, test, check logs)
- Troubleshooting
- How to modify the prompt

Manual run: `bash scripts/launch_showdoc.sh`

## Timing
- Viral Radar runs at 7 AM Bangkok (midnight UTC)
- Show doc automation fires at 7 AM Bangkok (runs ~15-20 min)
- Show doc should be ready by ~7:30 AM Bangkok
- Filming typically follows shortly after
