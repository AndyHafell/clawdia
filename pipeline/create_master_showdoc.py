#!/usr/bin/env python3
"""
Create a master Show Doc Google Doc with tabs for each day.
Uses the Google Docs API to create a document with multiple tabs.
Pulls existing content from Feb 18 and Feb 19 docs, adds Feb 24 content.
"""

import pickle, json, requests, os

# --- Config ---
TOKEN_PATH = "youtube_token.pickle"
FEB18_DOC_ID = "YOUR_EXISTING_DOC_ID_1"
FEB19_DOC_ID = "YOUR_EXISTING_DOC_ID_2"

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

# --- Step 1: Create a new Google Doc with the Docs API ---
print("Step 1: Creating master Google Doc with tabs...")

create_body = {
    "title": "YOUR_CHANNEL_NAME — Master Show Doc",
    "tabs": [
        {
            "tabProperties": {
                "title": "Feb 24, 2026"
            }
        }
    ]
}

resp = requests.post(
    "https://docs.googleapis.com/v1/documents",
    headers=headers,
    json=create_body
)

if resp.status_code not in (200, 201):
    print(f"ERROR creating doc: {resp.status_code}")
    print(resp.text[:1000])
    exit(1)

doc_data = resp.json()
doc_id = doc_data["documentId"]
doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
print(f"Master doc created: {doc_url}")

# Get the tab ID for the first tab (Feb 24)
first_tab_id = doc_data["tabs"][0]["tabProperties"]["tabId"]
print(f"First tab ID (Feb 24): {first_tab_id}")

# --- Step 2: Add tabs for Feb 18 and Feb 19 ---
print("\nStep 2: Adding additional tabs...")

# Add Feb 19 tab
add_tab_requests = [
    {
        "addDocumentTab": {
            "tabProperties": {
                "title": "Feb 19, 2026"
            }
        }
    },
    {
        "addDocumentTab": {
            "tabProperties": {
                "title": "Feb 18, 2026"
            }
        }
    }
]

resp = requests.post(
    f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate",
    headers=headers,
    json={"requests": add_tab_requests}
)

feb19_tab_id = None
feb18_tab_id = None

if resp.status_code != 200:
    print(f"ERROR adding tabs: {resp.status_code}")
    print(resp.text[:1000])
    exit(1)
else:
    print("Tabs added successfully")
    tab_replies = resp.json().get("replies", [])
    # Try multiple reply key formats
    for i, reply in enumerate(tab_replies):
        tab_props = (
            reply.get("addDocumentTab", {}).get("tabProperties", {}) or
            reply.get("addTab", {}).get("tabProperties", {})
        )
        tab_id = tab_props.get("tabId", "")
        if i == 0:
            feb19_tab_id = tab_id
            print(f"Feb 19 tab ID: {feb19_tab_id}")
        elif i == 1:
            feb18_tab_id = tab_id
            print(f"Feb 18 tab ID: {feb18_tab_id}")

    if not feb19_tab_id or not feb18_tab_id:
        # Fallback: re-read the document to get all tab IDs
        print("Fetching tab IDs from document...")
        doc_resp = requests.get(
            f"https://docs.googleapis.com/v1/documents/{doc_id}?includeTabsContent=true",
            headers={"Authorization": f"Bearer {creds.token}"}
        )
        if doc_resp.status_code == 200:
            tabs = doc_resp.json().get("tabs", [])
            for tab in tabs:
                tp = tab.get("tabProperties", {})
                title = tp.get("title", "")
                tid = tp.get("tabId", "")
                print(f"  Tab: {title} -> {tid}")
                if "19" in title:
                    feb19_tab_id = tid
                elif "18" in title:
                    feb18_tab_id = tid

# --- Step 3: Pull content from existing docs ---
print("\nStep 3: Pulling content from existing show docs...")

def get_doc_text(doc_id):
    """Pull all text from a Google Doc."""
    resp = requests.get(
        f"https://docs.googleapis.com/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {creds.token}"}
    )
    if resp.status_code != 200:
        print(f"ERROR reading doc {doc_id}: {resp.status_code}")
        return ""

    doc = resp.json()
    text = ""
    body = doc.get("body", {})
    for elem in body.get("content", []):
        if "paragraph" in elem:
            for pe in elem["paragraph"].get("elements", []):
                if "textRun" in pe:
                    text += pe["textRun"]["content"]
    return text

feb18_text = get_doc_text(FEB18_DOC_ID)
feb19_text = get_doc_text(FEB19_DOC_ID)

