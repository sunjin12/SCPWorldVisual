"""SCP Document Preprocessor — Clean, chunk, and prepare for embedding.

Reads raw scraped documents and produces chunks with separated metadata.

Usage:
    uv run python scripts/preprocess.py
"""

import json
import re
from pathlib import Path

import tiktoken

SCRIPT_DIR = Path(__file__).parent.parent
DATA_DIR = SCRIPT_DIR / "data"

# Chunking parameters (qwen3.5:2b 최적화)
CHUNK_SIZE = 768       # tokens (512 → 768, 더 풍부한 컨텍스트)
CHUNK_OVERLAP = 128    # tokens (64 → 128, 경계 정보 손실 방지)
MIN_CHUNK_LENGTH = 100 # chars (50 → 100, 잡음 제거)
ENCODING_NAME = "cl100k_base"  # tiktoken encoding


def clean_wikidot_markup(text: str) -> str:
    """Remove Wikidot-specific markup and noise."""
    # Remove [[module]], [[collapsible]], [[footnote]] etc.
    text = re.sub(r"\[\[.*?\]\]", "", text)
    # Remove [[/...]] closing tags
    text = re.sub(r"\[\[/.*?\]\]", "", text)
    # Remove +++ / ++ headings markup
    text = re.sub(r"^\++\s*", "", text, flags=re.MULTILINE)
    # Remove ---- horizontal rules
    text = re.sub(r"^-{4,}$", "", text, flags=re.MULTILINE)
    # Remove ** bold ** and // italic //
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"//(.*?)//", r"\1", text)
    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def chunk_text(text: str, encoding) -> list[str]:
    """Split text into overlapping token-based chunks."""
    tokens = encoding.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + CHUNK_SIZE
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text.strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return [c for c in chunks if len(c) > MIN_CHUNK_LENGTH]  # Skip tiny chunks


def process_document(doc: dict, encoding) -> list[dict]:
    """Process a single SCP document into embedding-ready chunks."""
    chunks = []
    item_number = doc["item_number"]
    object_class = doc["object_class"]
    tags = doc.get("tags", [])
    url = doc["url"]

    sections = doc.get("sections", {})

    for section_type, section_text in sections.items():
        if not section_text or len(section_text.strip()) < 50:
            continue

        cleaned = clean_wikidot_markup(section_text)
        text_chunks = chunk_text(cleaned, encoding)

        for i, chunk in enumerate(text_chunks):
            chunks.append({
                "item_number": item_number,
                "object_class": object_class,
                "section_type": section_type,
                "tags": tags,
                "text": chunk,
                "url": url,
                "chunk_index": i,
            })

    # If no sections extracted, chunk the raw text
    if not chunks and doc.get("raw_text"):
        cleaned = clean_wikidot_markup(doc["raw_text"])
        text_chunks = chunk_text(cleaned, encoding)
        for i, chunk in enumerate(text_chunks):
            chunks.append({
                "item_number": item_number,
                "object_class": object_class,
                "section_type": "full",
                "tags": tags,
                "text": chunk,
                "url": url,
                "chunk_index": i,
            })

    return chunks


def main():
    """Main preprocessing pipeline."""
    input_file = DATA_DIR / "scp_raw_documents.json"
    output_file = DATA_DIR / "scp_chunks.json"

    if not input_file.exists():
        print("❌ Run scrape_scp.py first!")
        return

    with open(input_file, encoding="utf-8") as f:
        documents = json.load(f)

    encoding = tiktoken.get_encoding(ENCODING_NAME)
    all_chunks = []

    for doc in documents:
        chunks = process_document(doc, encoding)
        all_chunks.extend(chunks)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ Preprocessed {len(documents)} documents → {len(all_chunks)} chunks")
    print(f"   Output: {output_file}")

    # Stats
    sections = {}
    for c in all_chunks:
        s = c["section_type"]
        sections[s] = sections.get(s, 0) + 1
    print(f"   Sections: {sections}")


if __name__ == "__main__":
    main()
