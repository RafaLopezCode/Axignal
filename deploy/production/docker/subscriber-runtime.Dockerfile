# Locked subscriber authentication and optional AXENT SDK. Providers stay lazy;
# without the explicit flag, key file and known rates there are zero model calls.
FROM ghcr.io/astral-sh/uv:0.12.15 AS uv

FROM python:3.12-slim

ARG AXIGNAL_CODE_SHA
LABEL org.opencontainers.image.title="AXIGNAL Subscriber Runtime" \
      org.opencontainers.image.source="https://github.com/RafaLopezCode/Axignal" \
      org.opencontainers.image.revision="$AXIGNAL_CODE_SHA"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --no-install-project --no-default-groups --group subscriber-auth --group research-canary-live

COPY application /app/application
COPY domain /app/domain
COPY pipeline /app/pipeline
COPY cognition /app/cognition
COPY tools /app/tools
COPY apps/web /app/apps/web

USER 33:33

ENTRYPOINT ["/app/.venv/bin/python", "-m", "tools.runtime"]
