from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import photos, auth, projects, stitch_jobs, project_members
from .models import photo as _photo
from .models import user as _user
from .models import project as _project
from .models import stitch_job as _stitch_job
from .models import project_member as _project_member

app = FastAPI(
    title="API (async, PostgreSQL)",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(project_members.router, prefix="/api/projects", tags=["project-members"])
app.include_router(photos.router, prefix="/api", tags=["photos"])
app.include_router(stitch_jobs.router, prefix="/api", tags=["stitch-jobs"])

@app.get("/health")
async def health():
    return {"ok": True}

# Serve Vue SPA from /app/static when running in Docker (not present in dev)
_static = Path("/app/static")
if _static.is_dir():
    app.mount("/", StaticFiles(directory=str(_static), html=True), name="static")
