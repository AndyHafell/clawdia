# Viral Radar — Standard Operating Procedure

## What It Does
Viral Radar is a daily n8n automation that scrapes 10 competitor YouTube channels, detects outlier videos (views > 2x channel median), stores everything in Airtable with Outlier Scores, and sends a Telegram summary at 7 AM Bangkok time.

## System Components

| Component | Location |
|-----------|----------|
| n8n Workflow | `YOUR_N8N_WORKFLOW_ID` on `https://YOUR_N8N_INSTANCE_URL` |
| Deploy Script | `deploy_viral_radar.py` (v2.0) |
| Cleanup Script | `viral_radar_cleanup.py` (dedup + backfill) |
| Channels Table | `YOUR_CHANNELS_TABLE_ID` in Mate OS base |
| Viral Videos Table | `YOUR_VIRAL_VIDEOS_TABLE_ID` in Mate OS base |
| Telegram Chat | `YOUR_TELEGRAM_CHAT_ID` |
| Schedule | Daily at midnight UTC (7 AM Bangkok) |

## Active Channels (10)
1. Channel A (900K+) — UC_CHANNEL_A_ID
2. Channel B (700K+) — UC_CHANNEL_B_ID
3. Channel C (500K+) — UC_CHANNEL_C_ID
4. Channel D (250K+) — UC_CHANNEL_D_ID
5. Channel E (250K+) — UC_CHANNEL_E_ID
6. Channel F (125K+) — UC_CHANNEL_F_ID
7. Channel G (100K+) — UC_CHANNEL_G_ID
8. Channel H (85K+) — UC_CHANNEL_H_ID
9. Channel I (60K+) — UC_CHANNEL_I_ID
10. Channel J (40K+) — UC_CHANNEL_J_ID

## How It Works (Node Flow — v2.0)

```
Schedule/Webhook → Get Channels → Extract → Fetch RSS ─────────┐
                └→ Fetch Existing URLs (Airtable, paginated) ──┤
                                                                 → Parse & Analyze → Route
                                                                    ├→ batch → Create Records
                                                                    └→ summary → Send Telegram
```

1. **Schedule Trigger** — Fires at midnight UTC (7 AM Bangkok)
2. **Manual Trigger** — Webhook at `/webhook/viral-radar-run`
3. **Get Channels** — Pulls active channels from Airtable Channels table
4. **Fetch Existing URLs** — Queries ALL existing URLs from Viral Videos table (with pagination) — runs in parallel with RSS fetching
5. **Extract Channels** — Builds RSS feed URLs from Channel IDs
6. **Fetch RSS** — Hits YouTube RSS feed for each channel (free, no quota)
7. **Parse & Analyze** — Core logic:
   - Parses RSS XML for video data (title, views, published date, thumbnail)
   - Dedup: checks against in-memory `seenVideoIds` (last 2000) AND pre-fetched Airtable URLs
   - Calculates channel median views
   - Calculates **Outlier Score** = views / channel median (numeric, e.g., 3.4)
   - Marks `Outlier?` checkbox if score > 2.0
   - Batches records into groups of 10 for Airtable
   - Builds Telegram summary with top outliers
8. **Route** — Splits batch items → Create Records, summary item → Send Summary
9. **Create Records** — POSTs batches to Viral Videos table (includes Outlier Score)
10. **Send Summary** — Telegram message with outlier highlights

## Key Fields in Viral Videos Table

| Field | Type | Description |
|-------|------|-------------|
| Title | Text | Video title |
| Video ID | Text | YouTube video ID |
| Channel Name | Text | Source channel |
| URL | Text | YouTube watch URL |
| Thumbnail | Attachment | Downloaded from YouTube |
| Views | Number | View count at scrape time |
| Published Date | Date | Video publish date |
| Description | Text | Up to 5000 chars |
| **Outlier Score** | Number | Views / channel median (e.g., 3.4x) |
| Outlier? | Checkbox | True if Outlier Score > 2.0 |
| **Thumbnail Used** | Checkbox | Marked true by `generate_thumbnail.py` after using this thumbnail |
| Scraped Date | Date | When the record was created |

