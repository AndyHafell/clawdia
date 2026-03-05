#!/usr/bin/env python3
"""
Embed top-scored thumbnails into a Google Doc content doc tab.

Called after thumbnail_service.py produces results and after
the content doc text has been formatted.

Usage (programmatic):
    from embed_thumbnails import embed_thumbnails_in_doc
    embed_thumbnails_in_doc(doc_id, tab_id, top_3)

Usage (CLI — for testing):
    python3 embed_thumbnails.py --doc-id DOC_ID --tab-id TAB_ID --urls URL1 URL2 URL3
"""

import pickle
import json
import requests
import os
import re
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

TOKEN_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "youtube_token.pickle")


def get_google_creds():
    """Load and refresh Google OAuth credentials."""
    with open(TOKEN_PATH, "rb") as f:
        creds = pickle.load(f)
    if not creds.valid:
        creds.refresh(Request())
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
    return creds


def _get_embeddable_url(drive_url: str) -> str:
    """Convert a Drive URL to one that works with insertInlineImage.

    Tries export=view format first. Falls back to lh3 direct link.
    """
    if not drive_url:
        return drive_url

    # Extract file ID from various URL formats
    file_id = None
    if "id=" in drive_url:
        file_id = drive_url.split("id=")[-1].split("&")[0]
    elif "/d/" in drive_url:
        file_id = drive_url.split("/d/")[1].split("/")[0]
    elif "/file/" in drive_url:
        file_id = drive_url.split("/file/")[1].split("/")[0]

    if file_id:
        return f"https://lh3.googleusercontent.com/d/{file_id}"
    return drive_url


def find_section_end(doc_id: str, tab_id: str, section_prefix: str, headers: dict) -> int:
    """Find the end index of a section in a Google Doc tab.

    Reads the doc, finds the section by prefix, then finds where the next
    section starts (the next heading). Returns the index just before it.
    """
    resp = requests.get(
        f"https://docs.googleapis.com/v1/documents/{doc_id}?includeTabsContent=true",
        headers=headers,
    )
    if resp.status_code != 200:
        print(f"ERROR reading doc: {resp.status_code}")
        return None

    doc = resp.json()

    for tab in doc.get("tabs", []):
        if tab.get("tabProperties", {}).get("tabId") == tab_id:
            content = tab.get("documentTab", {}).get("body", {}).get("content", [])
            found_section = False
            section_end = None

            for elem in content:
                para = elem.get("paragraph", {})
                text_parts = []
                for pe in para.get("elements", []):
                    text_parts.append(pe.get("textRun", {}).get("content", ""))
                full_text = "".join(text_parts).strip()

                if full_text.startswith(section_prefix):
                    found_section = True
                    continue

                if found_section:
                    named_style = para.get("paragraphStyle", {}).get("namedStyleType", "")
                    if named_style in ("HEADING_1", "HEADING_2", "HEADING_3"):
                        return elem.get("startIndex", 0)
                    # Track the end of content in this section
                    end_idx = elem.get("endIndex")
                    if end_idx:
                        section_end = end_idx

            # Section was the last one in the doc
            if found_section and section_end:
                return section_end

    return None


