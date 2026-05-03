"""מודלים של מפגשים ונקודות מפגש בטוחות"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


MEETING_STATUSES = ["scheduled", "completed", "cancelled"]


class SafePoint(Base):
    """נקודת מפגש בטוחה - ספרייה, מרכז קהילה, בית ספר וכו'"""
    __tablename__ = "safe_points"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(30))  # library, community_center, school

    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    safe_point_id: Mapped[int] = mapped_column(ForeignKey("safe_points.id"))

    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")

    # דירוגים לאחר המפגש
    buyer_rating: Mapped[int] = mapped_column(Integer, nullable=True)
    seller_rating: Mapped[int] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
