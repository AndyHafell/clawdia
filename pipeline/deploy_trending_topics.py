#!/usr/bin/env python3
"""
Deploy Trending Topics Scout workflow to n8n.
Scrapes latest videos from Channel 1 & Channel 2 YouTube channels,
picks 3 most relevant trending topics for your channel's niche,
writes content angles, and sends a Telegram briefing at 7:00 AM daily.
"""

import json
import urllib.request
import os

# === CONFIG ===
N8N_URL = os.environ.get("N8N_URL", "https://YOUR_N8N_INSTANCE_URL")
N8N_API_KEY = os.environ.get("n8n_API_KEY", "YOUR_N8N_API_KEY")

# Airtable (for Backbone context)
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_PERSONAL_ACCESS_TOKEN", "YOUR_AIRTABLE_TOKEN")
AIRTABLE_BASE = "YOUR_AIRTABLE_BASE_ID"

# Claude API
CLAUDE_KEY = os.environ.get("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")

# Telegram
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")

# YouTube channels
CHANNELS = {
    "Channel 1": {
        "id": "YOUR_COMPETITOR_CHANNEL_ID_1",
        "rss": "https://www.youtube.com/feeds/videos.xml?channel_id=YOUR_COMPETITOR_CHANNEL_ID_1"
    },
    "Channel 2": {
        "id": "YOUR_COMPETITOR_CHANNEL_ID_2",
        "rss": "https://www.youtube.com/feeds/videos.xml?channel_id=YOUR_COMPETITOR_CHANNEL_ID_2"
    }
}

# Airtable Trending Topics table
TRENDING_TABLE = "YOUR_TRENDING_TABLE_ID"

