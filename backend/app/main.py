"""SCP World — FastAPI Application Entrypoint."""

import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.dependencies import close_clients, get_embedding_service
from app.routers import auth, chat, health, personas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def _preload_embedding() -> None:
    """Load BGE-M3 in a worker thread so the first chat request doesn't pay
    the cost. Runs in the background — startup must NOT block on it, or
    Cloud Run's startup probe times out before the container is reachable."""
    try:
        await asyncio.to_thread(get_embedding_service)
        logger.info("✅ Embedding model ready.")
    except Exception as e:  # pragma: no cover - logged for observability
        logger.exception("Failed to preload embedding model: %s", e)


async def _warmup_llm() -> None:
    """Ollama 모델을 VRAM에 미리 로드.

    keep_alive=300 으로 5분 idle 후 언로드됩니다.
    """
    try:
        async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL,
                                     timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            await client.post(
                "/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL_NAME,
                    "messages": [{"role": "user", "content": "ping"}],
                    "stream": False,
                    "options": {"num_predict": 1},
                    "keep_alive": 300,  # 5분 idle 후 언로드 (VRAM 효율화)
                },
            )
        logger.info("✅ LLM model warm-up complete (keep_alive=300).")
    except Exception as e:
        logger.warning("LLM warm-up skipped (Ollama not ready?): %s", e)


from app.core.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("🚀 SCP World Backend starting up...")
    init_db()  # SQLite 초기화 실행
    logger.info("📐 Scheduling embedding model preload in background...")
    asyncio.create_task(_preload_embedding())
    logger.info("🔥 Scheduling LLM warm-up in background...")
    asyncio.create_task(_warmup_llm())
    yield
    logger.info("🛑 Shutting down — closing clients...")
    await close_clients()
    logger.info("✅ Shutdown complete.")


app = FastAPI(
    title="SCP World API",
    description=(
        "SCP Foundation AI Persona Chatbot — "
        "RAG-based knowledge retrieval with SSE streaming responses. "
        "Content based on the SCP Foundation Wiki (CC-BY-SA 3.0)."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — Flutter web + local dev (localhost / 127.0.0.1 / 0.0.0.0)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(personas.router)


@app.get("/")
async def root():
    """Root endpoint — API info."""
    return {
        "name": "SCP World API",
        "version": "0.1.0",
        "docs": "/docs",
        "license": "CC-BY-SA 3.0 (Source: SCP Foundation)",
    }
