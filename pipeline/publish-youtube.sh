#!/bin/bash
#
# YouTube Publisher - Easy Wrapper Script
#
# Usage:
#   ./publish-youtube.sh "https://drive.google.com/..."
#   ./publish-youtube.sh "https://drive.google.com/..." "My Custom Title"

DRIVE_URL="$1"
TITLE="$2"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

if [ -z "$DRIVE_URL" ]; then
    echo "❌ Error: No Google Drive URL provided"
    echo ""
    echo "Usage: ./publish-youtube.sh <drive-url> [title]"
    echo ""
    echo "Example:"
    echo "  ./publish-youtube.sh \"https://drive.google.com/open?id=1-VaKEItUKw7Swi_w0vM4W9PcxtaSoODq\""
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the publisher
if [ -z "$TITLE" ]; then
    python3 pipeline/youtube_publisher.py --drive-url "$DRIVE_URL"
else
    python3 pipeline/youtube_publisher.py --drive-url "$DRIVE_URL" --title "$TITLE"
fi
