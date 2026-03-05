#!/usr/bin/env python3
"""Format the Feb 24 show doc tab with pastel blue minimal styling + bullets."""

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

DOC_ID = "YOUR_SHOW_DOC_MASTER_ID"
TAB_ID = "t.0"

# ===== PASTEL BLUE MINIMAL PALETTE =====
DARK_BLUE = {"red": 0.11, "green": 0.27, "blue": 0.53}       # #1C4587 deep blue for h2 text
MEDIUM_BLUE = {"red": 0.24, "green": 0.47, "blue": 0.85}     # #3D78D8 section headers
LIGHT_BLUE_BG = {"red": 0.85, "green": 0.92, "blue": 1.0}    # #D9EBFF pastel blue backgrounds
VERY_LIGHT_BLUE = {"red": 0.93, "green": 0.96, "blue": 1.0}  # #EDF5FF very subtle blue tint
PASTEL_BLUE_BORDER = {"red": 0.40, "green": 0.60, "blue": 0.90}  # softer blue for borders
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}
DARK_TEXT = {"red": 0.13, "green": 0.13, "blue": 0.13}        # near-black for body
GRAY_TEXT = {"red": 0.45, "green": 0.45, "blue": 0.45}        # subtle gray for meta
LIGHT_GRAY_BG = {"red": 0.95, "green": 0.96, "blue": 0.97}   # code/prompt bg
STEP_BLUE = {"red": 0.17, "green": 0.38, "blue": 0.68}       # step title accent

# ===== CONTENT BLOCKS =====
# Types: h1, subtitle, h2, meta, h3, bullet, bullet_bold, quote, bold_label,
#         prompt, step_title, normal

