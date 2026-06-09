import sqlite3
from app.config import settings

def init_db():
    """SQLite 데이터베이스 파일을 열어 스키마 테이블을 생성합니다."""
    conn = sqlite3.connect(settings.SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # scp_documents 테이블 생성
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
    
    # chat_sessions 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_key TEXT PRIMARY KEY,
            user_id TEXT,
            persona_id TEXT,
            session_id TEXT,
            messages TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # users 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    _create_indexes()


def _create_indexes():
    """성능 최적화를 위한 인덱스 및 FTS5 생성."""
    conn = sqlite3.connect(settings.SQLITE_DB_PATH)
    cursor = conn.cursor()

    # 메타데이터 필터링 가속
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_scp_item_number
        ON scp_documents(item_number)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_scp_object_class
        ON scp_documents(object_class)
    """)

    # FTS5 전문 검색 (텍스트 사전 필터링)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS scp_documents_fts
        USING fts5(text, content='scp_documents', content_rowid='rowid')
    """)

    conn.commit()
    conn.close()
