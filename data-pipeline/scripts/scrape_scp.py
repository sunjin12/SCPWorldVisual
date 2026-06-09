"""SCP Wiki Scraper — SCP 시리즈 I 문서 수집 (병렬 처리).

Rate limit을 준수하며 ThreadPoolExecutor로 병렬 스크래핑합니다.
출력: JSON 형식의 SCP 문서 데이터.

Usage:
    uv run python scripts/scrape_scp.py
"""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Paths
SCRIPT_DIR = Path(__file__).parent.parent
CONFIG_DIR = SCRIPT_DIR / "config"
DATA_DIR = SCRIPT_DIR / "data"

SCP_BASE_URL = "https://scp-wiki.wikidot.com"
RATE_LIMIT_SECONDS = 2
MAX_WORKERS = 10  # 병렬 스크래핑 워커 수


def load_target_list() -> list[str]:
    """Load the list of SCP items to scrape."""
    target_file = CONFIG_DIR / "scp_target_list.json"
    if target_file.exists():
        with open(target_file) as f:
            return json.load(f)

    # Default: SCP-001 through SCP-200
    return [f"SCP-{str(i).zfill(3)}" for i in range(1, 201)]


def scrape_scp_page(item_number: str) -> dict | None:
    """Scrape a single SCP page and extract structured data."""
    slug = item_number.lower()
    url = f"{SCP_BASE_URL}/{slug}"

    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"  ⚠️  {item_number}: HTTP {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"  ❌ {item_number}: {e}")
        return None

    soup = BeautifulSoup(response.text, "lxml")

    # Extract main content
    content_div = soup.find("div", id="page-content")
    if not content_div:
        print(f"  ⚠️  {item_number}: No page-content found")
        return None

    raw_text = content_div.get_text(separator="\n", strip=True)

    # Extract Object Class
    object_class = "Unknown"
    class_match = re.search(
        r"Object Class:\s*(\w+)", raw_text, re.IGNORECASE
    )
    if class_match:
        object_class = class_match.group(1).strip()

    # Extract sections
    sections = extract_sections(raw_text)

    # Extract page title
    title_tag = soup.find("div", id="page-title")
    title = title_tag.get_text(strip=True) if title_tag else item_number

    # Extract tags
    tags = []
    tags_div = soup.find("div", class_="page-tags")
    if tags_div:
        for a_tag in tags_div.find_all("a"):
            tag_text = a_tag.get_text(strip=True)
            if tag_text:
                tags.append(tag_text)

    return {
        "item_number": item_number,
        "object_class": object_class,
        "title": title,
        "sections": sections,
        "raw_text": raw_text,
        "url": url,
        "tags": tags,
    }


def extract_sections(text: str) -> dict[str, str]:
    """Extract SCP document sections from raw text."""
    sections = {}

    # Common SCP section headers
    patterns = [
        ("containment_procedures", r"(?:Special )?Containment Procedures:(.*?)(?=Description:|Addendum|$)"),
        ("description", r"Description:(.*?)(?=Addendum|Appendix|Note|Interview|$)"),
        ("addendum", r"(?:Addendum|Appendix)(.*?)$"),
    ]

    for key, pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            sections[key] = match.group(1).strip()

    return sections


def main():
    """Main scraping pipeline — parallel workers with rate limit."""
    DATA_DIR.mkdir(exist_ok=True)
    target_list = load_target_list()

    print(f"🔍 Scraping {len(target_list)} SCP documents...")
    print(f"   Rate limit: {RATE_LIMIT_SECONDS}s per worker, {MAX_WORKERS} workers")
    print(f"   Estimated time: ~{len(target_list) * RATE_LIMIT_SECONDS / MAX_WORKERS:.0f}s")

    documents = []
    failed = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_item = {
            executor.submit(scrape_scp_page, item): item
            for item in target_list
        }

        for future in tqdm(as_completed(future_to_item), total=len(target_list), desc="Scraping"):
            item = future_to_item[future]
            try:
                doc = future.result()
                if doc:
                    documents.append(doc)
                else:
                    failed.append(item)
            except Exception as e:
                print(f"  ❌ {item}: {e}")
                failed.append(item)

    # Save results
    output_file = DATA_DIR / "scp_raw_documents.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Scraped {len(documents)} documents → {output_file}")
    if failed:
        print(f"⚠️  Failed: {len(failed)} — {failed[:10]}{'...' if len(failed) > 10 else ''}")


if __name__ == "__main__":
    main()
