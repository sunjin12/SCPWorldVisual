from app.models.session import Message
from app.services.storage_service import StorageService


class MemoryService:
    """Manages per-user, per-persona, per-session conversation history."""

    def __init__(
        self,
        storage_service: StorageService,
        max_turns: int = 6,
    ):
        self.storage = storage_service
        self.max_turns = max_turns

    async def get_history(
        self, user_id: str, persona_id: str, session_id: str
    ) -> list[Message]:
        """Retrieve the most recent conversation turns for a session from SQLite."""
        history = await self.storage.get_history(user_id, persona_id, session_id)
        # Sliding window: keep last max_turns * 2 messages (user + assistant pairs)
        return history[-self.max_turns * 2 :]

    async def add_turn(
        self,
        user_id: str,
        persona_id: str,
        session_id: str,
        user_msg: str,
        assistant_msg: str,
    ):
        """Append a conversation turn (user + assistant) to SQLite."""
        history = await self.get_history(user_id, persona_id, session_id)
        history.append(Message(role="user", content=user_msg))
        history.append(Message(role="assistant", content=assistant_msg))

        # Sliding window trim
        trimmed = history[-self.max_turns * 2 :]

        await self.storage.save_history(user_id, persona_id, session_id, trimmed)

    async def clear_session(
        self, user_id: str, persona_id: str, session_id: str
    ):
        """Delete a specific session's history."""
        await self.storage.clear_session(user_id, persona_id, session_id)