def embed_thumbnails_in_doc(
    doc_id: str,
    tab_id: str,
    top_3,
    image_width_pt: float = 320,
    image_height_pt: float = 180,
) -> bool:
    """Embed top 3 thumbnail images into the doc's THUMBNAIL IDEAS section.

    Each thumbnail gets:
    1. An inline image (320pt x 180pt, 16:9)
    2. A text line: "Must-Click Score: X/10 — [reasoning]"

    Args:
        doc_id: Google Doc ID
        tab_id: Tab ID within the doc
        top_3: List of ScoredThumbnail objects (or dicts with score, reasoning, drive_url)
        image_width_pt: Image width in points (default 320 = ~4.4 inches)
        image_height_pt: Image height in points (default 180)

    Returns:
        True if embedding succeeded, False otherwise
    """
    creds = get_google_creds()
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }

    # Find insertion point (end of THUMBNAIL IDEAS section)
    insert_point = find_section_end(doc_id, tab_id, "\U0001f5bc", headers)
    if insert_point is None:
        # Try without emoji (in case of different encoding)
        insert_point = find_section_end(doc_id, tab_id, "THUMBNAIL IDEAS", headers)

    if insert_point is None:
        print("WARNING: Could not find THUMBNAIL IDEAS section. Skipping embed.")
        print("Top 3 Drive URLs for manual insertion:")
        for t in top_3:
            url = t.drive_url if hasattr(t, "drive_url") else t.get("drive_url", "")
            score = t.score if hasattr(t, "score") else t.get("score", "?")
            print(f"  Score {score}/10: {url}")
        return False

    print(f"  Inserting thumbnails at index {insert_point}")

    # Build batch requests in REVERSE order (bottom to top) to avoid index shifts
    # Each thumbnail block: \n + image + \n + score text + \n
    batch_requests = []

    for thumb in reversed(top_3):
        score = thumb.score if hasattr(thumb, "score") else thumb.get("score", "?")
        reasoning = thumb.reasoning if hasattr(thumb, "reasoning") else thumb.get("reasoning", "")
        drive_url = thumb.drive_url if hasattr(thumb, "drive_url") else thumb.get("drive_url", "")
        label = thumb.label if hasattr(thumb, "label") else thumb.get("label", "")

        embeddable_url = _get_embeddable_url(drive_url)

        if not embeddable_url:
            print(f"  WARNING: No URL for {label} — skipping")
            continue

        # Insert in reverse order (bottom-to-top) at the same index.
        # Final visual order per thumbnail:
        #   [blank line]
        #   [image on its own line]
        #   Must-Click Score: X/10 — reasoning

        # 1. Score text (appears last visually, inserted first)
        score_text = f"Must-Click Score: {score}/10 — {reasoning}\n"
        batch_requests.append({
            "insertText": {
                "location": {"index": insert_point, "tabId": tab_id},
                "text": score_text,
            }
        })

        # 2. Newline after image (puts image on its own paragraph)
        batch_requests.append({
            "insertText": {
                "location": {"index": insert_point, "tabId": tab_id},
                "text": "\n",
            }
        })

        # 3. Image (on its own line thanks to surrounding newlines)
        batch_requests.append({
            "insertInlineImage": {
                "location": {"index": insert_point, "tabId": tab_id},
                "uri": embeddable_url,
                "objectSize": {
                    "height": {"magnitude": image_height_pt, "unit": "PT"},
                    "width": {"magnitude": image_width_pt, "unit": "PT"},
                },
            }
        })

        # 4. Newline before image (separator from previous content)
        batch_requests.append({
            "insertText": {
                "location": {"index": insert_point, "tabId": tab_id},
                "text": "\n",
            }
        })

    if not batch_requests:
        print("WARNING: No thumbnail URLs available for embedding.")
        return False

    # Send batch update
    resp = requests.post(
        f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate",
        headers=headers,
        json={"requests": batch_requests},
    )

    if resp.status_code != 200:
        print(f"ERROR embedding thumbnails: {resp.status_code}")
        error_text = resp.text[:500]
        print(f"  {error_text}")

        # If lh3 URL failed, try export=view format
        if "lh3" in str(batch_requests):
            print("  Retrying with export=view URL format...")
            for req in batch_requests:
                if "insertInlineImage" in req:
                    uri = req["insertInlineImage"]["uri"]
                    if "lh3.googleusercontent.com" in uri:
                        file_id = uri.split("/d/")[-1]
                        req["insertInlineImage"]["uri"] = f"https://drive.google.com/uc?export=view&id={file_id}"

            resp = requests.post(
                f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate",
                headers=headers,
                json={"requests": batch_requests},
            )
            if resp.status_code != 200:
                print(f"  Retry also failed: {resp.status_code}")
                return False

    print(f"  Embedded {len(top_3)} thumbnails in THUMBNAIL IDEAS section.")

    # Apply bullet formatting to score text lines
    _apply_score_bullets(doc_id, tab_id, headers, len(top_3))

    return True


def _apply_score_bullets(doc_id: str, tab_id: str, headers: dict, count: int):
    """Apply bullet formatting to the Must-Click Score text lines."""
    # Re-read doc to find actual positions of score text
    resp = requests.get(
        f"https://docs.googleapis.com/v1/documents/{doc_id}?includeTabsContent=true",
        headers=headers,
    )
    if resp.status_code != 200:
        return

    doc = resp.json()
    bullet_requests = []

    for tab in doc.get("tabs", []):
        if tab.get("tabProperties", {}).get("tabId") == tab_id:
            content = tab.get("documentTab", {}).get("body", {}).get("content", [])
            for elem in content:
                para = elem.get("paragraph", {})
                text_parts = []
                for pe in para.get("elements", []):
                    text_parts.append(pe.get("textRun", {}).get("content", ""))
                full_text = "".join(text_parts)
                if full_text.startswith("Must-Click Score:"):
                    start = elem.get("startIndex", 0)
                    end = elem.get("endIndex", start + 1)
                    bullet_requests.append({
                        "createParagraphBullets": {
                            "range": {
                                "startIndex": start,
                                "endIndex": end,
                                "tabId": tab_id,
                            },
                            "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                        }
                    })

    if bullet_requests:
        requests.post(
            f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate",
            headers=headers,
            json={"requests": bullet_requests},
        )
        print(f"  Applied bullet formatting to {len(bullet_requests)} score lines")


# ─── CLI (for testing) ───────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Embed thumbnails into a Google Doc")
    parser.add_argument("--doc-id", required=True, help="Google Doc ID")
    parser.add_argument("--tab-id", required=True, help="Tab ID")
    parser.add_argument("--urls", nargs="+", required=True, help="Drive URLs of thumbnails")
    parser.add_argument("--scores", nargs="*", default=None, help="Scores (1-10) for each URL")
    args = parser.parse_args()

    # Build mock top_3
    top_3 = []
    for i, url in enumerate(args.urls[:3]):
        score = float(args.scores[i]) if args.scores and i < len(args.scores) else 7
        top_3.append({
            "label": f"Test_{i+1}",
            "score": score,
            "reasoning": "Manual test",
            "drive_url": url,
        })

    success = embed_thumbnails_in_doc(args.doc_id, args.tab_id, top_3)
    if success:
        print("Embedding complete.")
    else:
        print("Embedding failed.")
