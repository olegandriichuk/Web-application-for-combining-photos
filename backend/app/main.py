import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routers import items, photos
from .models import photo as _photo  # важливо: реєструє модель Photo у Base.metadata
from .models import item as _item    # так само реєструємо Item

app = FastAPI(
    title="API (async, SQLite)",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS для фронтенду (Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    # створюємо всі таблиці (items, photos, …)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # гарантуємо існування директорії для зображень
    os.makedirs(os.path.join(os.getcwd(), "data", "photos"), exist_ok=True)

# маршрути
app.include_router(items.router)  # має власний prefix="/items" всередині
app.include_router(photos.router, prefix="/photos", tags=["photos"])

@app.get("/health")
async def health():
    return {"ok": True}
