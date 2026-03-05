#!/bin/bash
# Launcher: Opens a visible Terminal window with Claude Code running the show doc
# Called by launchd at 7 AM Bangkok daily

SCRIPT_PATH="/path/to/your/clawdia/scripts/run_showdoc.sh"

osascript <<EOF
tell application "Terminal"
    activate
    set newTab to do script "echo '🌅 Daily Show Doc Generator — $(date +\"%B %d, %Y\")' && echo 'Starting Claude Code...' && echo '' && '$SCRIPT_PATH'"
    set custom title of front window to "Show Doc Generator"
end tell
EOF
