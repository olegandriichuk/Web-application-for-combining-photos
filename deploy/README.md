# Deploy

Multi-stage Docker setup: FastAPI serves both the REST API and the Vue SPA on port 80. The GPU worker runs in a separate container with its own CUDA base image.

## Prerequisites

- Docker + Docker Compose v2
- NVIDIA Container Toolkit (for the worker only)

## Setup

```bash
cd deploy
cp .env.example .env
# Edit .env — fill in DATABASE_URL, REDIS_URL, SECRET_KEY, AWS credentials
```

## Commands

```bash
# All services
./update.sh build          # build both app and worker images (no cache)
./update.sh up             # start all containers
./update.sh down           # stop all containers

# App only (lightweight — no CUDA, rebuilds in ~3 min)
./update.sh app-build      # build app image
./update.sh app-up         # start app container
./update.sh app-down       # stop app container

# Worker only (CUDA + ML deps, rebuilds in ~20 min)
./update.sh worker-build   # build worker image
./update.sh worker-up      # start worker (requires NVIDIA GPU)
./update.sh worker-down    # stop worker

# Monitoring
./update.sh logs           # follow logs for all containers
./update.sh ps             # show container status
```

## WSL2 memory (local GPU machine)

ML models require ~10 GB RAM. Increase the WSL2 memory limit before running the worker:

```powershell
# Run in PowerShell on the Windows host
Set-Content -Path "$env:USERPROFILE\.wslconfig" -Value "[wsl2]`nmemory=12GB`nswap=4GB"
wsl --shutdown
```

## Verification

### Local (WSL2 + Docker Desktop)
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) with WSL2 backend
2. Configure WSL2 memory (see above)
3. `./update.sh app-build && ./update.sh app-up`
4. `curl http://localhost/health` → `{"ok":true}`
5. Open `http://localhost` — Vue SPA loads, register/login works
6. Install [NVIDIA Container Toolkit for WSL2](https://docs.nvidia.com/cuda/wsl-user-guide/index.html) for the worker
7. `./update.sh worker-build && ./update.sh worker-up`

### GPU Server (production)
1. Install Docker + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. Clone the repo and `cd deploy`
3. `cp .env.example .env` and fill in values
4. `./update.sh app-build && ./update.sh app-up`
5. `curl http://localhost/health` → `{"ok":true}`
6. `./update.sh worker-build && ./update.sh worker-up`
7. Submit a stitch job from the UI; `./update.sh logs` to watch the worker process it

## Architecture

```
Browser → :80 → app container (FastAPI, python:3.10-slim)
  ├── /api/*    → FastAPI routers
  ├── /assets/* → Vue SPA static assets
  ├── /health   → health check
  └── /*        → Vue SPA index.html (SPA routing fallback)

worker container (nvidia/cuda:12.1.1, GPU)
  └── python -m app.worker → Exposea CLI via subprocess

External:
  ├── PostgreSQL (Neon / Supabase — DATABASE_URL)
  ├── Redis     (Upstash        — REDIS_URL)
  └── S3        (AWS            — AWS_* + S3_BUCKET_NAME)
```
