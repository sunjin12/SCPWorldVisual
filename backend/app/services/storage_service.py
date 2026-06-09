"""Storage service — SQLite-based RAG vector search and session storage."""

import sqlite3
import json
import numpy as np
from app.config import settings
from app.models.session import Message


class StorageService:
    """Unified storage service using local SQLite database."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # --- RAG: Vector Search ---

    async def vector_search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        item_number: str | None = None,
        object_class: str | None = None,
    ) -> list[dict]:
        """
        Perform vector similarity search using NumPy cosine similarity over SQLite documents.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT text, item_number, object_class, section_type, url, embedding FROM scp_documents"
        params = []
        
        conditions = []
        if item_number:
            conditions.append("item_number = ?")
            params.append(item_number)
        if object_class:
            conditions.append("object_class = ?")
            params.append(object_class)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        rows = cursor.execute(query, params).fetchall()
        conn.close()
        
        if not rows:
            return []
            
        # Filter out documents without embeddings
        valid_rows = [r for r in rows if r["embedding"] is not None]
        if not valid_rows:
            return []
            
        # Parse embeddings from BLOBs
        embeddings = [np.frombuffer(r["embedding"], dtype=np.float32) for r in valid_rows]
        embeddings_matrix = np.stack(embeddings)  # Shape: (N, 1024)
        
        q_vec = np.array(query_vector, dtype=np.float32)
        
        # Calculate cosine similarity (if normalized, dot product is equivalent)
        similarities = np.dot(embeddings_matrix, q_vec)
        
        # Sort and select top K
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            row = valid_rows[idx]
            results.append({
                "item_number": row["item_number"],
                "object_class": row["object_class"],
                "section_type": row["section_type"],
                "text": row["text"],
                "url": row["url"],
            })
            
        return results

    # --- Session: Conversation History ---

    def _session_path(
        self, user_id: str, persona_id: str, session_id: str
    ) -> str:
        """Isolated path key for session."""
        return f"{user_id}__{persona_id}__{session_id}"

    async def get_history(
        self, user_id: str, persona_id: str, session_id: str
    ) -> list[Message]:
        """Retrieve conversation history from SQLite chat_sessions table."""
        conn = self._get_connection()
        cursor = conn.cursor()
        session_key = self._session_path(user_id, persona_id, session_id)
        
        row = cursor.execute(
            "SELECT messages FROM chat_sessions WHERE session_key = ?", (session_key,)
        ).fetchone()
        conn.close()

        if not row:
            return []

        messages = json.loads(row["messages"])
        return [Message(**m) for m in messages]

    async def save_history(
        self,
        user_id: str,
        persona_id: str,
        session_id: str,
        messages: list[Message],
    ):
        """Persist conversation history in SQLite."""
        conn = self._get_connection()
        cursor = conn.cursor()
        session_key = self._session_path(user_id, persona_id, session_id)
        messages_json = json.dumps([m.model_dump() for m in messages], ensure_ascii=False)
        
        cursor.execute(
            """INSERT OR REPLACE INTO chat_sessions (session_key, user_id, persona_id, session_id, messages) 
               VALUES (?, ?, ?, ?, ?)""",
            (session_key, user_id, persona_id, session_id, messages_json)
        )
        conn.commit()
        conn.close()

    async def clear_session(
        self, user_id: str, persona_id: str, session_id: str
    ):
        """Delete session history from SQLite."""
        conn = self._get_connection()
        cursor = conn.cursor()
        session_key = self._session_path(user_id, persona_id, session_id)
        
        cursor.execute("DELETE FROM chat_sessions WHERE session_key = ?", (session_key,))
        conn.commit()
        conn.close()

    # --- Auth: User Caching ---

    async def save_user(self, user: dict):
        """Cache verified user profile info in SQLite."""
        user_id = user.get("user_id")
        if not user_id:
            return

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, name) VALUES (?, ?)",
            (user_id, user.get("name", ""))
        )
        conn.commit()
        conn.close()
