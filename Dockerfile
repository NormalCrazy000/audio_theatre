# Copione Audio: frontend Svelte + backend FastAPI in un'unica immagine.
#
#   docker build -t copione-audio .
#   docker run -p 8000:8000 -v copione-audio-cache:/data/cache \
#       -v copione-audio-voci:/data/voci copione-audio
#
# Poi apri http://localhost:8000. Il TTS online (edge-tts) richiede internet;
# per quello offline (Piper) si scaricano una volta le voci nel volume:
#
#   docker run --rm -v copione-audio-voci:/data/voci copione-audio \
#       python -m copione_audio.tts.piper

# --- 1. Build del frontend -------------------------------------------------
FROM node:24-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- 2. Ambiente Python (dipendenze dal lock, senza quelle di sviluppo) -----
FROM python:3.14-slim AS backend
COPY --from=ghcr.io/astral-sh/uv:0.9.3 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Prima le sole dipendenze: questo strato resta in cache finché non cambia il lock.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/src ./src
RUN uv sync --frozen --no-dev --no-editable

# --- 3. Immagine finale ----------------------------------------------------
FROM python:3.14-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 app \
    && mkdir -p /data/cache /data/voci \
    && chown app /data/cache /data/voci

COPY --from=backend /app/.venv /app/.venv
COPY --from=frontend /frontend/dist /app/frontend

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    COPIONE_AUDIO_FRONTEND=/app/frontend \
    COPIONE_AUDIO_CACHE=/data/cache \
    COPIONE_AUDIO_PIPER=/data/voci

USER app
WORKDIR /home/app
# Cache delle battute sintetizzate e voci Piper: con i volumi sopravvivono ai riavvii.
VOLUME /data/cache /data/voci
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json')"

CMD ["uvicorn", "copione_audio.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