## Outlier Score Calculation
- Per channel: collect all video views, calculate median
- **Outlier Score** = video views / channel median (e.g., 50,000 views / 15,000 median = 3.3)
- Score > 2.0 = outlier (checkbox `Outlier?` = true)
- Score is stored as a **number field** so thumbnail generation can sort by it
- `generate_thumbnail.py` sorts unused viral thumbs by Outlier Score descending → picks best ones first

## Duplicate Prevention (v2.0)

### At Insert Time (n8n workflow)
1. Before parsing RSS, the workflow fetches ALL existing URLs from Airtable (paginated)
2. New videos are checked against: (a) in-memory `seenVideoIds` and (b) existing Airtable URLs
3. Videos with matching URLs are skipped entirely — never created as duplicates

### Post-Run Cleanup (viral_radar_cleanup.py)
For comprehensive dedup + score maintenance:
```bash
# Full cleanup: remove dupes + backfill Outlier Score
python3 viral_radar_cleanup.py

# Preview changes first (no modifications)
python3 viral_radar_cleanup.py --dry-run

# Only remove duplicates
python3 viral_radar_cleanup.py --dedup-only

# Only backfill Outlier Scores
python3 viral_radar_cleanup.py --backfill-only
```

**Dedup rules:**
- Groups records by YouTube URL
- Keeps the **oldest** record (earliest Scraped Date) — preserves `Thumbnail Used` flags
- Deletes all newer duplicates
- Handles batched Airtable DELETE (max 10 per request)

**Backfill rules:**
- Groups all records by Channel Name
- Calculates channel median views
- Updates `Outlier Score` for any record that's missing it or has score = 0

## Thumbnail Integration

The thumbnail system (`generate_thumbnail.py`) is a key consumer of Viral Videos:
1. Queries: `NOT({Thumbnail Used})` sorted by `Outlier Score` descending
2. Picks top 10, randomly selects 6 for thumbnail generation
3. After generation, marks selected records as `Thumbnail Used = True`
4. To reuse thumbnails: manually uncheck `Thumbnail Used` in Airtable

**Important:** Always use `NANO_BANANA_PRO_MODEL` (not the base model) for thumbnail generation.

## Daily API Usage
- YouTube RSS: free (no quota)
- Airtable: ~30-50 API calls per run (includes existing URL fetch + record creation)
- Telegram: 1 message per run

## Adding/Removing Channels
1. Go to the **Channels** table in Airtable
2. Add a new row with: Name, Channel ID (UCxxxxxx), Channel URL, Subscribers, Active = checked
3. To find a Channel ID: go to their YouTube page → view source → search for "UCxxxxxx"
4. Uncheck **Active** to stop scraping a channel (don't delete — keeps historical data)

## Manual Trigger
```bash
# Via webhook (simplest)
curl "https://YOUR_N8N_INSTANCE_URL/webhook/viral-radar-run"

# Via n8n API
curl -X POST "https://YOUR_N8N_INSTANCE_URL/api/v1/workflows/YOUR_N8N_WORKFLOW_ID/activate" \
  -H "X-N8N-API-KEY: $n8n_API_KEY"
```

## Deploying Changes
```bash
# Update deploy_viral_radar.py with changes, then:
python3 deploy_viral_radar.py
# This deactivates → updates → reactivates the workflow
```

## Troubleshooting
- **No new videos**: All recent videos already in Airtable (dedup working correctly)
- **Missing Outlier Scores**: Run `python3 viral_radar_cleanup.py --backfill-only`
- **Duplicate videos appeared**: Run `python3 viral_radar_cleanup.py --dedup-only`
- **Missing channel**: Check if Active = true in Channels table and Channel ID is valid
- **Telegram not sending**: Check bot token and chat ID in the Telegram node
- **Thumbnails picking wrong videos**: Check that `Outlier Score` field is populated (run backfill if needed)