# === CODE NODE: Parse RSS feeds + Claude analysis + save to Airtable + build message ===
CODE_BUILD_BRIEFING = r"""
// ===== TRENDING TOPICS SCOUT v1.1 =====
// Parses YouTube RSS feeds from Channel 1 & Channel 2,
// sends to Claude to pick top 3 topics + content angles + fit scores,
// saves each topic to Airtable Trending Topics table,
// formats a Telegram message.

const claudeKey = '""" + CLAUDE_KEY + r"""';
const airtableToken = '""" + AIRTABLE_TOKEN + r"""';
const baseId = '""" + AIRTABLE_BASE + r"""';
const trendingTable = '""" + TRENDING_TABLE + r"""';

// ===== DATE =====
const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const now = new Date();
const dateStr = days[now.getDay()] + ', ' + months[now.getMonth()] + ' ' + now.getDate();
const todayISO = now.toISOString().split('T')[0];

// ===== PARSE BOTH RSS FEEDS =====
const rssNodes = ['Fetch Channel 1 RSS', 'Fetch Channel 2 RSS'];
const channelNames = ['Channel 1', 'Channel 2'];
const allVideos = [];

for (let i = 0; i < rssNodes.length; i++) {
  try {
    const rssData = $(rssNodes[i]).first().json;
    let xmlStr = typeof rssData === 'string' ? rssData : (rssData.data || JSON.stringify(rssData));

    if (typeof rssData === 'object' && !rssData.data) {
      const rawItem = $(rssNodes[i]).first();
      if (rawItem && rawItem.binary && rawItem.binary.data) {
        xmlStr = Buffer.from(rawItem.binary.data.data, 'base64').toString('utf-8');
      }
    }

    const entryRegex = /<entry>([\s\S]*?)<\/entry>/g;
    let match;
    let count = 0;
    while ((match = entryRegex.exec(xmlStr)) !== null && count < 5) {
      const entry = match[1];
      const titleMatch = entry.match(/<title>([\s\S]*?)<\/title>/);
      const videoIdMatch = entry.match(/<yt:videoId>([\s\S]*?)<\/yt:videoId>/);
      const publishedMatch = entry.match(/<published>([\s\S]*?)<\/published>/);
      const descMatch = entry.match(/<media:description>([\s\S]*?)<\/media:description>/);

      if (titleMatch && videoIdMatch) {
        const pubDate = publishedMatch ? new Date(publishedMatch[1]) : new Date(0);
        const daysSincePublished = (now - pubDate) / (1000 * 60 * 60 * 24);

        if (daysSincePublished <= 7) {
          allVideos.push({
            title: titleMatch[1].trim(),
            videoId: videoIdMatch[1].trim(),
            url: 'https://youtube.com/watch?v=' + videoIdMatch[1].trim(),
            channel: channelNames[i],
            published: publishedMatch ? publishedMatch[1] : '',
            daysAgo: Math.round(daysSincePublished),
            description: descMatch ? descMatch[1].trim().substring(0, 300) : ''
          });
          count++;
        }
      }
    }
  } catch (e) {
    // Continue with other feeds
  }
}

if (allVideos.length === 0) {
  return [{ json: { message: '⚠️ <b>Trending Topics Scout</b>\n\nNo recent videos found from Channel 1 or Channel 2 in the last 7 days. They might be on a break!' } }];
}

// ===== GET BACKBONE FOR CONTEXT =====
let backboneSummary = '';
try {
  const backboneResp = await this.helpers.httpRequest({
    method: 'GET',
    url: 'https://api.airtable.com/v0/' + baseId + '/YOUR_BACKBONE_TABLE_ID',
    headers: { 'Authorization': 'Bearer ' + airtableToken }
  });

  const backbone = {};
  for (const rec of (backboneResp.records || [])) {
    const section = rec.fields['Section'] || 'Unknown';
    if (!backbone[section]) backbone[section] = [];
    backbone[section].push({ field: rec.fields['Field'] || '', value: rec.fields['Value'] || '' });
  }
  for (const [section, items] of Object.entries(backbone)) {
    backboneSummary += '\n## ' + section + '\n';
    for (const item of items) {
      backboneSummary += '- ' + item.field + ': ' + item.value + '\n';
    }
  }
} catch (e) {
  backboneSummary = 'AI automation YouTube channel helping people build AI agents and automation systems.';
}

// ===== BUILD VIDEO LIST FOR CLAUDE =====
let videoList = '';
for (const v of allVideos) {
  videoList += `- "${v.title}" by ${v.channel} (${v.daysAgo}d ago)\n  URL: ${v.url}\n  Description: ${v.description}\n\n`;
}

// ===== CLAUDE: PICK TOP 3 + CONTENT ANGLES + FIT SCORES (JSON) =====
const jsonPrompt = `You are a strategic AI companion for the YouTube channel "YOUR_CHANNEL_NAME".

CHANNEL BACKBONE (business identity):
${backboneSummary}

YOUR NICHE: [Describe your channel niche here]. Your audience is [describe your target audience].

YOUR TASK:
1. Analyze the recent videos from Channel 1 and Channel 2
2. Identify the TOP 3 most trending/relevant topics for your channel
3. For each topic, write a content angle and rate how well it fits the channel's content style

FIT SCORE (1-10):
- 10 = Perfect fit, MUST make this video, the audience is dying for it
- 8-9 = Strong fit, clearly in his wheelhouse, high audience demand
- 6-7 = Good fit, relevant to his niche but not a slam dunk
- 4-5 = Tangential, could work with the right angle but not core content
- 1-3 = Poor fit, outside his niche or audience wouldn't care

RULES:
- Extract the UNDERLYING TOPIC, don't just summarize the video
- Content angles must be specific, actionable, different from the source
- If multiple videos cover the same topic, that's a STRONG trending signal
- Be honest with fit scores — not everything is a 10

RESPOND IN EXACTLY THIS JSON FORMAT (no other text):
{"topics":[{"topic":"Topic Name","sourceTitle":"Video title","sourceChannel":"Channel name","sourceUrl":"https://youtube.com/watch?v=...","contentAngle":"2-3 sentences — specific video idea for the channel","fitScore":7,"fitReasoning":"1 sentence why this score"}]}`;

let parsedTopics = [];
let topicsSection = '';

try {
  const claudeResp = await this.helpers.httpRequest({
    method: 'POST',
    url: 'https://api.anthropic.com/v1/messages',
    headers: {
      'x-api-key': claudeKey,
      'anthropic-version': '2023-06-01',
      'Content-Type': 'application/json'
    },
    body: {
      model: 'claude-sonnet-4-20250514',
      max_tokens: 2000,
      system: jsonPrompt,
      messages: [{
        role: 'user',
        content: 'Here are the recent videos from the last 7 days:\n\n' + videoList + '\n\nPick the top 3 trending topics, write content angles, and rate each fit score 1-10.'
      }]
    }
  });

  const responseText = claudeResp.content[0].text;
  const jsonMatch = responseText.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    const parsed = JSON.parse(jsonMatch[0]);
    parsedTopics = (parsed.topics || []).slice(0, 3);
  }
} catch (e) {
  topicsSection = '⚠️ Could not analyze topics: ' + e.message;
}

// ===== SAVE TO AIRTABLE =====
if (parsedTopics.length > 0) {
  try {
    const records = parsedTopics.map(t => ({
      fields: {
        'Topic': t.topic,
        'Content Angle': t.contentAngle,
        'Source Video': t.sourceTitle,
        'Source Channel': t.sourceChannel,
        'Source URL': t.sourceUrl,
        'Fit Score': Math.min(Math.max(Math.round(t.fitScore || 5), 1), 10),
        'Fit Reasoning': t.fitReasoning || '',
        'Scouted Date': todayISO,
        'Used': false
      }
    }));

    await this.helpers.httpRequest({
      method: 'POST',
      url: 'https://api.airtable.com/v0/' + baseId + '/' + trendingTable,
      headers: {
        'Authorization': 'Bearer ' + airtableToken,
        'Content-Type': 'application/json'
      },
      body: { records }
    });
  } catch (e) {
    // Airtable save failed — still send Telegram
  }

  // ===== BUILD TELEGRAM MESSAGE FROM PARSED DATA =====
  const fitEmoji = (score) => {
    if (score >= 9) return '🟢';
    if (score >= 7) return '🟡';
    if (score >= 5) return '🟠';
    return '🔴';
  };

  topicsSection = parsedTopics.map((t, i) => {
    return `🔥 <b>Topic ${i+1}: ${t.topic}</b>\n` +
      `📺 Source: <a href="${t.sourceUrl}">${t.sourceTitle}</a> — ${t.sourceChannel}\n` +
      `💡 <b>Content Angle:</b> ${t.contentAngle}\n` +
      `${fitEmoji(t.fitScore)} <b>Fit Score: ${t.fitScore}/10</b> — <i>${t.fitReasoning}</i>`;
  }).join('\n\n');
}

// ===== BUILD FINAL MESSAGE =====
const header = `🎯 <b>Trending Topics Scout</b>\n☀️ <b>${dateStr}</b>\n\n`;
const sourceCount = `📊 <i>Scanned ${allVideos.length} recent videos from Channel 1 & Channel 2</i>\n\n`;
const divider = '━━━━━━━━━━━━━━━━━━━━\n\n';

const message = header + sourceCount + divider + topicsSection;

// Handle Telegram 4096 char limit
const TG_LIMIT = 4096;
if (message.length <= TG_LIMIT) {
  return [{ json: { message } }];
}

// Split at topic boundaries
const messages = [];
const topics = message.split(/(?=🔥 <b>Topic )/);
if (topics.length > 1) {
  let current = topics[0];
  for (let i = 1; i < topics.length; i++) {
    if ((current + topics[i]).length > TG_LIMIT) {
      messages.push(current.trim());
      current = topics[i];
    } else {
      current += topics[i];
    }
  }
  messages.push(current.trim());
} else {
  let remaining = message;
  while (remaining.length > TG_LIMIT) {
    let splitAt = remaining.lastIndexOf('\n', TG_LIMIT - 100);
    if (splitAt < 0) splitAt = TG_LIMIT - 100;
    messages.push(remaining.substring(0, splitAt).trim());
    remaining = remaining.substring(splitAt).trim();
  }
  messages.push(remaining);
}

return messages.map(m => ({ json: { message: m } }));
"""


