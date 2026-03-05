# Clawdia — Architecture

## System Overview

Clawdia is a **Claude Code-powered content automation system**. The key innovation is using `CLAUDE.md` as an operating manual that turns Claude Code into a full content team.

```
┌──────────────────────────────────────────────────────────┐
│                     CLAUDE.md                             │
│              (AI Operating Manual)                         │
│                                                           │
│  "When I say 'generate thumbnails', Claude reads the      │
│   CLAUDE.md, finds the relevant skill, and executes       │
│   the entire pipeline autonomously."                      │
└───────────┬───────────────────────────────┬───────────────┘
            │                               │
      ┌─────▼──────┐                 ┌──────▼──────┐
      │   Skills    │                 │   Scripts   │
      │  (SOPs)     │                 │ (Pipeline)  │
      └─────┬──────┘                 └──────┬──────┘
            │                               │
            │         ┌─────────┐           │
            └────────→│ Claude  │←──────────┘
                      │  Code   │
                      └────┬────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
   ┌─────▼─────┐   ┌──────▼──────┐   ┌─────▼─────┐
   │  YouTube   │   │   Google    │   │ Airtable  │
   │  Data API  │   │  Docs/Drive │   │    API    │
   └───────────┘   └─────────────┘   └───────────┘
```

## Components

### 1. CLAUDE.md (The Brain)
- Single file that defines all project knowledge
- Claude Code reads this on every session start
- Contains: architecture, commands, conventions, API references
- Points to `skills/` for detailed procedures

### 2. Skills (SOPs)
- Documented standard operating procedures
- Claude reads the relevant SOP before executing any task
- Ensures consistent, repeatable results
- Examples: thumbnail generation, video publishing, show doc creation

### 3. Pipeline Scripts
- Python scripts that do the actual work
- YouTube upload, thumbnail generation, Google Docs formatting
- All scripts use `.env` for configuration
- All scripts use `_PROJECT_ROOT` pattern for path resolution

### 4. Thumbnail System
- 2-step pipeline: Generate → Transform
- Uses Gemini image generation models
- Face references for consistent AI likeness
- Parallel processing for speed (~2 min for 6 thumbnails)

### 5. External Services

| Service | What For | API Used |
|---------|----------|----------|
| **YouTube** | Video upload, metadata | YouTube Data API v3 |
| **Google Drive** | File storage, sharing | Google Drive API |
| **Google Docs** | Show docs, content docs | Google Docs API |
| **Airtable** | Content database | Airtable REST API |
| **Gemini** | Thumbnail generation, AI metadata | Google AI Studio |
| **Telegram** | Notifications | Telegram Bot API |

## Data Flow

### Video Publishing
```
Video file → youtube_publisher.py → YouTube (private upload)
                                  → Airtable (record created)
                                  → Gemini (AI title, description, tags)
```

### Thumbnail Generation
```
Viral Videos (Airtable) → generate_thumbnail.py → 6 options (A-F)
                                                → Google Drive
                                                → Airtable

6 options → transform_thumbnail.py → 3 variations each (18 total)
                                   → Google Drive
                                   → Airtable
```

### Daily Show Doc
```
Viral Radar (Airtable) → Top 3 outlier topics
                       → Format matching (Hall of Fame)
                       → Research (web search)
                       → Show doc writing
                       → Google Docs (formatted)
                       → Airtable (tracked)
                       → Telegram (notification)
```

## Path Resolution Pattern

All pipeline scripts use this pattern to find project root:
```python
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
```

This allows scripts to find `.env`, `client_secrets.json`, `youtube_token.pickle`, and other root-level files regardless of where you run them from.

## Authentication

- **YouTube/Drive**: OAuth 2.0 via `client_secrets.json` → `youtube_token.pickle`
- **Airtable**: Personal Access Token in `.env`
- **Gemini**: API key in `.env`
- **Telegram**: Bot token in `.env`

OAuth tokens are stored in `youtube_token.pickle`. Delete this file to force re-authentication.
