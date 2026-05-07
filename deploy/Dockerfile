# ── Stage 1: clone repos ────────────────────────────────────────────────────
FROM alpine AS git
RUN apk add --no-cache git

ARG REPO=https://github.com/olegandriichuk/Web-application-for-combining-photos.git
ARG BRANCH=docker
RUN git clone --branch "${BRANCH}" --depth 1 "${REPO}" /tmp/app
RUN git clone --depth 1 https://github.com/DCGM/Exposea.git /tmp/exposea

# ── Stage 2: build Vue frontend ─────────────────────────────────────────────
FROM node:22-alpine AS frontend-build
COPY --from=git /tmp/app/frontend /app
WORKDIR /app
RUN npm ci && npm run build

# ── Stage 3: app base (lightweight — no CUDA, no ML deps) ───────────────────
FROM python:3.10-slim AS app-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=git /tmp/app/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --from=git /tmp/app/backend /app
COPY --from=frontend-build /app/dist /app/static
WORKDIR /app

# ── Stage 4: app (API + Vue SPA static file server) ─────────────────────────
FROM app-base AS app
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 80"]

# ── Stage 5: worker base (CUDA + Python + all deps) ─────────────────────────
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 AS worker-base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev \
    libopenjp2-tools git curl \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

COPY --from=git /tmp/app/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# LightGlue v0.2 has a pyproject.toml metadata bug (name="unknown") — install separately
COPY --from=git /tmp/exposea/requirements.txt /tmp/exposea-requirements.txt
RUN grep -v 'lightglue' /tmp/exposea-requirements.txt > /tmp/exposea-req-filtered.txt && \
    pip install --no-cache-dir -r /tmp/exposea-req-filtered.txt && \
    git clone --branch v0.2 --depth 1 https://github.com/cvg/LightGlue.git /tmp/lightglue && \
    cp -r /tmp/lightglue/lightglue /usr/local/lib/python3.10/dist-packages/lightglue

COPY --from=git /tmp/app/backend /app
COPY --from=git /tmp/exposea /app/exposea

ENV EXPOSEA_PATH=/app/exposea
WORKDIR /app

# ── Stage 6: worker (GPU stitch job processor) ──────────────────────────────
FROM worker-base AS worker
CMD ["python", "-m", "app.worker"]