def build_workflow():
    """Build the n8n workflow JSON."""
    return {
        "name": "Trending Topics Scout v1.0",
        "nodes": [
            # 1. Schedule Trigger — 7:00 AM Bangkok time
            {
                "parameters": {
                    "rule": {
                        "interval": [
                            {
                                "triggerAtHour": 7,
                                "triggerAtMinute": 0
                            }
                        ]
                    }
                },
                "id": "schedule-trigger",
                "name": "Daily 7AM Trigger",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [200, 300]
            },
            # 2. Fetch Channel 1 RSS
            {
                "parameters": {
                    "url": CHANNELS["Channel 1"]["rss"],
                    "options": {
                        "response": {
                            "response": {
                                "responseFormat": "text"
                            }
                        }
                    }
                },
                "id": "fetch-nick-rss",
                "name": "Fetch Channel 1 RSS",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [500, 200]
            },
            # 3. Fetch Channel 2 RSS
            {
                "parameters": {
                    "url": CHANNELS["Channel 2"]["rss"],
                    "options": {
                        "response": {
                            "response": {
                                "responseFormat": "text"
                            }
                        }
                    }
                },
                "id": "fetch-nate-rss",
                "name": "Fetch Channel 2 RSS",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [500, 400]
            },
            # 4. Build Briefing (Code node — does Claude API call internally)
            {
                "parameters": {
                    "jsCode": CODE_BUILD_BRIEFING
                },
                "id": "build-briefing",
                "name": "Build Trending Briefing",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [850, 300]
            },
            # 5. Send Telegram
            {
                "parameters": {
                    "chatId": TELEGRAM_CHAT_ID,
                    "text": "={{ $json.message }}",
                    "additionalFields": {
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True
                    }
                },
                "id": "send-telegram",
                "name": "Send Telegram",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1.2,
                "position": [1150, 300],
                "credentials": {
                    "telegramApi": {
                        "id": "YOUR_TELEGRAM_CREDENTIAL_ID",
                        "name": "YOUR_TELEGRAM_BOT_NAME"
                    }
                }
            }
        ],
        "connections": {
            "Daily 7AM Trigger": {
                "main": [
                    [
                        {"node": "Fetch Channel 1 RSS", "type": "main", "index": 0},
                        {"node": "Fetch Channel 2 RSS", "type": "main", "index": 0}
                    ]
                ]
            },
            "Fetch Channel 1 RSS": {
                "main": [
                    [
                        {"node": "Build Trending Briefing", "type": "main", "index": 0}
                    ]
                ]
            },
            "Fetch Channel 2 RSS": {
                "main": [
                    [
                        {"node": "Build Trending Briefing", "type": "main", "index": 0}
                    ]
                ]
            },
            "Build Trending Briefing": {
                "main": [
                    [
                        {"node": "Send Telegram", "type": "main", "index": 0}
                    ]
                ]
            }
        },
        "settings": {
            "executionOrder": "v1",
            "timezone": "Asia/Bangkok"
        }
    }