print(f"Feb 18 text length: {len(feb18_text)} chars")
print(f"Feb 19 text length: {len(feb19_text)} chars")

# --- Step 4: Write content to tabs ---
print("\nStep 4: Writing content to tabs...")

# Feb 24 content (our new show doc)
FEB24_CONTENT = """SHOW DOC — February 24, 2026
3 Topics | YOUR_CHANNEL_NAME Livestream

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOPIC 1 — GEMINI 3.1 PRO + ANTIGRAVITY: THE FREE AI IDE THAT BUILDS ENTIRE APPS
Format: New Tool Build-Along
Outlier Score: 3.4x | 96K views | Source: [Source Creator]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ TITLES (7 options — pick 1 before filming)
* Google's Free AI IDE Just Destroyed Every Web Designer (Live Build) ← primary
* I Built a Full Website in 10 Minutes with Google's New AI (Gemini 3.1 Pro)
* Google AntiGravity + Gemini 3.1 Pro: The AI IDE You Need to Try RIGHT NOW
* Forget Cursor — Google Just Made a FREE AI Coding Agent (AntiGravity Demo)
* Gemini 3.1 Pro Inside AntiGravity is Insane (Full Build-Along)
* Google's Secret Weapon: The Free AI IDE Nobody's Talking About
* I Tested Google AntiGravity for 24 Hours — Here's What Happened

🖼️ THUMBNAIL IDEAS
* Concept A: [Creator] looking shocked at a split screen — blank VS Code on left, fully built website on right. Text: "FREE" in orange gradient
* Concept B: AntiGravity Mission Control dashboard screenshot with [Creator]'s face overlaid, mouth open. Text: "GOOGLE'S SECRET" in orange

🎤 SAY THIS (word-for-word intro — read this aloud):
"Google just quietly released what might be the most powerful free AI coding tool on the planet. It's called AntiGravity, and with Gemini 3.1 Pro — which just scored 77% on ARC-AGI-2, more than double the previous version — it can run multiple AI agents in parallel to build, test, and ship entire applications while you just watch. Today I'm going to build a complete project live using this thing, and by the end you'll have it set up and running on your machine too."

📊 4P FRAMEWORK
Proof: Gemini 3.1 Pro scored 77.1% on ARC-AGI-2 — more than double the reasoning of Gemini 3 Pro. AntiGravity is free in public preview with unlimited completions.
Promise: By the end, you'll have AntiGravity installed and will have built a complete project live with multiple AI agents working in parallel.
Problem: If you're still using Cursor or VS Code with Copilot, you're paying monthly for a single-agent experience while Google is giving away a multi-agent IDE for free.
Path: Install AntiGravity → Tour the Mission Control and Editor views → Build a project from scratch with Gemini 3.1 Pro → Test it live → Show the advanced tricks.

🎣 HOOKS (pick 1 before filming — then go)
* How to: How to build a full web app without writing a single line of code using Google's free AI IDE
* Statement: Google just made Cursor irrelevant — and it's completely free
* Benefit: After this video, you'll never pay for an AI coding tool again
* Fact: Gemini 3.1 Pro just doubled its reasoning score — and it's free inside Google's new IDE
* Negative: If you're still paying for Cursor, you're wasting your money — here's why
* Personal/Emotional: I almost didn't believe it when I saw what this thing could do for free
* Story: Last week I was paying $20/month for AI coding. Then I found this.

🎯 TRANSFORMATION GOAL:
"By the end of this video, you will have Google AntiGravity installed on your machine with Gemini 3.1 Pro, and you'll have built your first complete project using multiple AI agents working in parallel."

📋 WALKTHROUGH

STEP 1 — The Paradigm Shift: Why This Changes Everything
🗣️ Say: "Most AI coding tools give you one assistant. AntiGravity gives you an entire team. One agent plans, one codes, one tests, one browses — all running in parallel while you orchestrate from what Google calls Mission Control. And it's free."
🖥️ Show: Open AntiGravity's homepage, show the Mission Control interface screenshot
🔗 Link: https://antigravity.google/ — "This is Google's official AntiGravity page — let me show you what we're working with"

STEP 2 — Install AntiGravity + Pick Your Model
🗣️ Say: "Installation takes about 2 minutes. You download it, sign in with your Google account, and you're in. The free tier gives you unlimited tab completions and unlimited commands. If you have Google AI Pro or Ultra, you get priority rate limits — but free is more than enough to follow along."
🖥️ Show: Download AntiGravity, walk through the install process, sign in with Google account
🔗 Link: https://antigravity.google/pricing — "Here's the pricing page — see, individual plan is $0/month"

STEP 3 — Tour the Two Views: Manager vs. Editor
🗣️ Say: "AntiGravity has two modes. Manager View is your Mission Control — this is where you spawn agents, monitor their progress, and see their artifacts. Editor View is the VS Code-like experience where you can edit files directly and give inline commands to the AI. Think of Manager as the CEO view and Editor as the developer view."
🖥️ Show: Switch between Manager View (Mission Control dashboard) and Editor View (VS Code-like interface). Point out the agent sidebar, artifact panel, and workspace folders.

STEP 4 — Launch Your First Agent Task
🗣️ Say: "Let's build something real. I'm going to tell AntiGravity to build me a full landing page with a contact form, a hero section, and responsive design. Watch how it breaks this into subtasks and assigns agents automatically."
🖥️ Show: Type the prompt into the Manager View, watch agents spin up
📋 Prompt: "Build a modern landing page for an AI automation agency. Include: hero section with gradient background, 3 service cards, client testimonials section, contact form with email validation, responsive mobile design. Use HTML, CSS, and vanilla JS."

STEP 5 — Watch the Agents Work (Artifacts + Feedback)
🗣️ Say: "This is the magic part. See these artifacts appearing? That's the agents showing you their work — task lists, implementation plans, screenshots. You can leave comments directly on any artifact, like commenting on a Google Doc, and the agent adjusts without stopping."
🖥️ Show: Artifacts panel populating with task breakdowns, code previews, and screenshots. Demonstrate leaving a comment like "make the gradient more orange" on an artifact.

STEP 6 — Test It Live + Review the Output
🗣️ Say: "Let's preview what it built. I'm going to open this in the browser and see if it actually works — the contact form, the responsiveness, everything."
🖥️ Show: Open the built project in the browser, test the contact form, resize the window to show responsive design, inspect the code quality in Editor View

STEP 7 — Power User Tricks: Gemini 3.1 Pro's New Thinking Modes
🗣️ Say: "One feature most people don't know about — Gemini 3.1 Pro has three thinking levels: low, medium, and high. Low is fast for simple tasks, medium is the sweet spot for most builds, and high is for complex reasoning where you need the AI to really think. This is like having a turbo button for your AI."
🖥️ Show: Toggle between thinking levels in settings, demonstrate a complex task with high thinking mode enabled
🔗 Link: https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-pro/ — "Google's official blog post on 3.1 Pro — I'll link this in the description"

STEP 8 — Where to Take It Next
🗣️ Say: "Now that you've got this running, here's where it gets crazy. You can connect NotebookLM inside AntiGravity, use Google Stitch for design-to-code, and even use it with Claude Sonnet and GPT models — it's not locked to Gemini. The free tier is generous enough to build real projects."
🖥️ Show: Quick tour of model selection (show Claude, GPT options), mention NotebookLM integration

📖 SUMMARY (background only — don't read during stream)
The details: Google launched AntiGravity as an agent-first IDE that goes beyond traditional coding assistants. Instead of one AI pair-programmer, it provides a Mission Control interface where multiple agents work in parallel — one plans, one codes, one tests, one browses. Gemini 3.1 Pro, released February 19, 2026, powers it with a 1M token context window, 77.1% ARC-AGI-2 score (double the previous version), and three-tier thinking modes (low/medium/high). The free tier includes unlimited completions and commands with weekly rate limits. Paid Google AI Pro/Ultra subscribers get 5-hour rolling rate limits.
Why it matters: AntiGravity is a direct competitor to Cursor, Windsurf, and other paid AI IDEs — but it's free. It also supports third-party models (Claude Sonnet, GPT-OSS), making it the most flexible free AI coding environment available. The multi-agent approach is a fundamental shift from single-agent tools.
Key stats/quotes: Gemini 3.1 Pro: 77.1% ARC-AGI-2 (ranked #1 on Artificial Analysis with Intelligence Index score of 57). 1M token context, 64K output tokens. API pricing: $2 input/$12 output per million tokens. Some users report latency spikes during high demand (up to 104 seconds). Mixed reception — strong reasoning but some feel creative/emotional depth reduced vs. Gemini 3.0.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOPIC 2 — CLAUDE CODE IS TURNING NON-CODERS INTO SOFTWARE COMPANIES
Format: Opportunity Strategy Play
Multiple viral videos (10K-14K views each) | Sources: [Source Creator], [Source Creator], AI Workshop
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ TITLES (7 options — pick 1 before filming)
* Non-Coders Are Building $10K/Month Software Businesses with Claude Code (Here's How) ← primary
* Claude Code Just Made 6-Figure Software Businesses Free to Start
* How to Build and Sell SaaS Without Writing Code (Claude Code Strategy)
* The $0 to $10K/Month AI Software Business Blueprint (2026)
* Claude Code is Creating a New Type of Millionaire — Here's the Playbook
* I Built a SaaS in 4 Hours for $20 — The AI Business Nobody Sees Coming
* 5 Claude Code Business Models That Pay $5K-$50K/Month (No Coding Required)

🖼️ THUMBNAIL IDEAS
* Concept A: Terminal screen showing Claude Code with dollar signs overlaid. [Creator] pointing at it, surprised face. Text: "$10K/mo" in orange gradient
* Concept B: Split image — "Before" (confused person staring at code) vs. "After" (polished SaaS dashboard). Text: "NO CODE" crossed out, replaced with "CLAUDE CODE"

🎤 SAY THIS (word-for-word intro — read this aloud):
"Claude Code just hit 29 million daily installs and Anthropic is now worth 380 billion dollars. But here's what nobody's talking about — regular people with zero coding experience are using this tool to build and sell real software businesses. One guy built a production SaaS in 4 hours for 20 bucks. Agencies that used to charge 50K for custom software are watching non-coders do it in a weekend. Today I'm going to show you the 5 business models that are actually working, and by the end you'll have picked your niche and know exactly what to build first."

📊 4P FRAMEWORK
Proof: Claude Code: 29M daily installs, $2.5B annual revenue. Developers report 26-55% productivity gains. Solo builders shipping production SaaS in hours, not months. Anthropic valued at $380B.
Promise: You'll leave with a specific niche, a business model, and a first action to take this week — no coding experience needed.
Problem: The window is open right now. Non-coders who move fast are building software businesses that used to require a team. If you wait, the market gets saturated.
Path: 5 proven business models → live demo building a micro-SaaS → niche selection formula → your first action plan.

🎣 HOOKS (pick 1 before filming — then go)
* How to: How to build a $10K/month software business without knowing how to code
* Statement: The easiest path to a six-figure business in 2026 doesn't require coding — it requires Claude Code
* Benefit: After this video, you'll have a complete blueprint for building software you can sell — even if you've never written a line of code
* Fact: Claude Code now has 29 million daily installs — and non-coders are building real businesses with it
* Negative: If you're still thinking you need to learn to code to build software, you're already behind
* Personal/Emotional: Six months ago, I couldn't have imagined showing someone with zero tech skills how to build a SaaS — now I'm doing it every week
* Story: A subscriber messaged me last week saying he built a SaaS in a weekend using Claude Code and already has 3 paying customers

🎯 TRANSFORMATION GOAL:
"By the end of this video, you will have picked a specific niche for your AI software business, chosen one of the 5 business models, and have a first action to take this week."

📋 WALKTHROUGH

INTRO MOVE — The Credibility Proof
🗣️ Say: "Let me show you the numbers that made me stop everything and make this video. Claude Code went from 17.7 million to 29 million daily installs in weeks. Anthropic just raised 30 billion at a 380 billion dollar valuation. Sequoia Capital literally published an essay called 'This Is AGI.' The tools are here. The question is: what do you build with them?"
🖥️ Show: Open the Anthropic funding article, Sequoia essay headline, Claude Code install graph
🔗 Link: https://sequoiacap.com/article/2026-this-is-agi/ — "Sequoia Capital literally called this 'AGI' — look at this"

POINT 1 — AI Micro-SaaS Builder ($2K-$10K/month)
🗣️ Say: "The first model is the simplest. Find a boring problem in a specific niche, build a small tool that solves it with Claude Code, charge 29 to 99 dollars a month. One developer built a production multi-tenant SaaS with billing, auth, and analytics in under two months. The key is picking a niche so specific that the big players ignore it."
🖥️ Show: Example of a niche micro-SaaS (e.g., client intake form for med spas, invoice tracker for freelancers)
🔗 Link: https://glaveski.medium.com/i-built-a-useful-saas-in-4-hours-for-20-using-claude-code-75e3e5630093 — "This guy built a SaaS in 4 hours for 20 dollars — let me show you"

POINT 2 — AI Automation Agency ($5K-$50K/month)
🗣️ Say: "Model two is the AI automation agency. You don't sell AI — you sell finished solutions to specific industries. Real estate agents need automated listing management. Law firms need document processing. Healthcare needs patient onboarding. You build it with Claude Code and n8n, charge a setup fee of 2,500 to 15,000 dollars, plus a monthly retainer."
🖥️ Show: Quick overview of agency model — show n8n workflow as example deliverable
🔗 Link: https://www.hakunamatatatech.com/our-resources/blog/ai-agents-in-b2b — "Here's the breakdown of the agency model"

POINT 3 — GEO (Generative Engine Optimization) Service ($3K-$8K/month per client)
🗣️ Say: "This one is brand new and almost nobody is doing it yet. GEO — Generative Engine Optimization. Instead of optimizing for Google search, you optimize businesses to get cited by ChatGPT, Claude, and Perplexity. ChatGPT alone has 800 million weekly active users. Claude Code can audit a website's AI visibility in minutes and generate the exact changes needed. This is the next SEO."
🖥️ Show: Open a GEO tool or guide, show what an AI citation looks like vs. a Google result
🔗 Link: https://searchengineland.com/mastering-generative-engine-optimization-in-2026-full-guide-469142 — "This is the best guide I've found on GEO"

POINT 4 — Content Repurposing Studio ($2K-$10K/month)
🗣️ Say: "Model four is a content repurposing studio. Creators and businesses have long-form content sitting there doing nothing. You use Claude Code to build a pipeline that takes one podcast episode and turns it into 20 pieces of content — blog posts, social threads, email sequences, short-form scripts. Low startup cost, massive demand from creators."
🖥️ Show: Quick demo of a repurposing workflow — transcript in, multiple outputs

POINT 5 — Claude Cowork Setup Consultant ($1K-$5K per engagement)
🗣️ Say: "The newest opportunity. Claude Cowork just launched — it brings Claude Code's power to non-technical knowledge workers on desktop. Companies need someone to set up their plugins, customize workflows, and train their teams. This is the equivalent of the early IT consultant who helped offices set up computers. Except now you're helping them set up AI workers."
🖥️ Show: Open Claude Cowork product page, show the plugin library
🔗 Link: https://claude.com/product/cowork — "Claude Cowork just launched and most businesses have no idea this exists"

LIVE BUILD — Quick Demo: Build a Niche Micro-SaaS with Claude Code
🗣️ Say: "Let me show you how fast this actually is. I'm going to build a simple client intake tool for a med spa right now in Claude Code. Watch how I describe what I want in plain English and it builds the entire thing."
🖥️ Show: Open terminal, launch Claude Code, build a simple intake form tool live
📋 Prompt: "Build a client intake web app for a med spa. It needs: a beautiful form with fields for name, email, phone, treatment interest (dropdown: Botox, Fillers, Laser, Facial), preferred date/time, and a notes field. When submitted, save to a JSON file and send a confirmation email summary. Use a clean, professional design with a calming color palette. Include form validation."

NICHE SELECTION FORMULA — How to Pick Yours
🗣️ Say: "Here's the formula: Pick an industry with high manual overhead, high transaction value, and low AI adoption. Real estate, legal, healthcare, financial services — these are goldmines. Then pick ONE problem in that niche and solve it better than anyone else. Don't be an 'AI agency.' Be 'the team that automates patient intake for med spas.' That's how you charge premium prices."
🖥️ Show: Write the formula on screen: High Manual Overhead + High Transaction Value + Low AI Adoption = Perfect Niche

📖 SUMMARY (background only — don't read during stream)
The details: Claude Code has exploded from 17.7M to 29M daily installs since early 2026. Anthropic raised $30B at a $380B valuation. Claude Opus 4.6 launched Feb 5, 2026 with improved coding, planning, and agentic capabilities. Claude Cowork launched Jan 2026 (Windows Feb 10) bringing agentic AI to non-technical knowledge workers. Solo developers are building production SaaS in hours — one built a multi-tenant SaaS with billing in under 2 months, another shipped an MVP in 4 hours for $20.
Why it matters: The barrier to building software businesses has collapsed. Non-coders can now ship production software using Claude Code's agentic capabilities. The AI automation agency market is projected to grow rapidly with agencies launching at $2K-$5K capital and scaling to $5K-$50K/month. New service categories like GEO are emerging. Claude Cowork creates an entirely new consulting market for non-technical setup.
Key stats/quotes: Claude Code: 29M daily installs, $2.5B annual revenue. Anthropic: 300K+ business customers, $380B valuation. Enterprise productivity gains: 26-55%. Claude Cowork: launched Jan 2026, plugins for productivity, sales, finance. 500+ companies spend $1M+/year on Anthropic products.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOPIC 3 — SEQUOIA SAYS AGI IS HERE. ARE THEY RIGHT? (AND WHAT TO DO ABOUT IT)
Format: Deep Dive Report
59K views | Source: [Source Creator]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ TITLES (7 options — pick 1 before filming)
* Sequoia Capital Says AGI Is Here — I Investigated (And It Changes Everything) ← primary
* The Biggest AI Claim of 2026: "This Is AGI" — Is It Real?
* AGI Just Arrived (According to the Smartest Money in Tech)
* I Read Sequoia's "This Is AGI" Essay — Here's What They Actually Mean
* The AGI Debate Is Over. Here's What Happens Next.
* Why 2026 Is the Year AI Becomes Your Coworker (Sequoia Report Breakdown)
* From Talkers to Doers: The AI Shift That Changes Your Career

🖼️ THUMBNAIL IDEAS
* Concept A: [Creator] holding a paper that says "AGI" with a magnifying glass over it. Sequoia Capital logo visible. Text: "IS IT REAL?" in orange gradient
* Concept B: Timeline graphic from "Talkers" (2023) to "Doers" (2026) with [Creator]'s face in the middle. Text: "AGI IS HERE" in orange

🎤 SAY THIS (word-for-word intro — read this aloud):
"Sequoia Capital — the most legendary venture capital firm on the planet, the people who backed Apple, Google, and OpenAI — just published an essay titled 'This Is AGI.' Not 'AGI is coming.' Not 'AGI might happen.' THIS. IS. AGI. Meanwhile, Dario Amodei from Anthropic says cognitive abilities are doubling every 4 to 12 months, and he used the phrase 'white-collar bloodbath' at Davos. Today I'm going to break down what they actually mean, whether they're right, and most importantly — what you should be doing about it right now."

📊 4P FRAMEWORK
Proof: Sequoia Capital published "2026: This Is AGI." Dario Amodei (Anthropic CEO) predicts AGI by 2026-2027. AI market: $514B in 2026, on track for $4.8T by 2033. AI funding hit $225.8B in 2025 — doubling YoY.
Promise: You'll know exactly whether AGI is real, what it means for your career, and the specific steps to take this month to stay ahead.
Problem: Amodei said "white-collar bloodbath" — up to 50% of entry-level office jobs at risk in 1-5 years. If you're not repositioning now, you're the one who gets displaced.
Path: The Sequoia essay → what they mean by AGI → the evidence for and against → the real job impact → your action plan.

🎣 HOOKS (pick 1 before filming — then go)
* How to: How to prepare for AGI now that the smartest investors say it's already here
* Statement: Sequoia Capital just declared AGI — and they've been right about every major tech shift for 50 years
* Benefit: After this video, you'll have a clear action plan for the AGI era, whether it's hype or reality
* Fact: AI funding hit $225 billion last year and Sequoia says we've already reached AGI — here's what that means for you
* Negative: Ignoring the AGI conversation is the most dangerous thing you can do for your career right now
* Personal/Emotional: When Sequoia Capital — the firm behind Apple and Google — says "This Is AGI," I stop everything and pay attention
* Story: I read this essay three times. By the second read, I started reorganizing my entire business.

🎯 TRANSFORMATION GOAL:
"By the end of this video, you will know exactly whether AGI is real or hype, understand what it means for your career and business, and have 3 specific actions to take this month."

📋 WALKTHROUGH

ACT 1 — Open with the Bomb: Sequoia's Declaration
🗣️ Say: "Let me show you something that dropped a few weeks ago that should have been front-page news everywhere. Sequoia Capital — Pat Grady and Sonya Huang — published this essay called 'This Is AGI.' Their definition is elegant: AGI is the ability to figure things out. Baseline knowledge, reasoning, and the ability to iterate to the answer. And they say we're there."
🖥️ Show: Open the Sequoia essay, scroll through the key sections
🔗 Link: https://sequoiacap.com/article/2026-this-is-agi/ — "Read along with me — this is the actual essay"

ACT 2 — What They Actually Mean: The Three Ingredients
🗣️ Say: "Sequoia breaks AGI down into three ingredients. First, baseline knowledge from pre-training — that's the foundation. Second, the ability to reason, which is inference-time compute — thinking harder about problems. And third, the ability to iterate, which is what they call long-horizon agents. Claude Code, coding agents that can work for hours autonomously — that's the third ingredient, and that just arrived."
🖥️ Show: Write the 3 ingredients on screen: Pre-training + Reasoning + Long-Horizon Agents = AGI

ACT 3 — The Evidence: METR's Exponential Graph
🗣️ Say: "Here's the data that convinced me this isn't hype. METR — a research organization that tracks AI capability — shows that AI's ability to complete long-horizon tasks is doubling every 7 months. If you trace this forward: agents handle a full day's work by 2028, a full year by 2034. This is exponential, and we're at the knee of the curve."
🖥️ Show: METR's capability graph showing exponential doubling

ACT 4 — The Skeptics: Why Smart People Disagree
🗣️ Say: "But not everyone agrees. Analysis from multiple sources puts the probability of AGI by 2027 at only 10 to 20 percent. Critics say current AI has fundamental weaknesses — it can't truly reason about novel situations, it hallucinates, and the word 'AGI' has become so stretched that it's almost meaningless. Sam Altman himself called AGI 'not a super useful term' because everyone defines it differently."
🖥️ Show: Open the skeptic articles side by side with the Sequoia essay
🔗 Link: https://waleedk.medium.com/agi-is-a-long-ways-off-d5f1c07526e4 — "Here's one of the best skeptic takes I found"

ACT 5 — The Job Impact: Amodei's "White-Collar Bloodbath"
🗣️ Say: "Whether or not we call it AGI, here's what's real. At Davos 2026, Dario Amodei used the phrase 'white-collar bloodbath.' He said AI could threaten up to 50 percent of entry-level office jobs within 1 to 5 years. Cognitive abilities are doubling every 4 to 12 months. The AI market is 514 billion dollars this year and projected to hit 4.8 trillion by 2033. The train has left the station."
🖥️ Show: Open the WEF 2026 / Davos quotes, show the AI market growth chart
🔗 Link: https://www.contextstudios.ai/blog/wef-2026-what-the-most-powerful-ai-leaders-say-about-agi-jobs-and-the-future-of-humanity — "Here's everything the AI leaders said at Davos"

ACT 6 — The Shift: From Talkers to Doers
🗣️ Say: "Here's the sentence from Sequoia that stuck with me. 'The AI applications of 2023 and 2024 were talkers. The AI applications of 2026 and 2027 will be doers.' That's the shift. AI is going from chatbots that talk to agents that work. Claude Code, AntiGravity, Claude Cowork — these are the first generation of doers. And usage will go from a few times a day to all day, every day, with multiple instances running in parallel."
🖥️ Show: Side-by-side of "2023: ChatGPT chatbot" vs "2026: Claude Code building software"

ACT 7 — The Verdict + Your 3 Action Steps
🗣️ Say: "My verdict: whether you call it AGI or not doesn't matter. What matters is that AI just crossed a capability threshold where it can do real work autonomously. Here are your three action steps for this month. One: pick up one AI tool and use it every day for a real task — Claude Code, AntiGravity, Claude Cowork. Two: identify one part of your job that's repetitive and automate it this week. Three: start building a side project with AI. Not to learn AI — to prove to yourself and the market that you can ship things that used to require a team."
🖥️ Show: Write the 3 actions on screen: 1. Pick a tool. 2. Automate one task. 3. Build a side project.

📖 SUMMARY (background only — don't read during stream)
The details: Sequoia Capital published "2026: This Is AGI" in January 2026, defining AGI as "the ability to figure things out" via pre-training + reasoning + long-horizon agents. METR research shows AI task completion doubling every 7 months. At WEF Davos 2026, Dario Amodei (Anthropic) warned of a "white-collar bloodbath" with 50% of entry-level office jobs at risk. Sam Altman called AGI "not a super useful term." Skeptics put AGI probability at 10-20% by 2027.
Why it matters: Regardless of the AGI label debate, AI has crossed a practical capability threshold. Tools like Claude Code, AntiGravity, and Claude Cowork represent the shift from "talkers" to "doers." AI funding hit $225.8B in 2025 (doubling YoY). The global AI market is $514B in 2026, projected to reach $4.8T by 2033. This is the biggest economic shift since the internet, and people who act now have a significant first-mover advantage.
Key stats/quotes: Sequoia: "Long-horizon agents are functionally AGI." Amodei: "white-collar bloodbath," cognitive abilities doubling every 4-12 months. AI market: $514B (2026) → $4.8T (2033). AI funding: $225.8B in 2025. METR: agent capability doubling every 7 months. Jensen Huang predicts AGI by 2029.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BONUS — EXTRA TOPIC IDEAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OpenClaw Goes Free: Stephen G Pope Built a $0 Alternative (No Mac Mini)
Outlier Score: N/A | 35,845 views | Feb 22, 2026 | https://youtube.com/watch?v=8uP2IrP3IG8

NotebookLM + AntiGravity Superpower Combo — Jack Roberts' Take
Outlier Score: N/A | 10,936 views | Feb 23, 2026 | https://youtube.com/watch?v=UwyUHOq1hIA

Anthropic Launches Claude Code Security — AI-Powered Vulnerability Scanner (500+ bugs found)
Released Feb 2026 | Enterprise & Team plans | https://thehackernews.com/2026/02/anthropic-launches-claude-code-security.html

India AI Summit 2026: Altman and Amodei's Awkward Handshake Moment (+ What They Actually Said)
Feb 19, 2026 | Modi, Altman, Amodei, Jensen Huang all present | https://techcrunch.com/2026/02/19/altman-and-amodei-share-a-moment-of-awkwardness-at-indias-big-ai-summit/

GEO Conference 2026 — Generative Engine Optimization Is Becoming Its Own Industry
New conference launched 2026 | GEO as the "next SEO" | https://www.geo-conference.com/

Claude Cowork on Windows: The AI Desktop Assistant for Non-Coders Just Went Cross-Platform
Feb 10, 2026 | Full feature parity with macOS | https://claude.com/product/cowork

Matt Wolfe's Honest Take on Gemini 3.1 Pro — "Mostly Great" with Caveats
Outlier Score: N/A | 4,478 views | Feb 22, 2026 | https://youtube.com/watch?v=MRoPpP_yEw0

Best AI Workflows for Business Research & Monitoring (AI Workshop Deep Dive)
Outlier Score: N/A | 3,619 views | Feb 21, 2026 | https://youtube.com/watch?v=NniDh-fYyHs
"""


