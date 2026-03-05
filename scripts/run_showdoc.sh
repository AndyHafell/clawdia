#!/bin/bash
# Daily Show Doc Generator — runs via launchd at 7 AM Bangkok
# Opens Claude Code with the full interactive UI so you can watch it work
# Uses Claude Max subscription (no API key needed)

# --- Config ---
PROJECT_DIR="/path/to/your/clawdia"
SCRIPTS_DIR="$PROJECT_DIR/scripts"
LOG_DIR="$PROJECT_DIR/scripts/logs"
PROMPT_FILE="$SCRIPTS_DIR/showdoc_prompt.md"
DATE_STAMP=$(date +"%Y-%m-%d")

# Ensure PATH includes claude binary
export PATH="$HOME/.nvm/versions/node/$(ls $HOME/.nvm/versions/node/ 2>/dev/null | tail -1)/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# SSL certs for Python requests
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())" 2>/dev/null || echo "")
export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"

# --- Setup ---
mkdir -p "$LOG_DIR"

# --- Read prompt and inject today's date ---
PROMPT=$(cat "$PROMPT_FILE")
PROMPT="${PROMPT//\$(date +\"%B %d, %Y\")/$(date +"%B %d, %Y")}"

# --- Run Claude Code with full interactive UI ---
cd "$PROJECT_DIR"

# Use -p for headless but with streaming output so you can see progress
# The --verbose flag shows tool calls and thinking in real time
claude -p "$PROMPT" \
    --allowedTools "Bash(run commands for Airtable API calls, Google Docs API, web research, sending Telegram messages),Read,Write,Edit,Grep,Glob,WebSearch,WebFetch,Task" \
    --max-turns 50 \
    --output-format stream-json \
    2>&1 | tee "$LOG_DIR/showdoc-$DATE_STAMP.log"

EXIT_CODE=${PIPESTATUS[0]}

# --- Send failure notification if it crashed ---
if [ "$EXIT_CODE" -ne 0 ]; then
    TELEGRAM_TOKEN=$(grep "^Telegram_access_token=" "$PROJECT_DIR/.env" | cut -d= -f2)
    TELEGRAM_CHAT_ID=$(grep "^Telegram_chat_id=" "$PROJECT_DIR/.env" | cut -d= -f2)
    if [ -n "$TELEGRAM_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_CHAT_ID}" \
            -d "parse_mode=Markdown" \
            -d "text=❌ Show Doc generation FAILED on $DATE_STAMP. Check logs." > /dev/null 2>&1
    fi
fi

echo ""
echo "=========================================="
echo "Show Doc generation finished (exit: $EXIT_CODE)"
echo "Log: $LOG_DIR/showdoc-$DATE_STAMP.log"
echo "=========================================="