blocks = [
    # ---- HEADER ----
    ("SHOW DOC — February 24, 2026\n", "h1"),
    ("3 Topics  |  YOUR_CHANNEL_NAME Livestream\n\n", "subtitle"),

    # ======== TOPIC 1 ========
    ("TOPIC 1 — GEMINI 3.1 PRO + ANTIGRAVITY: THE FREE AI IDE THAT BUILDS ENTIRE APPS\n", "h2"),
    ("Format: New Tool Build-Along  |  Outlier Score: 3.4x  |  96K views  |  Source: [Source Creator]\n\n", "meta"),

    ("📺 SOURCES\n", "h3"),
    ("[Source Creator] — \"AntiGravity: Google's Free AI IDE That Builds Entire Apps\" | 96K views | Feb 21, 2026 | https://youtube.com/watch?v=example_saraev\n", "source"),
    ("Google Blog — \"Introducing Gemini 3.1 Pro\" | Feb 19, 2026 | https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-pro/\n", "source"),
    ("AntiGravity Official — Product page + pricing | https://antigravity.google/\n\n", "source"),

    ("🏷️ TITLES (7 options — pick 1 before filming)\n", "h3"),
    ("Google's Free AI IDE Just Destroyed Every Web Designer (Live Build) ← primary\n", "bullet_bold"),
    ("I Built a Full Website in 10 Minutes with Google's New AI (Gemini 3.1 Pro)\n", "bullet"),
    ("Google AntiGravity + Gemini 3.1 Pro: The AI IDE You Need to Try RIGHT NOW\n", "bullet"),
    ("Forget Cursor — Google Just Made a FREE AI Coding Agent (AntiGravity Demo)\n", "bullet"),
    ("Gemini 3.1 Pro Inside AntiGravity is Insane (Full Build-Along)\n", "bullet"),
    ("Google's Secret Weapon: The Free AI IDE Nobody's Talking About\n", "bullet"),
    ("I Tested Google AntiGravity for 24 Hours — Here's What Happened\n\n", "bullet"),

    ("🖼️ THUMBNAIL IDEAS\n", "h3"),
    ("Concept A: [Creator] looking shocked at split screen — blank VS Code on left, fully built website on right. Text: \"FREE\" in orange gradient\n", "bullet"),
    ("Concept B: AntiGravity Mission Control dashboard with [Creator]'s face overlaid. Text: \"GOOGLE'S SECRET\" in orange\n\n", "bullet"),

    ("🎤 SAY THIS (word-for-word intro — read this aloud):\n", "h3"),
    ("\"Google just quietly released what might be the most powerful free AI coding tool on the planet. It's called AntiGravity, and with Gemini 3.1 Pro — which just scored 77% on ARC-AGI-2, more than double the previous version — it can run multiple AI agents in parallel to build, test, and ship entire applications while you just watch. Today I'm going to build a complete project live using this thing, and by the end you'll have it set up and running on your machine too.\"\n\n", "quote"),

    ("📊 4P FRAMEWORK\n", "h3"),
    ("Proof: Gemini 3.1 Pro scored 77.1% on ARC-AGI-2 — more than double Gemini 3 Pro. AntiGravity is free in public preview with unlimited completions.\n", "bold_label"),
    ("Promise: By the end, you'll have AntiGravity installed and will have built a complete project live with multiple AI agents working in parallel.\n", "bold_label"),
    ("Problem: If you're still using Cursor or VS Code with Copilot, you're paying monthly for a single-agent experience while Google is giving away a multi-agent IDE for free.\n", "bold_label"),
    ("Path: Install AntiGravity → Tour Mission Control and Editor views → Build from scratch → Test live → Advanced tricks.\n\n", "bold_label"),

    ("🎣 HOOKS (pick 1 before filming — then go)\n", "h3"),
    ("How to: How to build a full web app without writing a single line of code using Google's free AI IDE\n", "bullet"),
    ("Statement: Google just made Cursor irrelevant — and it's completely free\n", "bullet"),
    ("Benefit: After this video, you'll never pay for an AI coding tool again\n", "bullet"),
    ("Fact: Gemini 3.1 Pro just doubled its reasoning score — and it's free inside Google's new IDE\n", "bullet"),
    ("Negative: If you're still paying for Cursor, you're wasting your money — here's why\n", "bullet"),
    ("Personal/Emotional: I almost didn't believe it when I saw what this thing could do for free\n", "bullet"),
    ("Story: Last week I was paying $20/month for AI coding. Then I found this.\n\n", "bullet"),

    ("🎯 TRANSFORMATION GOAL:\n", "h3"),
    ("\"By the end of this video, you will have Google AntiGravity installed on your machine with Gemini 3.1 Pro, and you'll have built your first complete project using multiple AI agents working in parallel.\"\n\n", "quote"),

    ("📋 WALKTHROUGH\n", "h3"),

    ("STEP 1 — The Paradigm Shift: Why This Changes Everything\n", "step_title"),
    ("🗣️ Say: \"Most AI coding tools give you one assistant. AntiGravity gives you an entire team. One agent plans, one codes, one tests, one browses — all running in parallel while you orchestrate from what Google calls Mission Control. And it's free.\"\n", "normal"),
    ("🖥️ Show: Open AntiGravity's homepage, show the Mission Control interface screenshot\n", "normal"),
    ("🔗 Link: https://antigravity.google/ — \"This is Google's official AntiGravity page\"\n\n", "normal"),

    ("STEP 2 — Install AntiGravity + Pick Your Model\n", "step_title"),
    ("🗣️ Say: \"Installation takes about 2 minutes. Download it, sign in with Google, and you're in. Free tier = unlimited completions and commands.\"\n", "normal"),
    ("🖥️ Show: Download AntiGravity, walk through install, sign in with Google account\n", "normal"),
    ("🔗 Link: https://antigravity.google/pricing — \"Individual plan is $0/month\"\n\n", "normal"),

    ("STEP 3 — Tour the Two Views: Manager vs. Editor\n", "step_title"),
    ("🗣️ Say: \"Manager View = Mission Control (spawn agents, monitor progress). Editor View = VS Code-like (edit files, inline commands). Manager = CEO view, Editor = developer view.\"\n", "normal"),
    ("🖥️ Show: Switch between Manager View and Editor View. Point out agent sidebar, artifact panel, workspace folders.\n\n", "normal"),

    ("STEP 4 — Launch Your First Agent Task\n", "step_title"),
    ("🗣️ Say: \"Let's build something real. I'm telling AntiGravity to build a full landing page. Watch how it breaks this into subtasks and assigns agents automatically.\"\n", "normal"),
    ("🖥️ Show: Type the prompt into Manager View, watch agents spin up\n", "normal"),
    ("📋 Prompt: \"Build a modern landing page for an AI automation agency. Include: hero section with gradient background, 3 service cards, client testimonials section, contact form with email validation, responsive mobile design. Use HTML, CSS, and vanilla JS.\"\n\n", "prompt"),

    ("STEP 5 — Watch the Agents Work (Artifacts + Feedback)\n", "step_title"),
    ("🗣️ Say: \"See these artifacts? The agents show you task lists, code previews, screenshots. You can comment directly on any artifact — like a Google Doc — and the agent adjusts without stopping.\"\n", "normal"),
    ("🖥️ Show: Artifacts panel populating. Demonstrate leaving a comment like \"make the gradient more orange\".\n\n", "normal"),

    ("STEP 6 — Test It Live + Review the Output\n", "step_title"),
    ("🗣️ Say: \"Let's preview what it built — the contact form, the responsiveness, everything.\"\n", "normal"),
    ("🖥️ Show: Open project in browser, test form, resize window, inspect code quality.\n\n", "normal"),

    ("STEP 7 — Power User Tricks: Gemini 3.1 Pro's New Thinking Modes\n", "step_title"),
    ("🗣️ Say: \"Gemini 3.1 Pro has three thinking levels: low, medium, and high. Low = fast, medium = sweet spot, high = complex reasoning. Like a turbo button for your AI.\"\n", "normal"),
    ("🖥️ Show: Toggle thinking levels, demo a complex task with high thinking mode.\n", "normal"),
    ("🔗 Link: https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-pro/\n\n", "normal"),

    ("STEP 8 — Where to Take It Next\n", "step_title"),
    ("🗣️ Say: \"Connect NotebookLM inside AntiGravity, use Google Stitch for design-to-code, and use Claude Sonnet and GPT models too — it's not locked to Gemini.\"\n", "normal"),
    ("🖥️ Show: Model selection (Claude, GPT options), mention NotebookLM integration.\n\n", "normal"),

    ("📖 SUMMARY (background only — don't read during stream)\n", "h3"),
    ("The details: Google launched AntiGravity as an agent-first IDE. Multiple agents work in parallel — one plans, one codes, one tests, one browses. Gemini 3.1 Pro (Feb 19, 2026): 1M token context, 77.1% ARC-AGI-2 (2x previous), three-tier thinking modes. Free tier: unlimited completions, weekly rate limits.\n", "normal"),
    ("Why it matters: Free competitor to Cursor/Windsurf. Supports Claude Sonnet + GPT-OSS. Multi-agent = fundamental shift.\n", "normal"),
    ("Key stats: 77.1% ARC-AGI-2 (#1 on Artificial Analysis, score 57). 1M context, 64K output. API: $2/$12 per M tokens. Some latency spikes reported.\n\n", "normal"),

    # ======== TOPIC 2 ========
    ("TOPIC 2 — CLAUDE CODE IS TURNING NON-CODERS INTO SOFTWARE COMPANIES\n", "h2"),
    ("Format: Opportunity Strategy Play  |  Multiple viral videos (10K-14K views)  |  Sources: [Source Creator], [Source Creator], AI Workshop\n\n", "meta"),

    ("📺 SOURCES\n", "h3"),
    ("[Source Creator] — \"My Plan to Automate 70% of my Business w/ Claude Code (in 30 Days)\" | 14K views | Feb 22, 2026 | https://youtube.com/@LiamOttley\n", "source"),
    ("[Source Creator] — \"How I'd Make Money with AI in 2026 (if I had to Start Over)\" | 10K views | Feb 2026 | https://youtube.com/@example-channel\n", "source"),
    ("AI Workshop — \"Best AI Workflows for Business Research & Monitoring\" | 3.6K views | Feb 21, 2026 | https://youtube.com/watch?v=NniDh-fYyHs\n", "source"),
    ("Steve Glaveski — \"I Built a Useful SaaS in 4 Hours for $20 Using Claude Code\" (Medium article) | https://glaveski.medium.com/i-built-a-useful-saas-in-4-hours-for-20-using-claude-code-75e3e5630093\n\n", "source"),

    ("🏷️ TITLES (7 options — pick 1 before filming)\n", "h3"),
    ("Non-Coders Are Building $10K/Month Software Businesses with Claude Code (Here's How) ← primary\n", "bullet_bold"),
    ("Claude Code Just Made 6-Figure Software Businesses Free to Start\n", "bullet"),
    ("How to Build and Sell SaaS Without Writing Code (Claude Code Strategy)\n", "bullet"),
    ("The $0 to $10K/Month AI Software Business Blueprint (2026)\n", "bullet"),
    ("Claude Code is Creating a New Type of Millionaire — Here's the Playbook\n", "bullet"),
    ("I Built a SaaS in 4 Hours for $20 — The AI Business Nobody Sees Coming\n", "bullet"),
    ("5 Claude Code Business Models That Pay $5K-$50K/Month (No Coding Required)\n\n", "bullet"),

    ("🖼️ THUMBNAIL IDEAS\n", "h3"),
    ("Concept A: Terminal with Claude Code + dollar signs. [Creator] pointing, surprised. Text: \"$10K/mo\" in orange\n", "bullet"),
    ("Concept B: Before/After split — confused at code vs. polished SaaS dashboard. Text: \"CLAUDE CODE\" in orange\n\n", "bullet"),

    ("🎤 SAY THIS (word-for-word intro — read this aloud):\n", "h3"),
    ("\"Claude Code just hit 29 million daily installs and Anthropic is now worth 380 billion dollars. But here's what nobody's talking about — regular people with zero coding experience are using this tool to build and sell real software businesses. One guy built a production SaaS in 4 hours for 20 bucks. Agencies that used to charge 50K for custom software are watching non-coders do it in a weekend. Today I'm going to show you the 5 business models that are actually working, and by the end you'll have picked your niche and know exactly what to build first.\"\n\n", "quote"),

    ("📊 4P FRAMEWORK\n", "h3"),
    ("Proof: Claude Code: 29M daily installs, $2.5B annual revenue. 26-55% productivity gains. Solo builders shipping SaaS in hours. Anthropic valued at $380B.\n", "bold_label"),
    ("Promise: You'll leave with a specific niche, a business model, and a first action to take this week.\n", "bold_label"),
    ("Problem: Non-coders who move fast are building software businesses that used to require a team. The window is open now.\n", "bold_label"),
    ("Path: 5 proven business models → live demo → niche selection formula → action plan.\n\n", "bold_label"),

    ("🎣 HOOKS (pick 1 before filming — then go)\n", "h3"),
    ("How to: How to build a $10K/month software business without knowing how to code\n", "bullet"),
    ("Statement: The easiest path to six figures in 2026 doesn't require coding — it requires Claude Code\n", "bullet"),
    ("Benefit: Complete blueprint for building software you can sell — even if you've never written a line of code\n", "bullet"),
    ("Fact: Claude Code now has 29 million daily installs — and non-coders are building real businesses with it\n", "bullet"),
    ("Negative: If you still think you need to learn to code to build software, you're already behind\n", "bullet"),
    ("Personal/Emotional: Six months ago, I couldn't imagine showing a non-coder how to build a SaaS — now I do it weekly\n", "bullet"),
    ("Story: A subscriber built a SaaS in a weekend with Claude Code and already has 3 paying customers\n\n", "bullet"),

    ("🎯 TRANSFORMATION GOAL:\n", "h3"),
    ("\"By the end of this video, you will have picked a specific niche for your AI software business, chosen one of the 5 business models, and have a first action to take this week.\"\n\n", "quote"),

    ("📋 WALKTHROUGH\n", "h3"),

    ("INTRO MOVE — The Credibility Proof\n", "step_title"),
    ("🗣️ Say: \"Claude Code went from 17.7M to 29M daily installs in weeks. Anthropic raised $30B at $380B valuation. Sequoia published 'This Is AGI.' The tools are here — what do you build with them?\"\n", "normal"),
    ("🖥️ Show: Anthropic funding article, Sequoia essay, Claude Code install graph\n", "normal"),
    ("🔗 Link: https://sequoiacap.com/article/2026-this-is-agi/\n\n", "normal"),

    ("POINT 1 — AI Micro-SaaS Builder ($2K-$10K/month)\n", "step_title"),
    ("🗣️ Say: \"Find a boring problem in a specific niche, build a small tool, charge $29-$99/mo. One dev built a multi-tenant SaaS with billing in under 2 months.\"\n", "normal"),
    ("🔗 Link: https://glaveski.medium.com/i-built-a-useful-saas-in-4-hours-for-20-using-claude-code-75e3e5630093\n\n", "normal"),

    ("POINT 2 — AI Automation Agency ($5K-$50K/month)\n", "step_title"),
    ("🗣️ Say: \"Don't sell AI — sell finished solutions. Real estate, law firms, healthcare. Build with Claude Code + n8n. Setup fee $2.5K-$15K + monthly retainer.\"\n", "normal"),
    ("🔗 Link: https://www.hakunamatatatech.com/our-resources/blog/ai-agents-in-b2b\n\n", "normal"),

    ("POINT 3 — GEO Service ($3K-$8K/month per client)\n", "step_title"),
    ("🗣️ Say: \"GEO — Generative Engine Optimization. Optimize businesses to get cited by ChatGPT, Claude, Perplexity. ChatGPT alone: 800M weekly users. Almost nobody doing this yet.\"\n", "normal"),
    ("🔗 Link: https://searchengineland.com/mastering-generative-engine-optimization-in-2026-full-guide-469142\n\n", "normal"),

    ("POINT 4 — Content Repurposing Studio ($2K-$10K/month)\n", "step_title"),
    ("🗣️ Say: \"Take one podcast episode, turn it into 20 pieces of content. Low startup cost, massive creator demand.\"\n\n", "normal"),

    ("POINT 5 — Claude Cowork Setup Consultant ($1K-$5K per engagement)\n", "step_title"),
    ("🗣️ Say: \"Claude Cowork just launched for non-technical knowledge workers. Companies need setup + training. You're the early IT consultant for AI workers.\"\n", "normal"),
    ("🔗 Link: https://claude.com/product/cowork\n\n", "normal"),

    ("LIVE BUILD — Quick Demo: Build a Niche Micro-SaaS\n", "step_title"),
    ("🗣️ Say: \"Watch how I describe what I want in plain English and Claude Code builds the entire thing.\"\n", "normal"),
    ("📋 Prompt: \"Build a client intake web app for a med spa. Fields: name, email, phone, treatment interest (dropdown: Botox, Fillers, Laser, Facial), preferred date/time, notes. Save to JSON, send confirmation email. Clean design, calming colors, form validation.\"\n\n", "prompt"),

    ("NICHE SELECTION FORMULA\n", "step_title"),
    ("🗣️ Say: \"High Manual Overhead + High Transaction Value + Low AI Adoption = Perfect Niche. Don't be an 'AI agency.' Be 'the team that automates patient intake for med spas.'\"\n\n", "normal"),

    ("📖 SUMMARY (background only — don't read during stream)\n", "h3"),
    ("The details: Claude Code 17.7M→29M daily installs. Anthropic $30B raise, $380B valuation. Opus 4.6 (Feb 5). Cowork launched Jan 2026 (Windows Feb 10). Solo devs shipping SaaS in hours.\n", "normal"),
    ("Why it matters: Barrier to software businesses collapsed. Agency market growing. GEO emerging. Cowork = new consulting market.\n", "normal"),
    ("Key stats: 29M installs, $2.5B revenue, 300K+ business customers. 26-55% productivity gains. 500+ companies spend $1M+/yr.\n\n", "normal"),

    # ======== TOPIC 3 ========
    ("TOPIC 3 — SEQUOIA SAYS AGI IS HERE. ARE THEY RIGHT? (AND WHAT TO DO ABOUT IT)\n", "h2"),
    ("Format: Deep Dive Report  |  59K views  |  Source: [Source Creator]\n\n", "meta"),

    ("📺 SOURCES\n", "h3"),
    ("[Source Creator] — \"Sequoia Just Said AGI Is Here\" | 59K views | Feb 2026 | https://youtube.com/@LiamOttley\n", "source"),
    ("Sequoia Capital — \"2026: This Is AGI\" (essay) | Jan 2026 | https://sequoiacap.com/article/2026-this-is-agi/\n", "source"),
    ("Context Studios — \"WEF 2026: What AI Leaders Say About AGI, Jobs, and the Future\" | https://www.contextstudios.ai/blog/wef-2026-what-the-most-powerful-ai-leaders-say-about-agi-jobs-and-the-future-of-humanity\n", "source"),
    ("Waleed K — \"AGI Is a Long Ways Off\" (skeptic view) | https://waleedk.medium.com/agi-is-a-long-ways-off-d5f1c07526e4\n\n", "source"),

    ("🏷️ TITLES (7 options — pick 1 before filming)\n", "h3"),
    ("Sequoia Capital Says AGI Is Here — I Investigated (And It Changes Everything) ← primary\n", "bullet_bold"),
    ("The Biggest AI Claim of 2026: \"This Is AGI\" — Is It Real?\n", "bullet"),
    ("AGI Just Arrived (According to the Smartest Money in Tech)\n", "bullet"),
    ("I Read Sequoia's \"This Is AGI\" Essay — Here's What They Actually Mean\n", "bullet"),
    ("The AGI Debate Is Over. Here's What Happens Next.\n", "bullet"),
    ("Why 2026 Is the Year AI Becomes Your Coworker (Sequoia Report Breakdown)\n", "bullet"),
    ("From Talkers to Doers: The AI Shift That Changes Your Career\n\n", "bullet"),

    ("🖼️ THUMBNAIL IDEAS\n", "h3"),
    ("Concept A: [Creator] holding paper that says \"AGI\" with magnifying glass. Sequoia logo. Text: \"IS IT REAL?\" in orange\n", "bullet"),
    ("Concept B: Timeline from \"Talkers\" (2023) to \"Doers\" (2026) with [Creator]'s face. Text: \"AGI IS HERE\" in orange\n\n", "bullet"),

    ("🎤 SAY THIS (word-for-word intro — read this aloud):\n", "h3"),
    ("\"Sequoia Capital — the most legendary venture capital firm on the planet, the people who backed Apple, Google, and OpenAI — just published an essay titled 'This Is AGI.' Not 'AGI is coming.' Not 'AGI might happen.' THIS. IS. AGI. Meanwhile, Dario Amodei from Anthropic says cognitive abilities are doubling every 4 to 12 months, and he used the phrase 'white-collar bloodbath' at Davos. Today I'm going to break down what they actually mean, whether they're right, and most importantly — what you should be doing about it right now.\"\n\n", "quote"),

    ("📊 4P FRAMEWORK\n", "h3"),
    ("Proof: Sequoia published \"2026: This Is AGI.\" Amodei predicts AGI 2026-2027. AI market: $514B in 2026 → $4.8T by 2033. AI funding: $225.8B in 2025.\n", "bold_label"),
    ("Promise: Know whether AGI is real, what it means for your career, and specific steps to take this month.\n", "bold_label"),
    ("Problem: Amodei said \"white-collar bloodbath\" — 50% of entry-level office jobs at risk in 1-5 years.\n", "bold_label"),
    ("Path: Sequoia essay → what AGI means → evidence for and against → job impact → action plan.\n\n", "bold_label"),

    ("🎣 HOOKS (pick 1 before filming — then go)\n", "h3"),
    ("How to: How to prepare for AGI now that the smartest investors say it's already here\n", "bullet"),
    ("Statement: Sequoia Capital just declared AGI — and they've been right about every major tech shift for 50 years\n", "bullet"),
    ("Benefit: Clear action plan for the AGI era, whether it's hype or reality\n", "bullet"),
    ("Fact: AI funding hit $225B last year and Sequoia says we've reached AGI\n", "bullet"),
    ("Negative: Ignoring the AGI conversation is the most dangerous thing for your career right now\n", "bullet"),
    ("Personal/Emotional: When Sequoia says \"This Is AGI,\" I stop everything and pay attention\n", "bullet"),
    ("Story: I read this essay three times. By the second read, I started reorganizing my entire business.\n\n", "bullet"),

    ("🎯 TRANSFORMATION GOAL:\n", "h3"),
    ("\"By the end of this video, you will know exactly whether AGI is real or hype, understand what it means for your career and business, and have 3 specific actions to take this month.\"\n\n", "quote"),

    ("📋 WALKTHROUGH\n", "h3"),

    ("ACT 1 — Open with the Bomb: Sequoia's Declaration\n", "step_title"),
    ("🗣️ Say: \"Sequoia's Pat Grady and Sonya Huang published 'This Is AGI.' Their definition: AGI is the ability to figure things out. Baseline knowledge + reasoning + iteration. They say we're there.\"\n", "normal"),
    ("🔗 Link: https://sequoiacap.com/article/2026-this-is-agi/\n\n", "normal"),

    ("ACT 2 — The Three Ingredients\n", "step_title"),
    ("🗣️ Say: \"Pre-training (knowledge) + inference-time compute (reasoning) + long-horizon agents (iteration). Claude Code = the third ingredient. That just arrived.\"\n\n", "normal"),

    ("ACT 3 — The Evidence: METR's Exponential Graph\n", "step_title"),
    ("🗣️ Say: \"METR shows AI task completion doubling every 7 months. Agents handle a full day's work by 2028, a year by 2034. We're at the knee of the curve.\"\n\n", "normal"),

    ("ACT 4 — The Skeptics\n", "step_title"),
    ("🗣️ Say: \"10-20% probability of AGI by 2027 per multiple analyses. AI can't truly reason about novel situations. Sam Altman called AGI 'not a super useful term.'\"\n", "normal"),
    ("🔗 Link: https://waleedk.medium.com/agi-is-a-long-ways-off-d5f1c07526e4\n\n", "normal"),

    ("ACT 5 — The Job Impact\n", "step_title"),
    ("🗣️ Say: \"Amodei at Davos: 'white-collar bloodbath.' 50% of entry-level office jobs at risk in 1-5 years. AI market: $514B this year → $4.8T by 2033.\"\n", "normal"),
    ("🔗 Link: https://www.contextstudios.ai/blog/wef-2026-what-the-most-powerful-ai-leaders-say-about-agi-jobs-and-the-future-of-humanity\n\n", "normal"),

    ("ACT 6 — From Talkers to Doers\n", "step_title"),
    ("🗣️ Say: \"Sequoia: 'The AI applications of 2023-2024 were talkers. 2026-2027 will be doers.' Claude Code, AntiGravity, Cowork = first generation of doers.\"\n\n", "normal"),

    ("ACT 7 — The Verdict + 3 Action Steps\n", "step_title"),
    ("🗣️ Say: \"1. Pick one AI tool, use it daily. 2. Automate one repetitive task this week. 3. Build a side project with AI — prove you can ship.\"\n\n", "normal"),

    ("📖 SUMMARY (background only — don't read during stream)\n", "h3"),
    ("The details: Sequoia \"2026: This Is AGI\" (Jan 2026). METR: task completion doubling every 7 months. Amodei at Davos: \"white-collar bloodbath,\" 50% entry-level jobs at risk. Altman: AGI \"not a super useful term.\"\n", "normal"),
    ("Why it matters: AI crossed a practical capability threshold. Funding $225.8B (2025). Market $514B (2026) → $4.8T (2033).\n", "normal"),
    ("Key stats: Sequoia: \"Long-horizon agents are functionally AGI.\" METR: doubling every 7 months. Jensen Huang: AGI by 2029.\n\n", "normal"),

    # ======== BONUS ========
    ("BONUS — EXTRA TOPIC IDEAS\n", "h2"),
    ("OpenClaw Goes Free — Stephen G Pope built a $0 alternative (no Mac Mini) | 35,845 views | Feb 22 | https://youtube.com/watch?v=8uP2IrP3IG8\n", "bullet"),
    ("NotebookLM + AntiGravity Superpower Combo — Jack Roberts | 10,936 views | Feb 23 | https://youtube.com/watch?v=UwyUHOq1hIA\n", "bullet"),
    ("Claude Code Security — AI vulnerability scanner (500+ bugs found) | Feb 2026 | https://thehackernews.com/2026/02/anthropic-launches-claude-code-security.html\n", "bullet"),
    ("India AI Summit 2026 — Altman & Amodei awkward handshake + what they said | Feb 19 | https://techcrunch.com/2026/02/19/altman-and-amodei-share-a-moment-of-awkwardness-at-indias-big-ai-summit/\n", "bullet"),
    ("GEO Conference 2026 — Generative Engine Optimization becomes its own industry | https://www.geo-conference.com/\n", "bullet"),
    ("Claude Cowork on Windows — AI desktop assistant goes cross-platform | Feb 10 | https://claude.com/product/cowork\n", "bullet"),
    ("Matt Wolfe's Honest Take on Gemini 3.1 Pro — \"Mostly Great\" | 4,478 views | Feb 22 | https://youtube.com/watch?v=MRoPpP_yEw0\n", "bullet"),
    ("Best AI Workflows for Business Research & Monitoring — AI Workshop | 3,619 views | Feb 21 | https://youtube.com/watch?v=NniDh-fYyHs\n", "bullet"),
]

