# Deploy

Multi-stage Docker setup: FastAPI serves both the REST API and the Vue SPA on port 80. The GPU worker runs in a separate container with its own CUDA base image.

## Requirements

- NVIDIA GPU with CUDA support, ≥8 GB VRAM (required for the worker container)
- Docker + Docker Compose
- For worker container: NVIDIA Container Toolkit
- For local development: Python 3.10+, Node.js 18+

## Project Structure

```
backend/
  app/
    main.py        – FastAPI application factory and static file serving
    worker.py      – Redis Streams consumer, runs Exposea via subprocess
    config.py      – Pydantic settings loaded from environment variables
    database.py    – Async SQLAlchemy engine and session factory
    models/        – ORM models: User, Project, Photo, StitchJob, ProjectMember
    schemas/       – Pydantic request/response schemas
    routers/       – API route handlers
    repositories/  – Database query logic
    services/      – Business logic (S3, Redis, tiling, deletion)
    dependencies/  – JWT auth, role-based access guards
    utils/         – Shared utilities (JWT helpers)
  alembic/         – Database migrations
  alembic.ini
  requirements.txt

frontend/
  src/
    main.ts        – Vue application entry point
    App.vue        – Root component
    router/        – Vue Router with navigation guards
    stores/        – Pinia stores (auth state)
    api/           – Axios client and API call definitions
    types/         – TypeScript type definitions
    pages/         – Page components (Login, Register, Projects, Workspace, History, Account)
    layouts/       – Layout wrappers (DefaultLayout)
    components/    – Reusable UI components
      ui/          – shadcn-vue primitives (Button, Input, Label, Card)
    lib/           – Shared utilities (cn helper, toast)
    assets/        – Static assets
  package.json
  vite.config.ts

deploy/
  Dockerfile          – Multi-stage build for the app container
  docker-compose.yml  – Multi-container setup (app + worker)
  .env.example        – Environment variable template
  update.sh           – Helper script for build/start/stop commands
```

## Environment Variables

Copy the template and fill in your values:

```bash
cd deploy && cp .env.example .env
```

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing secret (generate with: `openssl rand -hex 32`) |
| `DATABASE_URL` | PostgreSQL connection string (e.g. Neon, Supabase) |
| `REDIS_URL` | Redis connection string (e.g. Upstash) |
| `AWS_ACCESS_KEY_ID` | AWS credentials for S3 |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials for S3 |
| `AWS_REGION` | S3 bucket region |
| `S3_BUCKET_NAME` | S3 bucket for photos, tiles, and results |
| `EXPOSEA_PATH` | Absolute path to the cloned [Exposea](https://github.com/DCGM/Exposea) repo on the worker machine. Exposea is an external CLI tool — clone it separately before starting the worker. |

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../deploy/.env.example .env  # fill in values
alembic upgrade head
uvicorn app.main:app --reload
# API available at http://localhost:8000
```

### Worker (requires GPU + Exposea)

The worker depends on [Exposea](https://github.com/DCGM/Exposea) — an external image stitching CLI that is NOT part of this codebase. This applies both to local development and to the Docker-based deployment (the Docker setup clones Exposea automatically inside the container via `EXPOSEA_PATH`). For local development without Docker, clone and set it up manually:

```bash
git clone https://github.com/DCGM/Exposea.git
cd Exposea
pip install -r requirements.txt
```

Then set `EXPOSEA_PATH` in your `.env` to the absolute path of the cloned repo:

```
EXPOSEA_PATH=/home/user/Exposea
```

Then start the worker:

```bash
python -m app.worker
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

---

> **Note:** The `worker` container requires an NVIDIA GPU with CUDA support to run
> the Exposea image stitching CLI. The `app` container (FastAPI + Vue SPA) runs on
> CPU only and can be deployed on any machine. If running in an environment without
> a GPU (e.g. FIT VUT CVT labs), the worker cannot be started — a live demo or
> recorded video should be used to demonstrate stitching functionality instead.

## Server Setup Checklist

Everything required on a GPU server before the first build.

### 1. Docker

```bash
docker --version
docker compose version
```

If not installed:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### 2. NVIDIA Driver

Required only for the `worker` container. The `app` container does not use the GPU.

```bash
nvidia-smi
```

Should print GPU name, driver version, and CUDA version. If the command is not found, install the NVIDIA driver for your OS.

### 3. NVIDIA Container Toolkit

The bridge between Docker and the GPU driver. Without it the container cannot see the GPU even if the driver is installed. Required only on the machine that runs the `worker` container.

Check your OS before choosing the installation path:

```bash
cat /etc/os-release
```

**Ubuntu/Debian (apt)**

```bash
# Add NVIDIA GPG key
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# Add repository
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit

# Restart Docker to pick up the toolkit
sudo systemctl restart docker
```

**RHEL/CentOS/Oracle Linux (dnf)**

```bash
# Add repository
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo \
  | sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

# Install
sudo dnf install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker
```

Verify:

```bash
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

If `nvidia-smi` runs successfully inside the container, the setup is complete.

### 4. WSL2 memory (local Windows machine only)

ML models require ~10 GB RAM. WSL2 defaults to 2 GB — increase it before running the worker:

```powershell
# Run in PowerShell on the Windows host
Set-Content -Path "$env:USERPROFILE\.wslconfig" -Value "[wsl2]`nmemory=12GB`nswap=4GB"
wsl --shutdown
```

Verify in the WSL terminal:

```bash
free -h
# Mem: should show ~12Gi
```

### 5. Pre-build checks

```bash
# Docker is running
docker ps

# GPU is accessible from Docker
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi

# Enough disk space (images take ~15–20 GB)
df -h
```

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

worker container (python:3.11-slim, GPU via pip CUDA wheels)
  └── python -m app.worker → Exposea CLI via subprocess

External:
  ├── PostgreSQL (Neon / Supabase — DATABASE_URL)
  ├── Redis     (Upstash        — REDIS_URL)
  └── S3        (AWS            — AWS_* + S3_BUCKET_NAME)
```