def deploy():
    """Deploy workflow to n8n via API."""
    workflow = build_workflow()

    # First, try to find existing workflow by name
    print("🔍 Checking for existing Trending Topics Scout workflow...")
    req = urllib.request.Request(
        f"{N8N_URL}/api/v1/workflows?limit=100",
        headers={"X-N8N-API-KEY": N8N_API_KEY}
    )
    resp = urllib.request.urlopen(req)
    existing = json.loads(resp.read().decode())

    existing_id = None
    for wf in existing.get("data", []):
        if "Trending Topics Scout" in wf.get("name", ""):
            existing_id = wf["id"]
            print(f"   Found existing workflow: {existing_id}")
            break

    if existing_id:
        # Update existing
        print(f"📝 Updating workflow {existing_id}...")
        workflow_json = json.dumps(workflow).encode()
        req = urllib.request.Request(
            f"{N8N_URL}/api/v1/workflows/{existing_id}",
            data=workflow_json,
            headers={
                "X-N8N-API-KEY": N8N_API_KEY,
                "Content-Type": "application/json"
            },
            method="PUT"
        )
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode())
        wf_id = result["id"]
        print(f"   ✅ Updated: {wf_id}")
    else:
        # Create new
        print("🆕 Creating new workflow...")
        workflow_json = json.dumps(workflow).encode()
        req = urllib.request.Request(
            f"{N8N_URL}/api/v1/workflows",
            data=workflow_json,
            headers={
                "X-N8N-API-KEY": N8N_API_KEY,
                "Content-Type": "application/json"
            },
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode())
        wf_id = result["id"]
        print(f"   ✅ Created: {wf_id}")

    # Activate the workflow (n8n uses POST /activate, not PATCH)
    print("⚡ Activating workflow...")
    req = urllib.request.Request(
        f"{N8N_URL}/api/v1/workflows/{wf_id}/activate",
        data=b"{}",
        headers={
            "X-N8N-API-KEY": N8N_API_KEY,
            "Content-Type": "application/json"
        },
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    active_status = result.get("active", False)
    print(f"   Active: {active_status}")

    print(f"\n🎯 Trending Topics Scout deployed!")
    print(f"   Workflow ID: {wf_id}")
    print(f"   Schedule: Daily at 7:00 AM (Asia/Bangkok)")
    print(f"   Sources: Channel 1 + Channel 2 (YouTube RSS)")
    print(f"   Output: Top 3 trending topics → Telegram")
    print(f"   URL: {N8N_URL}/workflow/{wf_id}")

    return wf_id


if __name__ == "__main__":
    deploy()
