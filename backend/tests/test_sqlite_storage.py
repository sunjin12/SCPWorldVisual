import pytest
import os
import sqlite3
from app.services.storage_service import StorageService
from app.models.session import Message

@pytest.mark.asyncio
async def test_sqlite_session_history():
    test_db = "test_database.db"
    if os.path.exists(test_db):
        os.remove(test_db)
        
    # 직접 테이블 초기화
    conn = sqlite3.connect(test_db)
    conn.execute("""
        CREATE TABLE chat_sessions (
            session_key TEXT PRIMARY KEY,
            user_id TEXT,
            persona_id TEXT,
            session_id TEXT,
            messages TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    
    storage = StorageService(test_db)
    
    user_id = "test_user"
    persona_id = "researcher"
    session_id = "session_123"
    messages = [
        Message(role="user", content="안녕하세요"),
        Message(role="assistant", content="반갑습니다, 요원님.")
    ]
    
    await storage.save_history(user_id, persona_id, session_id, messages)
    history = await storage.get_history(user_id, persona_id, session_id)
    
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[0].content == "안녕하세요"
    
    # 세션 정리
    await storage.clear_session(user_id, persona_id, session_id)
    history_after_clear = await storage.get_history(user_id, persona_id, session_id)
    assert len(history_after_clear) == 0
    
    if os.path.exists(test_db):
        os.remove(test_db)
