# =============================================
# SCP World Backend — Dockerfile
# CPU-based embedding (sentence-transformers BAAI/bge-m3)
# =============================================
FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml .

# Install dependencies (no dev deps in production)
# PyTorch CPU-only build to keep image size manageable
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    uv sync --no-dev --no-install-project

# Application code
COPY app/ app/

# Expose port
EXPOSE 8080

# Run with uvicorn
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
