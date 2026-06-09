import json
import sqlite3
import os
import uuid
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import torch

SCRIPT_DIR = Path(__file__).parent.parent
DATA_DIR = SCRIPT_DIR / "data"
DB_PATH = SCRIPT_DIR.parent / "backend" / "scp_database.db"

def main():
    input_file = DATA_DIR / "scp_chunks.json"
    if not input_file.exists():
        print("Run preprocess.py first!")
        return

    with open(input_file, encoding="utf-8") as f:
        chunks = json.load(f)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    print(f"Loading embedding model: {model_name} on {device.upper()}...")
    model = SentenceTransformer(model_name, device=device)

    # SQLite 연결
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ensure database table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scp_documents (
            id TEXT PRIMARY KEY,
            item_number TEXT,
            object_class TEXT,
            section_type TEXT,
            tags TEXT,
            text TEXT,
            url TEXT,
            embedding BLOB
        )
    """)
    conn.commit()
    
    print(f"Uploading {len(chunks)} chunks to SQLite database: {DB_PATH}")
    
    # 배치 인코딩 (128개씩 GPU 가속)
    BATCH_SIZE = 128
    texts = [chunk["text"] for chunk in chunks]
    all_embeddings = []
    
    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="Encoding batches"):
        batch_texts = texts[i:i + BATCH_SIZE]
        batch_embeddings = model.encode(
            batch_texts,
            normalize_embeddings=True,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
        )
        all_embeddings.extend(batch_embeddings)
    
    print(f"Inserting {len(chunks)} rows into SQLite...")
    for chunk, embedding in tqdm(zip(chunks, all_embeddings), total=len(chunks), desc="Ingesting"):
        # float32 리스트를 raw bytes로 변환
        embedding_blob = np.array(embedding, dtype=np.float32).tobytes()
        
        doc_id = uuid.uuid4().hex
        cursor.execute(
            """INSERT OR REPLACE INTO scp_documents (id, item_number, object_class, section_type, tags, text, url, embedding) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc_id,
                chunk["item_number"],
                chunk["object_class"],
                chunk["section_type"],
                json.dumps(chunk.get("tags", []), ensure_ascii=False),
                chunk["text"],
                chunk["url"],
                embedding_blob
            )
        )
    conn.commit()
    conn.close()
    print("✅ Local SQLite database population complete!")

if __name__ == "__main__":
    main()
