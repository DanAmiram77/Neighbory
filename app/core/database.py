"""חיבור למסד הנתונים - תומך גם ב-SQLite (פיתוח) וגם ב-PostgreSQL (פרודקשן)"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


db_url = settings.get_database_url()

# SQLite דורש הגדרה מיוחדת, PostgreSQL לא
connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,  # בודק חיבורים מתים לפני שימוש - חשוב לפרודקשן
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
