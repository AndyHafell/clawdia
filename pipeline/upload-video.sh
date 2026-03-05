#!/bin/bash
# YouTube Video Uploader - Content Mate
#
# Usage:
#   ./upload-video.sh path/to/video.mp4
#   ./upload-video.sh path/to/video.mp4 "Custom Title"

VIDEO_PATH="$1"
CUSTOM_TITLE="$2"

if [ -z "$VIDEO_PATH" ]; then
    echo "Usage: ./upload-video.sh <video-path> [title]"
    echo "Example: ./upload-video.sh video.mp4"
    echo "Example: ./upload-video.sh video.mp4 'My Custom Title'"
    exit 1
fi

if [ ! -f "$VIDEO_PATH" ]; then
    echo "Error: Video file not found: $VIDEO_PATH"
    exit 1
fi

cd "$(dirname "$0")/.."

if [ -n "$CUSTOM_TITLE" ]; then
    python3 pipeline/youtube_publisher.py --local-file "$VIDEO_PATH" --title "$CUSTOM_TITLE"
else
    python3 pipeline/youtube_publisher.py --local-file "$VIDEO_PATH"
fi
