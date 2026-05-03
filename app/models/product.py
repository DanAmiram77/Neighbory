"""מודל מוצר"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# קטגוריות מותרות (אכיפה ברמת האפליקציה)
ALLOWED_CATEGORIES = [
    "toys",          # צעצועים
    "books",         # ספרים
    "games",         # משחקי לוח ווידאו
    "clothes",       # בגדים
    "sports",        # ציוד ספורט
    "collectibles",  # אספנות (כרטיסים, מדבקות)
    "electronics",   # אלקטרוניקה פשוטה
    "handmade",      # יצירת יד
    "other",         # אחר
]

ALLOWED_CONDITIONS = ["new", "like_new", "used"]
PRODUCT_STATUSES = ["pending_parent", "active", "sold", "removed"]


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))

    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(1000))
    images: Mapped[list] = mapped_column(JSON, default=list)  # רשימת URLs
    category: Mapped[str] = mapped_column(String(30))
    condition: Mapped[str] = mapped_column(String(20))

    price: Mapped[float] = mapped_column(Float)

    # סטטוס אישור ע״י הורה
    status: Mapped[str] = mapped_column(String(20), default="pending_parent")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    store = relationship("Store", back_populates="products")
