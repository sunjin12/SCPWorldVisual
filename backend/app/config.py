"""Pydantic Settings for SCP World Backend."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings

# Minimal .env loader — populates os.environ so vars consumed directly by
# third-party libs are visible at the process level, not just on the
# Settings instance.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


class Settings(BaseSettings):
    """Application settings, loaded from environment variables or .env file."""

    # --- Local SQLite DB ---
    SQLITE_DB_PATH: str = "scp_database.db"

    # --- Ollama: Local LLM API ---
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_NAME: str = "qwen2.5:7b"

    # --- Embedding: sentence-transformers (all-MiniLM-L6-v2, 384-dim) ---
    EMBED_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Session ---
    MAX_CONVERSATION_TURNS: int = 6

    # Ignore env vars consumed directly by external libs so they can live
    # in `.env` for local dev without tripping pydantic's `extra='forbid'`.
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
