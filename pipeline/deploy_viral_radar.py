#!/usr/bin/env python3
"""
Deploy Viral Radar v2.0 workflow to n8n.
Uses proper n8n nodes (HTTP Request, Code, Telegram) since Code node
sandbox doesn't allow HTTP calls.
"""

import json
import os
import urllib.request

N8N_URL = os.environ.get("N8N_URL", "https://YOUR_N8N_INSTANCE_URL")
N8N_API_KEY = os.environ.get("n8n_API_KEY", "YOUR_N8N_API_KEY")
WF_ID = "YOUR_WORKFLOW_ID"

AIRTABLE_TOKEN = os.environ.get("AIRTABLE_PERSONAL_ACCESS_TOKEN", "YOUR_AIRTABLE_TOKEN")
AIRTABLE_BASE = "YOUR_AIRTABLE_BASE_ID"
CHANNELS_TABLE = "YOUR_CHANNELS_TABLE_ID"
VIDEOS_TABLE = "YOUR_VIRAL_VIDEOS_TABLE_ID"
YT_API_KEY = os.environ.get("YOUTUBE_DATA_API_KEY", "YOUR_YOUTUBE_API_KEY")

# === Code Node: Extract channels + build RSS URLs ===
CODE_EXTRACT = r"""
const input = $input.first().json;
const records = input.records || [];
const channels = records
  .map(r => ({
    channelName: r.fields['Name'] || '',
    channelId: r.fields['Channel ID'] || '',
    rssUrl: `https://www.youtube.com/feeds/videos.xml?channel_id=${r.fields['Channel ID'] || ''}`,
  }))
  .filter(c => c.channelId);

if (channels.length === 0) {
  return [{ json: { channelName: 'NONE', channelId: '', rssUrl: '' } }];
}

return channels.map(c => ({ json: c }));
"""

