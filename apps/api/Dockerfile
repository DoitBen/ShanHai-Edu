FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt /app/apps/api/requirements.txt

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r /app/apps/api/requirements.txt

COPY apps/api/app /app/apps/api/app
COPY apps/api/README.md /app/apps/api/README.md
COPY workflow /app/workflow
COPY fixtures/textbook-parsing /app/fixtures/textbook-parsing
COPY docs/api-research/octo-video/capabilities.json /app/docs/api-research/octo-video/capabilities.json

ENV STORAGE_ROOT=/app/storage \
    WORKFLOW_ROOT=/app/workflow \
    CAPABILITIES_PATH=/app/docs/api-research/octo-video/capabilities.json

RUN mkdir -p /app/storage

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" || exit 1

CMD ["python", "-m", "uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
