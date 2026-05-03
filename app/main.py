"""
KidsTrade API - נקודת הכניסה הראשית.
אפליקציית מסחר קהילתי לבני נוער 13-18.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # יצירת טבלאות
    Base.metadata.create_all(bind=engine)
    # זריעת נתונים ראשוניים
    seed_safe_points()
    print(f"🚀 KidsTrade API פועל במצב {settings.ENVIRONMENT}")
    yield
    print("👋 השרת נכבה")


app = FastAPI(
    title="KidsTrade API",
    description="אפליקציית מסחר קהילתי לבני נוער 13-18 - MVP",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS - בפרודקשן צריך להגביל לדומיינים הספציפיים של האפליקציה
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
