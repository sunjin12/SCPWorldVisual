"""Tests for LLMService — SSE streaming parsing and token extraction.

These tests verify the *parsing logic* of generate_stream without a live
Ollama server, by injecting pre-built SSE lines via an async mock.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

from app.services.llm_service import LLMService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sse_line(token: str) -> str:
    """Build a valid SSE data line carrying a single chat token."""
    payload = {
        "choices": [
            {"delta": {"content": token}, "finish_reason": None}
        ]
    }
    return f"data: {json.dumps(payload)}"


def _sse_done() -> str:
    return "data: [DONE]"


def _sse_empty_delta() -> str:
    """Line with a delta that carries no 'content' key (role-only chunk)."""
    payload = {"choices": [{"delta": {"role": "assistant"}, "finish_reason": None}]}
    return f"data: {json.dumps(payload)}"


def _sse_finish() -> str:
    """Final chunk with finish_reason but empty content delta."""
    payload = {"choices": [{"delta": {}, "finish_reason": "stop"}]}
    return f"data: {json.dumps(payload)}"


async def _make_mock_stream(lines: list[str]):
    """AsyncGenerator that yields lines one-by-one, simulating aiter_lines()."""
    for line in lines:
        yield line


def _make_client(lines: list[str]) -> MagicMock:
    """
    Build a fake httpx.AsyncClient whose stream() context manager yields the
    given list of SSE lines from response.aiter_lines().
    """
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.aiter_lines = MagicMock(return_value=_make_mock_stream(lines))

    @asynccontextmanager
    async def _stream(*args, **kwargs):
        yield mock_response

    mock_client = MagicMock()
    mock_client.stream = _stream
    return mock_client


# ---------------------------------------------------------------------------
# Tests — generate_stream
# ---------------------------------------------------------------------------

class TestGenerateStream:
    """LLMService.generate_stream SSE parsing behaviour."""

    @pytest.mark.asyncio
    async def test_yields_tokens_in_order(self):
        """정상 SSE 스트림에서 토큰을 순서대로 yield해야 한다."""
        lines = [
            _sse_empty_delta(),   # role-only header chunk (no content)
            _sse_line("SCP"),
            _sse_line("-1"),
            _sse_line("73은"),
            _sse_finish(),
            _sse_done(),
        ]
        client = _make_client(lines)
        svc = LLMService(client)

        tokens = [t async for t in svc.generate_stream([{"role": "user", "content": "test"}])]
        assert tokens == ["SCP", "-1", "73은"]

    @pytest.mark.asyncio
    async def test_stops_at_done_sentinel(self):
        """[DONE] 수신 즉시 반복을 중단해야 한다."""
        lines = [
            _sse_line("first"),
            _sse_done(),
            _sse_line("never"),   # should NOT be yielded
        ]
        client = _make_client(lines)
        svc = LLMService(client)

        tokens = [t async for t in svc.generate_stream([{"role": "user", "content": "test"}])]
        assert tokens == ["first"]
        assert "never" not in tokens

    @pytest.mark.asyncio
    async def test_skips_non_data_lines(self):
        """'data: ' 접두사가 없는 라인(빈 줄, 이벤트 헤더 등)은 무시해야 한다."""
        lines = [
            "",                   # blank line (SSE separator)
            "event: message",     # event type header
            ": keep-alive",       # SSE comment
            _sse_line("hello"),
            _sse_done(),
        ]
        client = _make_client(lines)
        svc = LLMService(client)

        tokens = [t async for t in svc.generate_stream([{"role": "user", "content": "test"}])]
        assert tokens == ["hello"]

    @pytest.mark.asyncio
    async def test_skips_malformed_json_without_crashing(self):
        """JSON 파싱 실패 시 예외 없이 해당 청크를 건너뛰어야 한다."""
        lines = [
            "data: {broken json!!!}",
            _sse_line("good"),
            _sse_done(),
        ]
        client = _make_client(lines)
        svc = LLMService(client)

        tokens = [t async for t in svc.generate_stream([{"role": "user", "content": "test"}])]
        assert tokens == ["good"]

    @pytest.mark.asyncio
    async def test_skips_delta_without_content_key(self):
        """delta에 'content' 키가 없는 청크는 yield하지 않아야 한다."""
        lines = [
            _sse_empty_delta(),   # {"delta": {"role": "assistant"}}
            _sse_finish(),        # {"delta": {}}
            _sse_line("ok"),
            _sse_done(),
        ]
        client = _make_client(lines)
        svc = LLMService(client)

        tokens = [t async for t in svc.generate_stream([{"role": "user", "content": "test"}])]
        assert tokens == ["ok"]

    @pytest.mark.asyncio
    async def test_empty_stream_yields_nothing(self):
        """즉시 [DONE]이 오면 토큰을 하나도 yield하지 않아야 한다."""
        lines = [_sse_done()]
        client = _make_client(lines)
        svc = LLMService(client)

        tokens = [t async for t in svc.generate_stream([{"role": "user", "content": "test"}])]
        assert tokens == []

    @pytest.mark.asyncio
    async def test_whitespace_trimmed_before_json_parse(self):
        """'data: ' 이후 공백이 있어도 올바르게 파싱해야 한다."""
        payload = json.dumps({"choices": [{"delta": {"content": "trimmed"}, "finish_reason": None}]})
        lines = [
            f"data:   {payload}",  # extra spaces after "data:"
            _sse_done(),
        ]
        client = _make_client(lines)
        svc = LLMService(client)

        tokens = [t async for t in svc.generate_stream([{"role": "user", "content": "test"}])]
        assert tokens == ["trimmed"]


# ---------------------------------------------------------------------------
# Tests — generate (non-streaming)
# ---------------------------------------------------------------------------

class TestGenerate:
    """LLMService.generate (non-streaming) 응답 파싱."""

    @pytest.mark.asyncio
    async def test_returns_message_content(self):
        """정상 응답에서 choices[0].message.content를 반환해야 한다."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "SCP-173은 조각상입니다."}, "finish_reason": "stop"}
            ]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        svc = LLMService(mock_client)
        result = await svc.generate([{"role": "user", "content": "SCP-173이란?"}])
        assert result == "SCP-173은 조각상입니다."


# ---------------------------------------------------------------------------
# Tests — health_check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    """LLMService.health_check 동작."""

    @pytest.mark.asyncio
    async def test_returns_true_on_200(self):
        """HTTP 200 응답 시 True를 반환해야 한다."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        svc = LLMService(mock_client)
        assert await svc.health_check() is True

    @pytest.mark.asyncio
    async def test_returns_false_on_connection_error(self):
        """연결 실패 시 예외 없이 False를 반환해야 한다."""
        import httpx
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        svc = LLMService(mock_client)
        assert await svc.health_check() is False
