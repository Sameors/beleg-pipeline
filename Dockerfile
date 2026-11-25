FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1

# Dependencies first for better layer caching
COPY pyproject.toml uv.lock* README.md ./
RUN uv sync --no-install-project --no-dev

COPY src ./src
COPY migrations ./migrations
RUN uv sync --no-dev

# Run as non-root; data lives in a mounted volume, never in the image
RUN useradd --create-home appuser && mkdir -p /app/data && chown appuser /app/data
USER appuser
VOLUME ["/app/data"]

ENTRYPOINT ["uv", "run", "--no-sync", "ingest"]
CMD ["watch"]
