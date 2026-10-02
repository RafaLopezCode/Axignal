FROM python:3.12-slim

ARG AXIGNAL_CODE_SHA
LABEL org.opencontainers.image.title="AXIGNAL Runtime" \
      org.opencontainers.image.source="https://github.com/RafaLopezCode/Axignal" \
      org.opencontainers.image.revision="$AXIGNAL_CODE_SHA"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY application /app/application
COPY domain /app/domain
COPY pipeline /app/pipeline
COPY cognition /app/cognition
COPY tools /app/tools
COPY apps/web /app/apps/web

USER 33:33

ENTRYPOINT ["python", "-m", "tools.runtime"]
