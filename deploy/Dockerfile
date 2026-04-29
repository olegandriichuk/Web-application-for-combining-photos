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

# ── Stage 3: base image (CUDA + Python + all deps) ──────────────────────────
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev \
    libopenjp2-tools git curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

# Install backend Python dependencies
COPY --from=git /tmp/app/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install Exposea Python dependencies
COPY --from=git /tmp/exposea/requirements.txt /tmp/exposea-requirements.txt
RUN pip install --no-cache-dir -r /tmp/exposea-requirements.txt

# Copy app source, Exposea, and built frontend
COPY --from=git /tmp/app/backend /app
COPY --from=git /tmp/exposea /app/exposea
COPY --from=frontend-build /app/dist /app/static

ENV EXPOSEA_PATH=/app/exposea
WORKDIR /app

# ── Stage 4: app (API + Vue SPA static file server) ─────────────────────────
FROM base AS app
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 80"]

# ── Stage 5: worker (GPU stitch job processor) ──────────────────────────────
FROM base AS worker
CMD ["python", "-m", "app.worker"]