# ===== STEP 1: Clear existing content =====
print("Step 1: Reading current doc to get content length...")
doc_resp = requests.get(
    f"https://docs.googleapis.com/v1/documents/{DOC_ID}?includeTabsContent=true",
    headers=headers
)
doc_data = doc_resp.json()

# Find the Feb 24 tab content
tab_content = None
for tab in doc_data.get("tabs", []):
    if tab.get("tabProperties", {}).get("tabId") == TAB_ID:
        tab_content = tab.get("documentTab", {}).get("body", {}).get("content", [])
        break

if tab_content:
    last_elem = tab_content[-1]
    end_index = last_elem.get("endIndex", 1)
    if end_index > 2:
        print(f"  Clearing existing content (end index: {end_index})...")
        clear_resp = requests.post(
            f"https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate",
            headers=headers,
            json={"requests": [{
                "deleteContentRange": {
                    "range": {"startIndex": 1, "endIndex": end_index - 1, "tabId": TAB_ID}
                }
            }]}
        )
        if clear_resp.status_code != 200:
            print(f"  Warning: Clear failed: {clear_resp.status_code}")
            print(clear_resp.text[:500])
    else:
        print("  Tab is already empty.")
else:
    print("  Could not find tab content, continuing anyway...")

# ===== STEP 2: Insert all text =====
print("Step 2: Inserting text content...")
all_text = ""
for text, _ in blocks:
    all_text += text

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
    print(f"ERROR inserting text: {insert_resp.status_code}")
    print(insert_resp.text[:500])
    exit(1)