def insert_text_to_tab(doc_id, tab_id, text, headers):
    """Insert text into a specific tab of a Google Doc."""
    requests_body = [
        {
            "insertText": {
                "location": {
                    "segmentId": "",
                    "index": 1,
                    "tabId": tab_id
                },
                "text": text
            }
        }
    ]

    resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate",
        headers=headers,
        json={"requests": requests_body}
    )
    return resp


# Insert Feb 24 content
print("\nInserting Feb 24 content...")
resp = insert_text_to_tab(doc_id, first_tab_id, FEB24_CONTENT, headers)
if resp.status_code == 200:
    print("Feb 24 content inserted successfully!")
else:
    print(f"Error: {resp.status_code}")
    print(resp.text[:500])

# Insert Feb 19 content
if feb19_text:
    print("\nInserting Feb 19 content...")
    resp = insert_text_to_tab(doc_id, feb19_tab_id, feb19_text, headers)
    if resp.status_code == 200:
        print("Feb 19 content inserted successfully!")
    else:
        print(f"Error: {resp.status_code}")
        print(resp.text[:500])

# Insert Feb 18 content
if feb18_text:
    print("\nInserting Feb 18 content...")
    resp = insert_text_to_tab(doc_id, feb18_tab_id, feb18_text, headers)
    if resp.status_code == 200:
        print("Feb 18 content inserted successfully!")
    else:
        print(f"Error: {resp.status_code}")
        print(resp.text[:500])

