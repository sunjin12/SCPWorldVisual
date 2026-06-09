"""Tests for MemoryService — SQLite-backed sliding-window conversation history."""

import pytest
from unittest.mock import AsyncMock

from app.models.session import Message
from app.services.memory_service import MemoryService


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.get_history = AsyncMock(return_value=[])
    storage.save_history = AsyncMock()
    storage.clear_session = AsyncMock()
    return storage


@pytest.fixture
def memory_service(mock_storage):
    return MemoryService(mock_storage, max_turns=3)


class TestGetHistory:
    @pytest.mark.asyncio
    async def test_empty_history(self, memory_service, mock_storage):
        mock_storage.get_history.return_value = []
        history = await memory_service.get_history("user1", "researcher", "sess1")
        assert history == []

    @pytest.mark.asyncio
    async def test_returns_messages(self, memory_service, mock_storage):
        mock_storage.get_history.return_value = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there"),
        ]
        history = await memory_service.get_history("user1", "researcher", "sess1")
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].content == "Hi there"

    @pytest.mark.asyncio
    async def test_persona_forwarded(self, memory_service, mock_storage):
        await memory_service.get_history("user1", "agent", "sess1")
        mock_storage.get_history.assert_awaited_with("user1", "agent", "sess1")


class TestSlidingWindow:
    @pytest.mark.asyncio
    async def test_trims_to_max_turns(self, memory_service, mock_storage):
        existing = [
            Message(role="user" if i % 2 == 0 else "assistant", content=f"m{i}")
            for i in range(6)
        ]
        mock_storage.get_history.return_value = existing

        await memory_service.add_turn(
            "user1", "researcher", "sess1", "new_q", "new_a"
        )

        saved = mock_storage.save_history.call_args.args[3]
        # 6 existing + 2 new = 8, trimmed to max_turns*2 = 6
        assert len(saved) == 6
        assert saved[-2].content == "new_q"
        assert saved[-1].content == "new_a"


class TestClearSession:
    @pytest.mark.asyncio
    async def test_delegates_to_storage(self, memory_service, mock_storage):
        await memory_service.clear_session("user1", "researcher", "sess1")
        mock_storage.clear_session.assert_awaited_once_with(
            "user1", "researcher", "sess1"
        )
