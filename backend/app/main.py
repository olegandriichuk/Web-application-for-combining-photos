from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routers import photos, auth, projects, stitch_jobs
from .models import photo as _photo
from .models import user as _user
from .models import project as _project
from .models import stitch_job as _stitch_job

app = FastAPI(
    title="API (async, SQLite)",
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

@app.on_event("startup")
async def on_startup():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(photos.router, tags=["photos"])
app.include_router(stitch_jobs.router, tags=["stitch-jobs"])

@app.get("/health")
async def health():
    return {"ok": True}