# --- Create Airtable Record ---
print("\nCreating Airtable record...")
at_headers = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

at_data = {
    "records": [{
        "fields": {
            "Title": "Show Doc — Feb 24, 2026",
            "Date": "2026-02-24",
            "Google Doc URL": doc_url,
            "Status": "Draft",
            "Topic 1": "Gemini 3.1 Pro + AntiGravity",
            "Topic 1 Format": "New Tool Build-Along",
            "Topic 1 Outlier Score": 3.4,
            "Topic 2": "Claude Code Business Models",
            "Topic 2 Format": "Opportunity Strategy Play",
            "Topic 3": "AGI Is Here (Sequoia)",
            "Topic 3 Format": "Deep Dive Report"
        }
    }]
}

at_resp = requests.post(
    f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{SHOW_DOCS_TABLE}",
    headers=at_headers,
    json=at_data
)

if at_resp.status_code == 200:
    print("Airtable record created!")
    print(f"Record ID: {at_resp.json()['records'][0]['id']}")
else:
    print(f"Airtable: {at_resp.status_code}")
    print(at_resp.text[:500])

print(f"\n{'='*60}")
print(f"MASTER SHOW DOC: {doc_url}")
print(f"{'='*60}")
print(f"\nTabs:")
print(f"  - Feb 24, 2026 (today's show doc)")
print(f"  - Feb 19, 2026 (migrated)")
print(f"  - Feb 18, 2026 (migrated)")