# === Code Node: Parse RSS, dedup, outliers, build Airtable payloads + summary ===
CODE_PARSE = r"""
// Get channel data from earlier node (matches RSS items by index)
const channelItems = $('Extract Channels').all();

// Build set of existing URLs from pre-fetched Airtable data (prevents duplicates at insert time)
const existingUrls = new Set();
try {
  const existingData = $('Fetch Existing URLs').all();
  for (const item of existingData) {
    const records = item.json?.records || [];
    for (const rec of records) {
      const url = rec?.fields?.URL || rec?.fields?.url || '';
      if (url) existingUrls.add(url);
    }
    // Also handle flat record items (if pagination flattens them)
    const directUrl = item.json?.fields?.URL || item.json?.fields?.url || '';
    if (directUrl) existingUrls.add(directUrl);
  }
} catch (e) {
  // Fetch Existing URLs node might not exist in older versions — fall back to static data only
}

// Dedup via workflow static data + existing Airtable URLs
const staticData = $getWorkflowStaticData('global');
if (!staticData.seenVideoIds) staticData.seenVideoIds = [];
const seenSet = new Set(staticData.seenVideoIds);

// Helper: decode XML entities
function decodeXml(str) {
  return str
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'");
}

// Parse all RSS feeds
const allVideos = [];
const rssItems = $input.all();

for (let i = 0; i < rssItems.length; i++) {
  const responseData = rssItems[i].json;
  // HTTP Request node returns response in 'data' field when text mode
  const xmlStr = typeof responseData === 'string'
    ? responseData
    : (responseData.data || responseData.body || JSON.stringify(responseData));

  const channelName = channelItems[i]?.json?.channelName || 'Unknown';

  if (!xmlStr || xmlStr.includes('"channelName"')) continue; // Skip non-XML

  const entries = xmlStr.split('<entry>').slice(1);
  for (const entry of entries) {
    const videoId = entry.match(/<yt:videoId>([^<]+)/)?.[1];
    if (!videoId || seenSet.has(videoId)) continue;

    // Also check against existing Airtable URLs to prevent duplicates
    const candidateUrl = `https://youtube.com/watch?v=${videoId}`;
    if (existingUrls.has(candidateUrl) || existingUrls.has(`https://www.youtube.com/watch?v=${videoId}`)) continue;

    const titleMatch = entry.match(/<title>([^<]+)/);
    const title = titleMatch ? decodeXml(titleMatch[1]) : 'Unknown';
    const published = entry.match(/<published>([^<]+)/)?.[1] || '';
    const viewsMatch = entry.match(/views="(\d+)"/);
    const views = viewsMatch ? parseInt(viewsMatch[1]) : 0;
    const descMatch = entry.match(/<media:description>([\s\S]*?)<\/media:description>/);
    const description = descMatch ? decodeXml(descMatch[1].trim()).substring(0, 5000) : '';

    allVideos.push({
      videoId, title, channelName, published, views, description,
      thumbnailUrl: `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`,
      url: `https://youtube.com/watch?v=${videoId}`,
    });

    seenSet.add(videoId);
  }
}

// Update static data (keep last 2000 IDs)
staticData.seenVideoIds = [...seenSet].slice(-2000);

// Calculate outliers per channel
const byChannel = {};
for (const v of allVideos) {
  if (!byChannel[v.channelName]) byChannel[v.channelName] = [];
  byChannel[v.channelName].push(v);
}

for (const [ch, vids] of Object.entries(byChannel)) {
  const viewsList = vids.map(v => v.views).sort((a, b) => a - b);
  const mid = Math.floor(viewsList.length / 2);
  const median = viewsList.length === 0 ? 0
    : viewsList.length % 2 === 0
      ? (viewsList[Math.max(0, mid - 1)] + viewsList[mid]) / 2
      : viewsList[mid];
  for (const v of vids) {
    v.isOutlier = median > 0 && v.views > median * 2;
    v.channelMedian = Math.round(median);
  }
}

// Build output items
const output = [];

// Batch Airtable payloads (10 records per batch)
for (let i = 0; i < allVideos.length; i += 10) {
  const batch = allVideos.slice(i, i + 10);
  const records = batch.map(v => ({
    fields: {
      'Title': v.title,
      'Video ID': v.videoId,
      'Channel Name': v.channelName,
      'URL': v.url,
      'Thumbnail': [{ url: v.thumbnailUrl }],
      'Views': v.views,
      'Likes': 0,
      'Comments': 0,
      'Duration': '00:00:00',
      'Published Date': v.published ? v.published.split('T')[0] : null,
      'Description': v.description,
      'Outlier?': v.isOutlier || false,
      'Outlier Score': v.channelMedian > 0 ? parseFloat((v.views / v.channelMedian).toFixed(1)) : 0,
      'Scraped Date': new Date().toISOString().split('T')[0],
    }
  }));
  output.push({ json: { type: 'batch', payload: { records } } });
}

// Build Telegram summary
const today = new Date().toLocaleDateString('en-GB', {
  day: 'numeric', month: 'short', year: 'numeric'
});
const channelCount = Object.keys(byChannel).length;
const outliers = allVideos.filter(v => v.isOutlier).sort((a, b) => b.views - a.views);

let msg = `<b>Viral Radar — ${today}</b>\n\n`;
msg += `${allVideos.length} new videos from ${channelCount} channels\n`;

if (outliers.length > 0) {
  msg += `\n<b>OUTLIERS (${outliers.length})</b>\n`;
  msg += `<i>Videos performing 2x+ above channel median</i>\n\n`;
  for (const v of outliers.slice(0, 10)) {
    const ratio = v.channelMedian > 0 ? (v.views / v.channelMedian).toFixed(1) : '?';
    msg += `<b>${v.title}</b>\n`;
    msg += `${v.channelName} | ${v.views.toLocaleString()} views (${ratio}x median)\n`;
    msg += `<a href="${v.url}">Watch</a>\n\n`;
  }
} else if (allVideos.length > 0) {
  msg += `\nNo major outliers today.\n`;
} else {
  msg += `\nNo new videos found.\n`;
}

msg += `\n<b>By Channel</b>\n`;
for (const [ch, vids] of Object.entries(byChannel)) {
  const chOutliers = vids.filter(v => v.isOutlier).length;
  msg += `${ch}: ${vids.length} new`;
  if (chOutliers > 0) msg += ` (${chOutliers} outlier${chOutliers > 1 ? 's' : ''})`;
  msg += `\n`;
}

if (allVideos.length === 0) {
  msg += `(All channels up to date)\n`;
}

if (msg.length > 4000) msg = msg.substring(0, 3990) + '\n...(truncated)';

output.push({ json: { type: 'summary', text: msg } });

return output;
"""

