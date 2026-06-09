"""Embedding service — CPU-based sentence-transformers (BAAI/bge-m3).

Runs in-process within the backend container. Produces 1024-dim vectors
compatible with the data-pipeline ingestion that populates SQLite.
"""

import asyncio
import logging
import torch

from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding using sentence-transformers (BGE-M3) with GPU support."""

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or settings.EMBED_MODEL_NAME
        self._model: SentenceTransformer | None = None

    def load(self) -> None:
        """Load the model into memory. Call once at application startup."""
        if self._model is None:
            device = "cpu"
            logger.info("📐 Loading embedding model: %s (%s)...", self._model_name, device.upper())
            self._model = SentenceTransformer(self._model_name, device=device)
            logger.info("✅ Embedding model loaded.")

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self.load()
        return self._model  # type: ignore[return-value]

    async def encode(self, text: str) -> list[float]:
        """Embed a single text string and return the dense vector."""
        model = self._get_model()
        # Run CPU-bound encoding in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: model.encode(text, normalize_embeddings=True).tolist(),
        )
        return embedding

    async def health_check(self) -> bool:
        """Check if the embedding model is loaded and ready."""
        try:
            self._get_model()
            return True
        except Exception:
            return False
