"""LLM service — Ollama native API with streaming support."""

import json
import logging
from collections.abc import AsyncGenerator

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Calls Ollama's native /api/chat endpoint (streaming + non-streaming)."""

    def __init__(self, http_client: httpx.AsyncClient):
        self.client = http_client
        self.model = settings.OLLAMA_MODEL_NAME

    async def generate_stream(
        self,
        messages: list[dict],
        *,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama one at a time via native /api/chat."""
        options: dict = {
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens,
        }
        if frequency_penalty:
            options["frequency_penalty"] = frequency_penalty
        if presence_penalty:
            options["presence_penalty"] = presence_penalty

        # qwen3 계열은 enable_thinking=False가 필요 (qwen2.5는 미해당)
        if "qwen3" in self.model:
            options["enable_thinking"] = False

        async with self.client.stream(
            "POST",
            "/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": options,
            },
        ) as response:
            response.raise_for_status()
            logger.info("📡 Ollama streaming connection established.")
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    if chunk.get("done"):
                        logger.info("🏁 Ollama streaming complete (done=true)")
                        break
                    msg = chunk.get("message", {})
                    if "content" in msg:
                        token = msg["content"]
                        if token:
                            yield token
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning("Failed to decode chunk: %s (data: %s)", e, line[:100])
                    continue

    async def generate(
        self,
        messages: list[dict],
        *,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
    ) -> str:
        """Non-streaming generation (fallback)."""
        options: dict = {
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens,
        }
        if frequency_penalty:
            options["frequency_penalty"] = frequency_penalty
        if presence_penalty:
            options["presence_penalty"] = presence_penalty

        # qwen3 계열은 enable_thinking=False가 필요
        if "qwen3" in self.model:
            options["enable_thinking"] = False

        response = await self.client.post(
            "/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": options,
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data.get("message", {}).get("content", "")
        # qwen3.5 안전망: content가 비었으면 thinking 필드에서 추출
        if not content:
            thinking = data.get("message", {}).get("thinking", "")
            if thinking:
                logger.warning("content empty, falling back to thinking field (%d chars)", len(thinking))
                content = thinking
        return content

    async def health_check(self) -> bool:
        """Check if the LLM endpoint is reachable via Ollama native API."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
