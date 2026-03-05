"""
Thumbnail Mate v1.0 - Configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables from parent directory's .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# === API Keys ===
GEMINI_API_KEY = os.getenv('Google_AI_Studio')
YOUTUBE_API_KEY = os.getenv('Youtube_data_key')
AIRTABLE_TOKEN = os.getenv('AIRTABLE_PERSONAL_ACCESS_TOKEN')

# === Airtable (Legacy Thumbnail Mate base — used by scrape_competitors & update_performance) ===
AIRTABLE_BASE_ID = "YOUR_AIRTABLE_BASE_ID"  # Your Airtable base ID for the thumbnail system
AIRTABLE_TABLES = {
    "templates": "YOUR_TEMPLATES_TABLE_ID",       # Table for thumbnail style templates / analyses
    "generations": "YOUR_GENERATIONS_TABLE_ID",    # Table for tracking generated thumbnails
    "performance": "YOUR_PERFORMANCE_TABLE_ID",    # Table for YouTube performance data (views, CTR)
    "competitors": "YOUR_COMPETITORS_TABLE_ID",    # Table for competitor channel tracking
}

# === Nano Banana (Gemini Image Generation) ===
NANO_BANANA_MODEL = "gemini-2.5-flash-image"  # Fast, good quality
NANO_BANANA_PRO_MODEL = "gemini-3-pro-image-preview"  # Best quality, 4K, better text
GEMINI_FLASH_TEXT_MODEL = "gemini-2.5-flash"  # Text+vision scoring (not image gen)

# === Paths ===
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FACE_REFS_DIR = os.path.join(os.path.dirname(BASE_DIR), "face_references")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# === Content Mate Airtable (main output table — used by generate_thumbnail & transform_thumbnail) ===
CONTENT_MATE_BASE = "YOUR_AIRTABLE_BASE_ID"              # Your main Airtable base ID (can be same as above)
CONTENT_MATE_TABLE = "YOUR_CONTENT_TABLE_ID"              # Content / video records table
VIRAL_VIDEOS_TABLE = "YOUR_VIRAL_VIDEOS_TABLE_ID"         # Viral Videos table (top-performing thumbnails for inspiration)
THUMBNAIL_GENERATIONS_TABLE = "YOUR_THUMBNAIL_GENERATIONS_TABLE_ID"  # Thumbnail Generations table (generated output)
FAVORITE_THUMBNAILS_TABLE = "YOUR_FAVORITE_THUMBNAILS_TABLE_ID"      # Favorite Thumbnails table (curated picks)

# === Your YouTube Channel ===
ANDY_CHANNEL_ID = "YOUR_YOUTUBE_CHANNEL_ID"  # Your YouTube channel ID (format: UC...)

# === Thumbnail Settings ===
OUTPUT_WIDTH = 1920
OUTPUT_HEIGHT = 1080
NUM_OPTIONS = 6  # Generate 6 options per request
