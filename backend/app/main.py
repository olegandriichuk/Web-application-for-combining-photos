# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import items  # лишаємо ту саму назву файлу routers/items.py

app = FastAPI(title="API (async, SQLite)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    # створимо таблиці асинхронно
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# підключаємо рівно ті ж маршрути
app.include_router(items.router)

@app.get("/health")
async def health():
    return {"ok": True}
