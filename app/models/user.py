"""מודל משתמש - ילד או הורה"""
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))

    role: Mapped[str] = mapped_column(String(10))  # "child" | "parent"
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))

    # עבור ילדים
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    city: Mapped[str] = mapped_column(String(50), nullable=True)
    neighborhood: Mapped[str] = mapped_column(String(100), nullable=True)

    # סטטוס אישור
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_code: Mapped[str] = mapped_column(String(10), nullable=True)

    # איפוס סיסמה
    password_reset_token: Mapped[str] = mapped_column(String(100), nullable=True)
    password_reset_expires: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # יחסים (relationships)
    parent = relationship("User", remote_side=[id], foreign_keys=[parent_id])
    store = relationship("Store", back_populates="owner", uselist=False)
