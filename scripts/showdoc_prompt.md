Create today's Show Doc. Follow the SHOW_DOC_PROCESS_SOP.md workflow exactly. Here's the step-by-step:

1. Read `skills/SHOW_DOC_PROCESS_SOP.md` and `skills/FORMAT_SELECTION_SOP.md` first.

2. Pull today's top outliers from the Viral Videos Airtable table (`YOUR_VIRAL_VIDEOS_TABLE_ID` in base `YOUR_AIRTABLE_BASE_ID`). Filter for videos published in the last 3 days, sort by Outlier Score descending (fall back to Views if Outlier Score is sparse). Pick the top 3 topics — if topics overlap, merge and pick the next one. Use the Airtable API with the token from `.env`.

3. Match each topic to a Hall of Fame format from the Hall of Fame table (`YOUR_HALL_OF_FAME_TABLE_ID`). Follow the Format Selection SOP decision matrix.

4. Research each topic deeply. For each one:
   - Find the main source (announcement, blog post, article)
   - Search Reddit (r/singularity, r/ClaudeAI, r/artificial, r/technology)
   - Search X/Twitter for viral posts and hot takes
   - Search tech press (TechCrunch, The Verge, VentureBeat, CNBC, Ars Technica)
   - Find proof points: stats, quotes, data
   - Find demos and tools the creator can show on screen

5. Write the full show doc content for each topic following the SOP structure exactly:
   - SOURCES section (all original creators with video title, views, date, link)
   - 7 TITLES
   - THUMBNAIL IDEAS
   - SAY THIS (word-for-word spoken intro using 4P framework)
   - 4P FRAMEWORK (Proof, Promise, Problem, Path)
   - 7 HOOKS (How to, Statement, Benefit, Fact, Negative, Personal/Emotional, Story)
   - TRANSFORMATION GOAL (specific: "you will have [X]", not "you will learn about X")
   - WALKTHROUGH (format-specific: STEPS for Build-Along, ACTS for Deep Dive, POINTS for Opportunity)
   - SUMMARY (details, why it matters, key stats/quotes)

6. Write a BONUS section at the bottom with 5-10 extra topic ideas from remaining outliers and tech news.

7. Create a new tab in the Master Show Doc (`YOUR_SHOW_DOC_MASTER_ID`) for today's date using `create_master_showdoc.py` and `format_showdoc.py` as reference for Google Docs API formatting. Follow the formatting standards:
   - Pastel blue minimal palette
   - All URLs as clickable hyperlinks
   - Proper heading structure (H1=title, H2=topics, H4=emoji sections)
   - Actual Google Docs bullets (not text with bullet characters)
   - Apply formatting in correct order: insert text -> styles -> bullets -> headings -> hyperlinks

8. Create an Airtable record in the Show Docs table (`YOUR_SHOW_DOCS_TABLE_ID`) with: Title, Date, Google Doc URL, Topic names, Formats, and Status = "Draft".

9. At the very end, send a Telegram notification using this curl command (replace the URL and message):
   ```
   curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
     -d "chat_id=${TELEGRAM_CHAT_ID}" \
     -d "parse_mode=Markdown" \
     -d "text=message_here"
   ```
   The message should include: today's date, the 3 topic names, and the Google Doc link.

The .env file has TELEGRAM credentials as:
- Telegram_access_token
- Telegram_chat_id

Today's date is $(date +"%B %d, %Y").
