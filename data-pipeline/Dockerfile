# =============================================
# SCP World Data Pipeline — Dockerfile
# One-shot job: embed scp_chunks.json into Firestore Vector Search.
# =============================================
FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml .

# Install dependencies
RUN uv sync --no-dev --no-install-project

# Copy scripts and config
COPY scripts/ scripts/
COPY config/ config/
COPY data/ data/

# Default: embed pre-built chunks and upload to Firestore.
# To run the full pipeline (scrape -> preprocess -> upload), override CMD.
CMD ["uv", "run", "python", "scripts/upload_to_firestore.py"]
