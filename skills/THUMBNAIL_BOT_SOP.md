# Clawdia SOP — Telegram Bot for Thumbnail Pipeline

## What It Does

**Clawdia** (`@YOUR_TELEGRAM_BOT_USERNAME`) is a persistent Telegram bot that listens for `/thumbnails` commands and triggers the full 4-system thumbnail pipeline (`pipeline/thumbnail_service.py`). Results (top 3 with scores) are sent back to Telegram when done.

**How it works**: Python long-polling (`getUpdates` with `timeout=30`) — one persistent HTTP connection to Telegram, zero wasted API calls when idle. Runs as a `launchd` daemon that auto-starts on login and auto-restarts on crash.

## Commands

| Command | What It Does |
|---------|-------------|
| `/thumbnails Title \| concept A \| concept B` | Run full pipeline (21 thumbnails → score → top 3) |
| `/thumbnails Title` | Run pipeline without concepts |
| `/status` | Check if pipeline is running or idle |
| `/help` | Show command format |

### Example

```
/thumbnails How I Film 3 Videos a Day | AI replaces editor | Revenue dashboard
```

**Pipe `|` separates title from concepts.** Concepts are optional.

## Result Message

After ~5-8 minutes, the bot sends:

```
✅ Thumbnail Pipeline Complete!

🥇 S4_A — Score: 9/10 (NoFace)
🥈 S1_B2_v2 — Score: 8/10 (Viral)
🥉 S3_C — Score: 8/10 (AI+Face)

📊 All scores: S4_A:9, S1_B2:8, ...
📎 6 Airtable records created
⏱ Total time: 6m 42s
```

## Architecture

```
launchd (RunAtLoad=true)
  └── launch_thumbnail_bot.sh (opens Terminal.app for Full Disk Access)
      └── Terminal.app window "Clawdia"
          └── run_thumbnail_bot.sh (PATH, SSL, Drive mount wait, logging)
              └── thumbnail_bot.py (long-polling loop)
                  └── getUpdates(timeout=30) — blocks 30s per call
                      └── /thumbnails command received
                          └── subprocess: python3 pipeline/thumbnail_service.py "Title" --concepts ...
                          └── parse output → send results to Telegram
```

**Why Terminal.app?** Google Drive files require Full Disk Access. Terminal.app has this permission. Running directly via launchd's `/bin/bash` does not — you get "Operation not permitted" errors. Same pattern as the showdoc automation.

## Files

| File | Location | Purpose |
|------|----------|---------|
| Bot script | `scripts/thumbnail_bot.py` | Python long-polling listener |
| Launcher | `~/.thumbnailbot/launch_thumbnail_bot.sh` | Opens Terminal window (for Full Disk Access) |
| Runner script | `~/.thumbnailbot/run_thumbnail_bot.sh` | Environment setup, logging |
| launchd plist | `~/Library/LaunchAgents/com.yourorg.thumbnailbot.plist` | Auto-start on login |
| Logs | `~/.thumbnailbot/logs/bot-YYYY-MM-DD.log` | Daily log files |
| launchd stdout | `/tmp/thumbnailbot-launcher.log` | Launcher-level output |
| launchd stderr | `/tmp/thumbnailbot-launcher-err.log` | Launcher-level errors |

## Management

```bash
# Check if running
ps aux | grep thumbnail_bot | grep -v grep

# Start (load daemon — opens Terminal window)
launchctl load ~/Library/LaunchAgents/com.yourorg.thumbnailbot.plist

# Stop (kill bot process + unload daemon)
pkill -f thumbnail_bot.py
launchctl unload ~/Library/LaunchAgents/com.yourorg.thumbnailbot.plist

# Restart
pkill -f thumbnail_bot.py
launchctl unload ~/Library/LaunchAgents/com.yourorg.thumbnailbot.plist && \
launchctl load ~/Library/LaunchAgents/com.yourorg.thumbnailbot.plist

# View live logs
tail -f ~/.thumbnailbot/logs/bot-$(date +"%Y-%m-%d").log

# View launcher logs (if Terminal didn't open)
cat /tmp/thumbnailbot-launcher.log
cat /tmp/thumbnailbot-launcher-err.log

# Run manually (for testing — no launchd needed)
cd "/path/to/your/project"
python3 scripts/thumbnail_bot.py
```

## Security

- **Authorized chat only**: Bot only responds to messages from `Telegram_chat_id` in `.env`. All other chats are silently ignored.
- **Credentials in `.env`**: `Telegram_access_token` and `Telegram_chat_id` — never hardcoded.
- **Concurrency guard**: Only one pipeline can run at a time. Second requests get a "please wait" message.

## Changing the Authorized Chat

To allow a different Telegram group/user to trigger the bot:

1. Edit `.env` — change `Telegram_chat_id` to the new chat ID
2. Restart: `launchctl unload ... && launchctl load ...`

To find a chat ID: send a message to the bot, then check `https://api.telegram.org/bot<TOKEN>/getUpdates` — the `chat.id` field shows the ID.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Bot not responding | Check `launchctl list \| grep thumbnailbot` — PID should show. If `-` or missing, reload the plist |
| Google Drive not mounted | Bot waits 120s on startup. If Drive never mounts, bot exits and launchd restarts it |
| Pipeline fails | Bot sends error message with last 15 lines. Check `~/.thumbnailbot/logs/` for full output |
| Pipeline timeout | Default is 15 minutes. If consistently timing out, check API rate limits |
| Bot crashed | launchd auto-restarts within 10s (ThrottleInterval). Check `/tmp/thumbnailbot-err.log` |
| Wrong chat responding | Verify `Telegram_chat_id` in `.env` matches your group chat ID |
| "Pipeline already running" | Wait for current run to finish, or restart the bot to clear the lock |
| Telegram 409 Conflict | Another bot instance is polling. Stop all instances: `pkill -f thumbnail_bot.py` then reload launchd |
