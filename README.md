# Clawdia

**Turn Claude Code into your entire YouTube content team.**

Clawdia is an open-source automation system that uses Claude Code + Airtable + Google APIs to run a full YouTube content pipeline — from trending topic research to published videos with AI-generated thumbnails.

Built by [AI Andy](https://youtube.com/@AIAndyAutomation), who uses this system daily to produce content.

---

## What It Does

| Step | What Happens | Tool |
|------|-------------|------|
| **1. Viral Radar** | Finds trending topics and outlier videos in your niche | Airtable + YouTube API |
| **2. Show Doc** | Creates a daily filming outline with hooks, titles, walkthroughs | Google Docs API + Gemini |
| **3. Content Doc** | Turns any idea into a filmable outline in seconds | Google Docs API |
| **4. Thumbnails** | Generates 6 AI thumbnails from viral inspiration, then transforms them into original variations | Gemini Image Gen |
| **5. Publish** | Uploads video to YouTube with AI-generated metadata | YouTube API + OAuth |
| **6. Track** | Creates/updates records in Airtable for every video | Airtable API |

All orchestrated through **Claude Code** using a single `CLAUDE.md` file that teaches Claude your entire workflow.

---

## The Architecture

```
You (filming) ──→ Clawdia (everything else)

┌─────────────────────────────────────────────────────┐
│                    CLAUDE.md                         │
│         (Your AI's operating manual)                │
│                                                     │
│  Skills/SOPs ──→ Claude Code reads these and        │
│                  follows them step-by-step           │
└──────────┬──────────────────────────────┬───────────┘
           │                              │
     ┌─────▼─────┐                 ┌──────▼──────┐
     │  Pipeline  │                 │  Thumbnail  │
     │  Scripts   │                 │   System    │
     └─────┬─────┘                 └──────┬──────┘
           │                              │
     ┌─────▼──────────────────────────────▼───────┐
     │              External Services              │
     │  YouTube API · Google Docs · Google Drive   │
     │  Airtable · Gemini · Telegram               │
     └────────────────────────────────────────────┘
```

---

## Features

### Thumbnail Pipeline (2-Step)
The most powerful part of the system:

1. **Generate** — Pulls top viral thumbnails from your niche, sends them to Gemini with your face references, generates 6 AI thumbnail options in parallel
2. **Transform** — Takes those 6 and creates 3 original variations each (24 total), with consistent branding (shirt color, text style, background)

```bash
# Step 1: Generate from viral inspiration
python3 thumbnail_system/generate_thumbnail.py "Your Video Title"

# Step 2: Transform to make original
python3 thumbnail_system/transform_thumbnail.py "Your Video Title" --latest
```

### Daily Show Doc Automation
Runs every morning automatically (via macOS `launchd`):
- Pulls trending topics from Viral Radar
- Matches each to a proven format template
- Researches each topic (Reddit, X, tech press)
- Writes a complete filming outline with hooks, titles, and step-by-step walkthroughs
- Publishes to Google Docs and notifies you via Telegram

### YouTube Publisher
Upload videos with zero manual metadata entry:
```bash
# Upload a local video
python3 pipeline/youtube_publisher.py --local-file "video.mp4"

# Upload from Google Drive
python3 pipeline/youtube_publisher.py --drive-url "https://drive.google.com/..."

# Split test (3 versions with different thumbnails)
python3 pipeline/youtube_publisher.py --local-file "video.mp4" --split-test
```

### Content Doc System
Turn any brain dump into a filmable outline:
- Paste a messy idea, article, or notes
- Get back: one-liner, outline, benefits, why-stay-to-the-end, sources

### Skills-First Workflow
Every process has a documented SOP in the `skills/` folder. Claude reads these before doing anything — no improvisation, consistent results every time.

---

## Quick Start

### Prerequisites
- Python 3.10+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (Claude Max or API)
- Google Cloud project with YouTube Data API v3 + Google Drive API enabled
- Airtable account (free tier works)
- Google AI Studio API key (for Gemini)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/clawdia.git
cd clawdia

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and fill in your config
cp .env.example .env
# Edit .env with your API keys

# 4. Set up Google OAuth
# Place your client_secrets.json in the root directory
# First run will open a browser for OAuth consent

# 5. Add your face references (for thumbnails)
# Add face-only crops to face_references/
# See docs/FACE_EXTRACTION.md for how to extract them

# 6. Start using it with Claude Code
claude
# Then say: "Generate thumbnails for 'My Video Title'"
```

See [docs/SETUP.md](docs/SETUP.md) for the full setup guide.

---

## Folder Structure

```
clawdia/
├── CLAUDE.md              # The brain — Claude Code reads this first
├── .env.example           # API key template
├── requirements.txt       # Python dependencies
│
├── pipeline/              # Core automation scripts
│   ├── youtube_publisher.py
│   ├── thumbnail_service.py
│   ├── crop_faces.py
│   └── ...
│
├── thumbnail_system/      # AI thumbnail generation engine
│   ├── generate_thumbnail.py   # Step 1: Generate from viral inspiration
│   ├── transform_thumbnail.py  # Step 2: Originality transformer
│   └── config.py               # Model & Airtable config
│
├── skills/                # SOPs — Claude follows these step-by-step
│   ├── SHOW_DOC_PROCESS_SOP.md
│   ├── THUMBNAIL_SYSTEM_GUIDE.md
│   ├── CONTENT_DOC_PROCESS_SOP.md
│   └── ...
│
├── scripts/               # Automation (launchd, cron)
├── face_references/       # Your face crops (add your own)
├── context/               # Your content, ideas, goals
├── projects/              # Standalone tools
└── docs/                  # Setup guides
```

---

## How the CLAUDE.md Works

The `CLAUDE.md` file is the core innovation. It's a single file that teaches Claude Code:

- **What the project is** and how all the pieces connect
- **Where everything lives** (file paths, API endpoints, table IDs)
- **How to run every process** (exact commands, in order)
- **What conventions to follow** (thumbnail styling, video defaults, etc.)
- **Skills-First Directive** — always check `skills/` before starting any task

When you open Claude Code in this project, it reads `CLAUDE.md` and becomes your content team. You say "generate thumbnails for X" and it knows exactly what to do.

---

## Airtable Setup

Clawdia uses Airtable as its database. You'll need these tables:

| Table | Purpose |
|-------|---------|
| **Content Long-Form** | Video records (title, status, YouTube URL, thumbnail) |
| **Viral Videos** | Top-performing videos in your niche (outlier score, thumbnail) |
| **Thumbnail Generations** | Generated thumbnail options (A-F attachments) |
| **Show Docs** | Daily filming outlines |

See [docs/AIRTABLE_SETUP.md](docs/AIRTABLE_SETUP.md) for the full schema and setup instructions.

---

## Community

**Want help setting this up? Want pre-built Airtable templates, n8n workflows, and video walkthroughs?**

Join the [Skool community](https://www.skool.com/ai-mate) where creators help each other build AI-powered content systems.

What you get:
- Pre-built Airtable base templates (one-click clone)
- n8n workflow imports
- Video walkthroughs for every setup step
- Custom CLAUDE.md templates for different niches
- Weekly live Q&A
- Community of creators using Clawdia

---

## Contributing

PRs welcome! If you build something cool with Clawdia, open a PR or share it in the community.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## See Also

**[Content Mate](https://github.com/AndyHafell/content-mate)** — The short-form content factory. Uses n8n to scrape viral X posts, generate AI videos with avatars + voiceover + captions, and publish to 9 platforms. Clawdia handles long-form; Content Mate handles short-form.

---

## Star This Repo

If Clawdia helps you automate your content pipeline, give it a star! It helps other creators find it.

Built with Claude Code, Gemini, YouTube API, Google Docs API, and Airtable.
