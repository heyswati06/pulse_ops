"""
ingest_confluence.py
────────────────────
Fetches Confluence pages by page ID.
Strips HTML. Chunks into 300-word segments.
Stores to MongoDB KB.

Owner: [ASSIGNED_TO]

HOW TO GET PAGE IDs:
    Open the Confluence page in your browser.
    Look at the URL: /pages/1234567890/Page+Title
    That number is the page ID.

    Ask Joel for the right page IDs:
    - Cyberflow runbook page
    - FOSS scan guide page
    - Deployment troubleshooting page
    - Any DevOps FAQ page

HOW TO RUN:
    python ingestion/ingest_confluence.py
"""

import requests
from bs4 import BeautifulSoup

from config import CONFLUENCE_URL, CONFLUENCE_TOKEN
from knowledge_base.schema import make_kb_document
from knowledge_base.store import insert_many, clear_source
from knowledge_base.chunker import clean_text, chunk_text

# ── CONFIG — edit these ───────────────────────────────────
# Joel gives you these page IDs
# Format: { "page_id": "topic label for tagging" }
CONFLUENCE_PAGES = {
    "5818866217": "devops-kb",           # Replace with your real page IDs
    # "1234567890": "cyberflow-runbook",
    # "9876543210": "foss-guide",
    # "1111111111": "deployment-troubleshooting",
}
# ─────────────────────────────────────────────────────────


def get_headers():
    return {
        "Authorization": f"Bearer {CONFLUENCE_TOKEN}",
        "Content-Type":  "application/json",
    }


def fetch_page(page_id: str) -> tuple:
    """
    Fetch a Confluence page by ID.
    Returns (title, raw_html) or (None, None) on failure.
    """
    url = f"{CONFLUENCE_URL}/rest/api/content/{page_id}"
    params = {"expand": "body.storage"}

    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=10)
        response.raise_for_status()
        data  = response.json()
        title = data.get("title", "Unknown Page")
        html  = data["body"]["storage"]["value"]
        print(f"  [confluence] Fetched page: '{title}' (id={page_id})")
        return title, html

    except Exception as e:
        print(f"  [confluence] ERROR fetching page {page_id}: {e}")
        return None, None


def html_to_text(raw_html: str) -> str:
    """Strip HTML tags, return clean plain text."""
    soup = BeautifulSoup(raw_html, "lxml")
    return soup.get_text(separator="\n", strip=True)


def ingest_confluence():
    """
    Main ingestion function.
    Run once before Week 2 demo.
    """
    print("\n[confluence] Starting Confluence ingestion...")
    print(f"[confluence] Pages to process: {list(CONFLUENCE_PAGES.keys())}\n")

    clear_source("confluence")

    all_docs = []

    for page_id, topic in CONFLUENCE_PAGES.items():
        title, raw_html = fetch_page(page_id)

        if not raw_html:
            continue

        plain_text = html_to_text(raw_html)
        cleaned    = clean_text(plain_text)
        chunks     = chunk_text(cleaned, chunk_size=300)

        print(f"  [confluence] '{title}' → {len(chunks)} chunks")

        for chunk in chunks:
            doc = make_kb_document(
                text=chunk,
                source="confluence",
                error_type="general",
                severity=None,
                tags=[topic, "runbook", "confluence", title.lower().replace(" ", "-")],
                raw_reference=f"{CONFLUENCE_URL}/pages/{page_id}"
            )
            all_docs.append(doc)

    inserted = insert_many(all_docs)
    print(f"\n[confluence] Done. {inserted} documents stored to MongoDB.\n")


if __name__ == "__main__":
    ingest_confluence()
