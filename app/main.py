"""
KidsTrade API - נקודת הכניסה הראשית.
אפליקציית מסחר קהילתי לבני נוער 13-18.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.database import Base, engine, SessionLocal
from app.core.config import settings
from app.models.meeting import SafePoint

# ייבוא כל המודלים כדי ש-SQLAlchemy יכיר אותם
from app.models import user, store, product, chat, meeting  # noqa: F401

from app.routers import auth, stores, products, chat as chat_router, meetings


def seed_safe_points():
    """יצירת נקודות מפגש בטוחות ראשוניות - פעם אחת בהפעלה ראשונה"""
    db = SessionLocal()
    try:
        if db.query(SafePoint).count() == 0:
            initial_points = [
                SafePoint(
                    name="ספריית בית אריאלה",
                    address="שאול המלך 25, תל אביב",
                    city="תל אביב",
                    type="library",
                    latitude=32.0853, longitude=34.7818,
                ),
                SafePoint(
                    name="מרכז קהילתי רמת אביב",
                    address="איינשטיין 40, תל אביב",
                    city="תל אביב",
                    type="community_center",
                    latitude=32.1131, longitude=34.8069,
                ),
                SafePoint(
                    name="ספריית העיר חיפה",
                    address="פבזנר 4, חיפה",
                    city="חיפה",
                    type="library",
                    latitude=32.8156, longitude=34.9885,
                ),
                SafePoint(
                    name="הספרייה העירונית ירושלים",
                    address="בצלאל 6, ירושלים",
                    city="ירושלים",
                    type="library",
                    latitude=31.7767, longitude=35.2169,
                ),
            ]
            db.add_all(initial_points)
            db.commit()
            print(f"✅ נוספו {len(initial_points)} נקודות מפגש בטוחות")
    finally:
        db.close()


def run_migrations():
    """Add any missing columns to existing tables (safe, idempotent)."""
    migrations = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_expires TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS neighborhood VARCHAR(100)",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            conn.execute(text(sql))
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        run_migrations()
        seed_safe_points()
    except Exception as e:
        print(f"⚠️ DB init error (will retry on first request): {e}")
    print(f"🚀 KidsTrade API פועל במצב {settings.ENVIRONMENT}")
    yield
    print("👋 השרת נכבה")


app = FastAPI(
    title="KidsTrade API",
    description="אפליקציית מסחר קהילתי לבני נוער 13-18 - MVP",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS - Bearer token auth doesn't need allow_credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Ensure CORS headers are present even on unhandled 500 errors.
    Without this, the CORSMiddleware is bypassed on crashes and the
    browser sees 'Failed to fetch' instead of a useful error message."""
    origin = request.headers.get("origin", "")
    headers = {"Access-Control-Allow-Origin": "*"} if origin else {}
    print(f"💥 Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "שגיאת שרת פנימית. אנא נסו שוב."},
        headers=headers,
    )

# רישום כל הנתיבים
app.include_router(auth.router)
app.include_router(stores.router)
app.include_router(products.router)
app.include_router(chat_router.router)
app.include_router(meetings.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "app": "KidsTrade API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
