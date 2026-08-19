FROM ghcr.io/astral-sh/uv:0.11.15 AS uv

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen

COPY backend ./backend
COPY docker/backend/entrypoint.sh /entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/backend
EXPOSE 8000

ENTRYPOINT ["sh", "/entrypoint.sh"]
