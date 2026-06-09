"""Shared dependencies for FastAPI dependency injection."""

import logging

import httpx

from app.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


def get_storage_service() -> StorageService:
    """Singleton Storage Service."""
    return StorageService(settings.SQLITE_DB_PATH)


_llm_http_client: httpx.AsyncClient | None = None
_embedding_service: EmbeddingService | None = None


async def get_llm_http_client() -> httpx.AsyncClient:
    """HTTP client for Ollama LLM endpoint."""
    global _llm_http_client
    if _llm_http_client is None:
        _llm_http_client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=httpx.Timeout(300.0, connect=30.0),
        )
    return _llm_http_client


def get_embedding_service() -> EmbeddingService:
    """Singleton CPU-based EmbeddingService (sentence-transformers)."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
        _embedding_service.load()
    return _embedding_service


async def close_clients():
    """Close all HTTP clients on shutdown."""
    global _llm_http_client
    if _llm_http_client is not None:
        await _llm_http_client.aclose()
        _llm_http_client = None


async def close_clients():
    """Cleanup all clients on app shutdown."""
    global _llm_http_client
    if _llm_http_client:
        await _llm_http_client.aclose()
        _llm_http_client = None
