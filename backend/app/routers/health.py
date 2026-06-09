"""Health check router — checks all backend dependencies."""

import logging

from fastapi import APIRouter

import sqlite3
from app.config import settings

from app.dependencies import (
    get_embedding_service,
    get_llm_http_client,
    get_storage_service,
)
from app.models.schemas import HealthResponse
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint (unauthenticated).

    Checks connectivity to SQLite, vLLM LLM, and CPU Embedding.
    Used by Cloud Run startup probes and Flutter splash screen.
    """
    status = "healthy"
    checks = {}

    # SQLite database check
    try:
        conn = sqlite3.connect(settings.SQLITE_DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"
        status = "degraded"

    # Ollama LLM
    try:
        llm_client = await get_llm_http_client()
        llm_svc = LLMService(llm_client)
        if await llm_svc.health_check():
            checks["ollama_llm"] = "healthy"
        else:
            checks["ollama_llm"] = "unhealthy"
            status = "degraded"
    except Exception as e:
        checks["ollama_llm"] = f"unhealthy: {e}"
        status = "degraded"

    # CPU Embedding (sentence-transformers, in-process)
    try:
        embed_svc = get_embedding_service()
        if await embed_svc.health_check():
            checks["embedding"] = "healthy (CPU)"
        else:
            checks["embedding"] = "unhealthy"
            status = "degraded"
    except Exception as e:
        checks["embedding"] = f"unhealthy: {e}"
        status = "degraded"

    return HealthResponse(status=status, **checks)


@router.get("/ready")
async def ready():
    """Simple readiness probe for Cloud Run."""
    return {"status": "ready"}