print(f"  Inserted {len(all_text)} characters.")

# ===== STEP 3: Build and apply text/paragraph formatting =====
print("Step 3: Building formatting requests...")
BATCH_SIZE = 150
style_requests = []   # text styles, paragraph styles (safe — don't shift indices)
bullet_requests = []  # createParagraphBullets (shifts indices — applied after styles)
# Note: heading namedStyleType applied in Step 5b by re-reading actual doc positions
current_index = 1

for text, style in blocks:
    start = current_index
    end = start + len(text)

    if style == "h1":
        # namedStyleType applied in Step 5b using actual positions (after bullets)
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
                "textStyle": {
                    "foregroundColor": {"color": {"rgbColor": DARK_BLUE}},
                    "fontSize": {"magnitude": 20, "unit": "PT"}
                },
                "fields": "foregroundColor,fontSize"
            }
        })

    elif style == "subtitle":
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT", "alignment": "CENTER"},
                "fields": "namedStyleType,alignment"
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "textStyle": {
                    "foregroundColor": {"color": {"rgbColor": GRAY_TEXT}},
                    "fontSize": {"magnitude": 11, "unit": "PT"},
                    "italic": True
                },
                "fields": "foregroundColor,fontSize,italic"
            }
        })

    elif style == "h2":
        # namedStyleType applied in Step 5b using actual positions (after bullets)
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "paragraphStyle": {
                    "shading": {"backgroundColor": {"color": {"rgbColor": LIGHT_BLUE_BG}}},
                    "spaceAbove": {"magnitude": 20, "unit": "PT"}
                },
                "fields": "shading.backgroundColor,spaceAbove"
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "textStyle": {
                    "foregroundColor": {"color": {"rgbColor": DARK_BLUE}},
                    "bold": True,
                    "fontSize": {"magnitude": 14, "unit": "PT"}
                },
                "fields": "foregroundColor,bold,fontSize"
            }
        })

    elif style == "meta":
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "fields": "namedStyleType"
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "textStyle": {
                    "foregroundColor": {"color": {"rgbColor": GRAY_TEXT}},
                    "italic": True,
                    "fontSize": {"magnitude": 9, "unit": "PT"}
                },
                "fields": "foregroundColor,italic,fontSize"
            }
        })

    elif style == "h3":
        # H4 heading — namedStyleType applied in Step 5b using actual positions
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "paragraphStyle": {
                    "spaceAbove": {"magnitude": 14, "unit": "PT"},
                    "borderBottom": {
                        "color": {"color": {"rgbColor": LIGHT_BLUE_BG}},
                        "width": {"magnitude": 1, "unit": "PT"},
                        "padding": {"magnitude": 4, "unit": "PT"},
                        "dashStyle": "SOLID"
                    }
                },
                "fields": "spaceAbove,borderBottom"
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "textStyle": {
                    "foregroundColor": {"color": {"rgbColor": MEDIUM_BLUE}},
                    "bold": True,
                    "fontSize": {"magnitude": 11, "unit": "PT"}
                },
                "fields": "foregroundColor,bold,fontSize"
            }
        })

    elif style == "source":
        # Source items — bullet + small gray text, bold creator name
        bullet_requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "textStyle": {
                    "fontSize": {"magnitude": 9, "unit": "PT"},
                    "foregroundColor": {"color": {"rgbColor": GRAY_TEXT}}
                },
                "fields": "fontSize,foregroundColor"
            }
        })
        dash_pos = text.find("—")
        if dash_pos > 0:
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": start, "endIndex": start + dash_pos, "tabId": TAB_ID},
                    "textStyle": {
                        "bold": True,
                        "foregroundColor": {"color": {"rgbColor": DARK_TEXT}}
                    },
                    "fields": "bold,foregroundColor"
                }
            })

    elif style == "bullet" or style == "bullet_bold":
        bullet_requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
            }
        })
        text_style = {"fontSize": {"magnitude": 10, "unit": "PT"}}
        fields = "fontSize"
        if style == "bullet_bold":
            text_style["bold"] = True
            text_style["foregroundColor"] = {"color": {"rgbColor": DARK_BLUE}}
            fields = "fontSize,bold,foregroundColor"
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "textStyle": text_style,
                "fields": fields
            }
        })

    elif style == "quote":
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "paragraphStyle": {
                    "namedStyleType": "NORMAL_TEXT",
                    "shading": {"backgroundColor": {"color": {"rgbColor": VERY_LIGHT_BLUE}}},
                    "indentFirstLine": {"magnitude": 18, "unit": "PT"},
                    "indentStart": {"magnitude": 18, "unit": "PT"},
                    "indentEnd": {"magnitude": 18, "unit": "PT"},
                    "borderLeft": {
                        "color": {"color": {"rgbColor": PASTEL_BLUE_BORDER}},
                        "width": {"magnitude": 3, "unit": "PT"},
                        "padding": {"magnitude": 8, "unit": "PT"},
                        "dashStyle": "SOLID"
                    },
                    "spaceAbove": {"magnitude": 6, "unit": "PT"},
                    "spaceBelow": {"magnitude": 6, "unit": "PT"}
                },
                "fields": "namedStyleType,shading.backgroundColor,indentFirstLine,indentStart,indentEnd,borderLeft,spaceAbove,spaceBelow"
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "textStyle": {
                    "italic": True,
                    "foregroundColor": {"color": {"rgbColor": DARK_TEXT}}
                },
                "fields": "italic,foregroundColor"
            }
        })

    elif style == "bold_label":
        colon_pos = text.find(":")
        if colon_pos > 0:
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": start, "endIndex": start + colon_pos + 1, "tabId": TAB_ID},
                    "textStyle": {
                        "bold": True,
                        "foregroundColor": {"color": {"rgbColor": DARK_BLUE}}
                    },
                    "fields": "bold,foregroundColor"
                }
            })
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "paragraphStyle": {
                    "namedStyleType": "NORMAL_TEXT",
                    "shading": {"backgroundColor": {"color": {"rgbColor": VERY_LIGHT_BLUE}}},
                    "indentStart": {"magnitude": 10, "unit": "PT"},
                    "spaceAbove": {"magnitude": 2, "unit": "PT"},
                    "spaceBelow": {"magnitude": 2, "unit": "PT"}
                },
                "fields": "namedStyleType,shading.backgroundColor,indentStart,spaceAbove,spaceBelow"
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "textStyle": {"fontSize": {"magnitude": 10, "unit": "PT"}},
                "fields": "fontSize"
            }
        })

    elif style == "prompt":
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "paragraphStyle": {
                    "namedStyleType": "NORMAL_TEXT",
                    "shading": {"backgroundColor": {"color": {"rgbColor": LIGHT_GRAY_BG}}},
                    "indentStart": {"magnitude": 18, "unit": "PT"},
                    "indentEnd": {"magnitude": 18, "unit": "PT"},
                    "spaceAbove": {"magnitude": 4, "unit": "PT"},
                    "spaceBelow": {"magnitude": 4, "unit": "PT"}
                },
                "fields": "namedStyleType,shading.backgroundColor,indentStart,indentEnd,spaceAbove,spaceBelow"
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "textStyle": {
                    "weightedFontFamily": {"fontFamily": "Roboto Mono"},
                    "fontSize": {"magnitude": 9, "unit": "PT"},
                    "foregroundColor": {"color": {"rgbColor": DARK_TEXT}}
                },
                "fields": "weightedFontFamily,fontSize,foregroundColor"
            }
        })

    elif style == "step_title":
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "paragraphStyle": {
                    "namedStyleType": "NORMAL_TEXT",
                    "spaceAbove": {"magnitude": 12, "unit": "PT"},
                    "borderLeft": {
                        "color": {"color": {"rgbColor": MEDIUM_BLUE}},
                        "width": {"magnitude": 3, "unit": "PT"},
                        "padding": {"magnitude": 6, "unit": "PT"},
                        "dashStyle": "SOLID"
                    }
                },
                "fields": "namedStyleType,spaceAbove,borderLeft"
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "textStyle": {
                    "bold": True,
                    "fontSize": {"magnitude": 11, "unit": "PT"},
                    "foregroundColor": {"color": {"rgbColor": STEP_BLUE}}
                },
                "fields": "bold,fontSize,foregroundColor"
            }
        })

    elif style == "normal":
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "fields": "namedStyleType"
            }
        })
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end, "tabId": TAB_ID},
                "textStyle": {
                    "fontSize": {"magnitude": 10, "unit": "PT"},
                    "foregroundColor": {"color": {"rgbColor": DARK_TEXT}}
                },
                "fields": "fontSize,foregroundColor"
            }
        })

    current_index = end

