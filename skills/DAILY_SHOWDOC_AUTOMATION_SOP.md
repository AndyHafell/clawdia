# Daily Show Doc Automation — Standard Operating Procedure

## Purpose
Automatically generate a complete show doc every morning at 7 AM Bangkok time using Claude Code (headless mode) on your Mac, powered by the Claude Max subscription — zero API costs.

## Architecture

```
6:55 AM  →  pmset wakes Mac from sleep
7:00 AM  →  launchd fires com.yourorg.showdoc
         →  launch_showdoc.sh opens a visible Terminal window
         →  run_showdoc.sh sets environment, runs claude -p with the prompt
         →  Claude Code executes the full 7-step Show Doc Process SOP
         →  Google Doc tab created, Airtable record created
         →  Telegram notification sent to you
         →  If failure: separate Telegram failure alert
```

## System Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **launchd plist** | `~/Library/LaunchAgents/com.yourorg.showdoc.plist` | macOS scheduler, fires at 7:00 AM daily |
| **Terminal launcher** | `scripts/launch_showdoc.sh` | Opens a visible Terminal window via osascript |
| **Runner script** | `scripts/run_showdoc.sh` | Sets PATH, SSL, reads prompt, runs `claude -p`, logs, failure notification |
| **Prompt file** | `scripts/showdoc_prompt.md` | The full prompt Claude executes (9-step process) |
| **Logs** | `scripts/logs/showdoc-YYYY-MM-DD.log` | Daily log files |
| **Show Doc SOP** | `skills/SHOW_DOC_PROCESS_SOP.md` | The 7-step process Claude follows |
| **Format Selection SOP** | `skills/FORMAT_SELECTION_SOP.md` | Format matching decision matrix |

## Prerequisites

- **Mac must be sleeping (lid closed), NOT fully shut down** — pmset can only wake from sleep
- **Claude Code installed** via npm (path: `$HOME/.nvm/versions/node/<YOUR_NODE_VERSION>/bin/claude`)
- **Claude Max subscription** active ($100/mo plan — provides OAuth auth, no API key needed)
- **Internet connection** available when Mac wakes (for Airtable API, Google Docs API, web research, Telegram)
- **Google Drive sync** active (for the project folder)

## What Claude Code Executes

The prompt in `scripts/showdoc_prompt.md` instructs Claude to:

1. Read `SHOW_DOC_PROCESS_SOP.md` and `FORMAT_SELECTION_SOP.md`
2. Pull today's top outliers from Viral Videos table (last 3 days, sorted by Views)
3. Match each topic to a Hall of Fame format
4. Deep research each topic (Reddit, X/Twitter, tech press, demos)
5. Write full show doc content (SOURCES, 7 TITLES, THUMBNAIL IDEAS, SAY THIS, 4P, 7 HOOKS, TRANSFORMATION GOAL, WALKTHROUGH, SUMMARY)
6. Write BONUS section (5-10 extra topic ideas)
7. Create a new tab in the Master Show Doc via Google Docs API with pastel blue formatting
8. Create an Airtable record in Show Docs table
9. Send Telegram notification with topics and Google Doc link

### Allowed Tools
```
Bash (Airtable API, Google Docs API, web research, Telegram)
Read, Write, Edit, Grep, Glob
WebSearch, WebFetch
Task (for parallel research agents)
```

### Limits
- `--max-turns 50` (prevents runaway sessions)
- `--output-format stream-json` (visible progress in Terminal)

## Management Commands

```bash
# Check if the job is loaded
launchctl list | grep showdoc

# Manual test run (opens Terminal window, runs full process)
bash scripts/launch_showdoc.sh

# Pause automation (stop daily runs)
launchctl unload ~/Library/LaunchAgents/com.yourorg.showdoc.plist

# Resume automation
launchctl load ~/Library/LaunchAgents/com.yourorg.showdoc.plist

# Reload after editing the plist
launchctl unload ~/Library/LaunchAgents/com.yourorg.showdoc.plist && \
launchctl load ~/Library/LaunchAgents/com.yourorg.showdoc.plist

# Check wake schedule
pmset -g sched

# Change wake time (requires sudo)
sudo pmset repeat wakeorpoweron MTWRFSU 06:55:00

# View today's log
cat scripts/logs/showdoc-$(date +"%Y-%m-%d").log

# View latest log (tail)
tail -100 scripts/logs/showdoc-$(date +"%Y-%m-%d").log
```

## Troubleshooting

### Automation didn't run
1. **Mac was shut down** → Must be sleeping (lid closed), not powered off
2. **launchd not loaded** → Run `launchctl load ~/Library/LaunchAgents/com.yourorg.showdoc.plist`
3. **No internet** → Mac woke but WiFi didn't reconnect in time. Check `/tmp/showdoc-launcher-err.log`
4. **Claude binary not found** → Check PATH in plist includes nvm node path

### Claude Code failed mid-run
1. Check log: `cat scripts/logs/showdoc-$(date +"%Y-%m-%d").log`
2. You should have received a Telegram failure notification
3. Common causes: Airtable API rate limit, Google Docs API token expired, web research timeout
4. Fix: Run manually with `bash scripts/launch_showdoc.sh`

### Google Doc token expired
1. Delete `youtube_token.pickle` and run any script that uses Google APIs
2. Browser will open for re-authorization
3. After re-auth, the automation will work again

### Change the schedule time
1. Edit `~/Library/LaunchAgents/com.yourorg.showdoc.plist`
2. Change `<integer>7</integer>` (Hour) and `<integer>0</integer>` (Minute)
3. Reload: `launchctl unload ... && launchctl load ...`
4. Update pmset wake time: `sudo pmset repeat wakeorpoweron MTWRFSU HH:MM:00`

## File Locations

```
~/Library/LaunchAgents/
└── com.yourorg.showdoc.plist          ← launchd scheduler

Claude Folder/
├── scripts/
│   ├── launch_showdoc.sh              ← Terminal window opener
│   ├── run_showdoc.sh                 ← Runner (env + claude -p + logging)
│   ├── showdoc_prompt.md              ← The prompt Claude executes
│   └── logs/
│       └── showdoc-YYYY-MM-DD.log     ← Daily logs
├── skills/
│   ├── SHOW_DOC_PROCESS_SOP.md        ← The 7-step process
│   ├── FORMAT_SELECTION_SOP.md        ← Format matching
│   └── DAILY_SHOWDOC_AUTOMATION_SOP.md ← This file
└── .env                               ← Telegram credentials
```

## Modifying the Prompt

To change what the automation does each morning, edit `scripts/showdoc_prompt.md`. Changes take effect on the next run — no need to reload launchd.

Key things you might want to change:
- Number of topics (currently 3)
- Research depth (currently full: Reddit, X, tech press, demos)
- Bonus section size (currently 5-10 ideas)
- Notification format

## History

- **Created**: February 25, 2026
- **First successful run**: February 25, 2026 (manual test, produced full show doc with 3 topics)
- **Architecture choice**: launchd + pmset + `claude -p` was chosen over n8n because the goal is to use the Claude Max subscription ($100/mo) instead of paying per-API-call costs
