"""חיבור למסד הנתונים - תומך גם ב-SQLite (פיתוח) וגם ב-PostgreSQL (פרודקשן)"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


db_url = settings.get_database_url()

# SQLite דורש הגדרה מיוחדת, PostgreSQL לא
if "sqlite" in db_url:
    connect_args = {"check_same_thread": False}
else:
    connect_args = {"connect_timeout": 10}  # don't hang >10s waiting for sleeping DB

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300,  # recycle connections every 5 min to avoid stale sockets
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