# Send style requests (text + paragraph formatting — doesn't shift indices)
print(f"  Applying {len(style_requests)} style requests...")
for i in range(0, len(style_requests), BATCH_SIZE):
    batch = style_requests[i:i+BATCH_SIZE]
    batch_num = (i // BATCH_SIZE) + 1
    total_batches = (len(style_requests) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"  Sending style batch {batch_num}/{total_batches} ({len(batch)} requests)...")
    fmt_resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate",
        headers=headers,
        json={"requests": batch}
    )
    if fmt_resp.status_code != 200:
        print(f"  ERROR in style batch {batch_num}: {fmt_resp.status_code}")
        print(fmt_resp.text[:1000])
        exit(1)

# ===== STEP 5: Apply bullet formatting =====
print(f"Step 5: Applying {len(bullet_requests)} bullet requests...")
if bullet_requests:
    for i in range(0, len(bullet_requests), BATCH_SIZE):
        batch = bullet_requests[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(bullet_requests) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Sending bullet batch {batch_num}/{total_batches} ({len(batch)} requests)...")
        bul_resp = requests.post(
            f"https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate",
            headers=headers,
            json={"requests": batch}
        )
        if bul_resp.status_code != 200:
            print(f"  ERROR in bullet batch {batch_num}: {bul_resp.status_code}")
            print(bul_resp.text[:1000])
            exit(1)

# ===== STEP 5b: Apply heading styles by re-reading document (actual positions) =====
# After bullets, indices shift. So we re-read the doc, find headings by text content,
# and apply the correct namedStyleType based on what each paragraph actually says.
print("Step 5b: Applying heading styles using actual document positions...")

H1_PREFIXES = ["SHOW DOC"]
H2_PREFIXES = ["TOPIC 1", "TOPIC 2", "TOPIC 3", "BONUS"]
H4_PREFIXES = ["📺", "🏷", "🖼", "🎤", "📊", "🎣", "🎯", "📖"]
# 📋 needs special handling: only "📋 WALKTHROUGH" is H4, not "📋 Prompt"
H4_WALKTHROUGH = "📋 WALKTHROUGH"

doc_resp_hdg = requests.get(
    f"https://docs.googleapis.com/v1/documents/{DOC_ID}?includeTabsContent=true",
    headers=headers
)
doc_data_hdg = doc_resp_hdg.json()
heading_fix_requests = []

for tab in doc_data_hdg.get("tabs", []):
    if tab.get("tabProperties", {}).get("tabId") == TAB_ID:
        content = tab.get("documentTab", {}).get("body", {}).get("content", [])
        for elem in content:
            para = elem.get("paragraph", {})
            text_parts = []
            for pe in para.get("elements", []):
                tr = pe.get("textRun", {})
                text_parts.append(tr.get("content", ""))
            full_text = "".join(text_parts).strip()
            if not full_text:
                continue

            start_idx = elem.get("startIndex", 0)
            end_idx = elem.get("endIndex", 0)
            if start_idx >= end_idx:
                continue

            target_style = None

            # Check H1
            for prefix in H1_PREFIXES:
                if full_text.startswith(prefix):
                    target_style = "HEADING_1"
                    break

            # Check H2
            if not target_style:
                for prefix in H2_PREFIXES:
                    if full_text.startswith(prefix):
                        target_style = "HEADING_2"
                        break

            # Check H4 (emoji section headers)
            if not target_style:
                for prefix in H4_PREFIXES:
                    if full_text.startswith(prefix):
                        target_style = "HEADING_4"
                        break
                # Special case: 📋 WALKTHROUGH only (not 📋 Prompt)
                if not target_style and full_text.startswith(H4_WALKTHROUGH):
                    target_style = "HEADING_4"

            if target_style:
                ps = para.get("paragraphStyle", {})
                current_style = ps.get("namedStyleType", "")
                if current_style != target_style:
                    extra_fields = ""
                    extra_style = {}
                    if target_style == "HEADING_1":
                        extra_style = {"alignment": "CENTER"}
                        extra_fields = ",alignment"
                    elif target_style == "HEADING_2":
                        extra_style = {
                            "shading": {"backgroundColor": {"color": {"rgbColor": LIGHT_BLUE_BG}}},
                            "spaceAbove": {"magnitude": 20, "unit": "PT"}
                        }
                        extra_fields = ",shading.backgroundColor,spaceAbove"
                    elif target_style == "HEADING_4":
                        extra_style = {
                            "spaceAbove": {"magnitude": 14, "unit": "PT"},
                            "borderBottom": {
                                "color": {"color": {"rgbColor": LIGHT_BLUE_BG}},
                                "width": {"magnitude": 1, "unit": "PT"},
                                "padding": {"magnitude": 4, "unit": "PT"},
                                "dashStyle": "SOLID"
                            }
                        }
                        extra_fields = ",spaceAbove,borderBottom"

                    heading_fix_requests.append({
                        "updateParagraphStyle": {
                            "range": {"startIndex": start_idx, "endIndex": end_idx, "tabId": TAB_ID},
                            "paragraphStyle": {"namedStyleType": target_style, **extra_style},
                            "fields": f"namedStyleType{extra_fields}"
                        }
                    })
        break

if heading_fix_requests:
    print(f"  Applying {len(heading_fix_requests)} heading style updates...")
    for i in range(0, len(heading_fix_requests), BATCH_SIZE):
        batch = heading_fix_requests[i:i+BATCH_SIZE]
        hdr_resp = requests.post(
            f"https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate",
            headers=headers,
            json={"requests": batch}
        )
        if hdr_resp.status_code != 200:
            print(f"  ERROR: {hdr_resp.status_code}")
            print(hdr_resp.text[:1000])
            exit(1)
else:
    print("  No heading updates needed.")

# ===== STEP 6: Re-read document and apply hyperlinks using ACTUAL positions =====
# After all formatting (including bullets), indices may have shifted.
# So we read the final document, find URLs by scanning text runs, and apply links.
print("Step 6: Making URLs clickable (reading actual document positions)...")
url_pattern = re.compile(r'https?://[^\s\n"\'<>]+')

doc_resp2 = requests.get(
    f"https://docs.googleapis.com/v1/documents/{DOC_ID}?includeTabsContent=true",
    headers=headers
)
doc_data2 = doc_resp2.json()
link_requests = []

for tab in doc_data2.get("tabs", []):
    if tab.get("tabProperties", {}).get("tabId") == TAB_ID:
        content = tab.get("documentTab", {}).get("body", {}).get("content", [])
        for elem in content:
            para = elem.get("paragraph", {})
            for pe in para.get("elements", []):
                tr = pe.get("textRun", {})
                text = tr.get("content", "")
                ts = tr.get("textStyle", {})
                start_idx = pe.get("startIndex", 0)
                # Skip if already linked
                if ts.get("link"):
                    continue
                # Find URLs in this text run
                for m in url_pattern.finditer(text):
                    url = m.group()
                    while url and url[-1] in (')', ',', '.', ';', ':', "'", '"'):
                        url = url[:-1]
                    abs_start = start_idx + m.start()
                    abs_end = abs_start + len(url)
                    link_requests.append({
                        "updateTextStyle": {
                            "range": {"startIndex": abs_start, "endIndex": abs_end, "tabId": TAB_ID},
                            "textStyle": {
                                "link": {"url": url},
                                "foregroundColor": {"color": {"rgbColor": MEDIUM_BLUE}},
                                "underline": True
                            },
                            "fields": "link,foregroundColor,underline"
                        }
                    })
        break

if link_requests:
    print(f"  Found {len(link_requests)} URLs to hyperlink...")
    for i in range(0, len(link_requests), BATCH_SIZE):
        batch = link_requests[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(link_requests) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Sending link batch {batch_num}/{total_batches} ({len(batch)} requests)...")
        link_resp = requests.post(
            f"https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate",
            headers=headers,
            json={"requests": batch}
        )
        if link_resp.status_code != 200:
            print(f"  ERROR in link batch {batch_num}: {link_resp.status_code}")
            print(link_resp.text[:1000])
else:
    print("  No unlinked URLs found.")

print("\nDone! Feb 24 show doc formatted with pastel blue minimal theme + clickable links.")