# === Build Workflow JSON ===
workflow_update = {
    "name": "Viral Radar v2.0",
    "nodes": [
        # --- Triggers ---
        {
            "id": "schedule-trigger",
            "name": "Schedule Trigger",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [0, 300],
            "parameters": {
                "rule": {
                    "interval": [
                        {
                            "field": "cronExpression",
                            "expression": "0 7 * * *"
                        }
                    ]
                }
            }
        },
        {
            "id": "webhook-trigger",
            "name": "Manual Trigger",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 2,
            "position": [0, 500],
            "webhookId": "viral-radar-run",
            "parameters": {
                "path": "viral-radar-run",
                "httpMethod": "GET",
                "responseMode": "lastNode",
            }
        },

        # --- Step 1: Fetch channels from Airtable ---
        {
            "id": "get-channels",
            "name": "Get Channels",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [300, 400],
            "parameters": {
                "method": "GET",
                "url": f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{CHANNELS_TABLE}",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Authorization",
                            "value": f"Bearer {AIRTABLE_TOKEN}"
                        }
                    ]
                },
                "sendQuery": True,
                "queryParameters": {
                    "parameters": [
                        {
                            "name": "filterByFormula",
                            "value": "{Active} = TRUE()"
                        }
                    ]
                },
                "options": {}
            }
        },

        # --- Step 2: Extract channels + build RSS URLs ---
        {
            "id": "extract-channels",
            "name": "Extract Channels",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [550, 400],
            "parameters": {
                "mode": "runOnceForAllItems",
                "jsCode": CODE_EXTRACT
            }
        },

        # --- Step 2b: Fetch existing URLs from Airtable (for dedup at insert time) ---
        {
            "id": "fetch-existing-urls",
            "name": "Fetch Existing URLs",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [550, 600],
            "parameters": {
                "method": "GET",
                "url": f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{VIDEOS_TABLE}?fields%5B%5D=URL&pageSize=100",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Authorization",
                            "value": f"Bearer {AIRTABLE_TOKEN}"
                        }
                    ]
                },
                "options": {
                    "pagination": {
                        "pagination": {
                            "paginationMode": "responseContainsNextUrl",
                            "responseContainsNextUrl": {
                                "url": "={{ $response.body.offset ? '" + f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{VIDEOS_TABLE}?fields%5B%5D=URL&pageSize=100&offset=" + "' + $response.body.offset : '' }}",
                                "limitPagesFetched": True,
                                "maxPages": 100
                            }
                        }
                    }
                }
            }
        },

        # --- Step 3: Fetch RSS feeds ---
        {
            "id": "fetch-rss",
            "name": "Fetch RSS",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [800, 400],
            "parameters": {
                "method": "GET",
                "url": "={{ $json.rssUrl }}",
                "options": {
                    "response": {
                        "response": {
                            "responseFormat": "text"
                        }
                    }
                }
            }
        },

        # --- Step 4: Parse RSS + Outliers + Build output ---
        {
            "id": "parse-analyze",
            "name": "Parse & Analyze",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1050, 400],
            "parameters": {
                "mode": "runOnceForAllItems",
                "jsCode": CODE_PARSE
            }
        },

        # --- Step 5: Route batch vs summary ---
        {
            "id": "if-route",
            "name": "Route",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": [1300, 400],
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "leftValue": "",
                        "typeValidation": "strict"
                    },
                    "conditions": [
                        {
                            "id": "condition-0",
                            "leftValue": "={{ $json.type }}",
                            "rightValue": "batch",
                            "operator": {
                                "type": "string",
                                "operation": "equals"
                            }
                        }
                    ],
                    "combinator": "and"
                }
            }
        },

        # --- Step 6: Create Airtable records (batch) ---
        {
            "id": "create-records",
            "name": "Create Records",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1550, 300],
            "parameters": {
                "method": "POST",
                "url": f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{VIDEOS_TABLE}",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Authorization",
                            "value": f"Bearer {AIRTABLE_TOKEN}"
                        },
                        {
                            "name": "Content-Type",
                            "value": "application/json"
                        }
                    ]
                },
                "sendBody": True,
                "contentType": "raw",
                "rawContentType": "application/json",
                "body": "={{ JSON.stringify($json.payload) }}",
                "options": {
                    "batching": {
                        "batch": {
                            "batchSize": 1,
                            "batchInterval": 300
                        }
                    }
                }
            }
        },

        # --- Step 7: Telegram summary ---
        {
            "id": "telegram-send",
            "name": "Send Summary",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [1550, 500],
            "parameters": {
                "chatId": "YOUR_TELEGRAM_CHAT_ID",
                "text": "={{ $json.text }}",
                "additionalFields": {
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
            },
            "credentials": {
                "telegramApi": {
                    "id": "YOUR_TELEGRAM_CREDENTIAL_ID",
                    "name": "YOUR_TELEGRAM_BOT_NAME"
                }
            }
        }
    ],
    "connections": {
        "Schedule Trigger": {
            "main": [[
                {"node": "Get Channels", "type": "main", "index": 0},
                {"node": "Fetch Existing URLs", "type": "main", "index": 0}
            ]]
        },
        "Manual Trigger": {
            "main": [[
                {"node": "Get Channels", "type": "main", "index": 0},
                {"node": "Fetch Existing URLs", "type": "main", "index": 0}
            ]]
        },
        "Get Channels": {
            "main": [[{"node": "Extract Channels", "type": "main", "index": 0}]]
        },
        "Extract Channels": {
            "main": [[{"node": "Fetch RSS", "type": "main", "index": 0}]]
        },
        "Fetch RSS": {
            "main": [[{"node": "Parse & Analyze", "type": "main", "index": 0}]]
        },
        "Fetch Existing URLs": {
            "main": [[{"node": "Parse & Analyze", "type": "main", "index": 0}]]
        },
        "Parse & Analyze": {
            "main": [[{"node": "Route", "type": "main", "index": 0}]]
        },
        "Route": {
            "main": [
                [{"node": "Create Records", "type": "main", "index": 0}],
                [{"node": "Send Summary", "type": "main", "index": 0}]
            ]
        }
    },
    "settings": {
        "executionOrder": "v1"
    }
}

# === Deploy ===
print(f"Updating Viral Radar v2.0 ({WF_ID})...")

# Deactivate
try:
    req = urllib.request.Request(
        f"{N8N_URL}/api/v1/workflows/{WF_ID}/deactivate",
        data=b"", method="POST",
        headers={"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15):
        pass
    print("  Deactivated")
except:
    pass

# PUT update
payload = json.dumps(workflow_update).encode("utf-8")
req = urllib.request.Request(
    f"{N8N_URL}/api/v1/workflows/{WF_ID}",
    data=payload, method="PUT",
    headers={"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    result = json.loads(resp.read().decode("utf-8"))
    print(f"  Updated: {result.get('name')}")

# Activate
req = urllib.request.Request(
    f"{N8N_URL}/api/v1/workflows/{WF_ID}/activate",
    data=b"", method="POST",
    headers={"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    result = json.loads(resp.read().decode("utf-8"))
    print(f"  Active: {result.get('active')}")

print(f"\nWebhook: {N8N_URL}/webhook/viral-radar-run")
print("Nodes: Schedule Trigger → Get Channels → Extract → Fetch RSS → Parse → Route → Create Records / Send Telegram")
