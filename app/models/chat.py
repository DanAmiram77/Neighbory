"""מודלים של צ'אט - תבניות בלבד, ללא טקסט חופשי"""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# תבניות הודעה מותרות (אין טקסט חופשי ב-MVP)
MESSAGE_TEMPLATES = {
    "interested": "שלום, אני מעוניין/ת לקנות את המוצר",
    "still_available": "האם המוצר עדיין זמין?",
    "price_negotiation": "האם אפשר להוריד קצת את המחיר?",
    "meeting_request": "מתי אפשר להיפגש?",
    "confirm_meeting": "מאשר/ת את המפגש",
    "cant_meet": "אני לא יכול/ה להיפגש כרגע",
    "arrived": "הגעתי לנקודת המפגש",
    "thank_you": "תודה על העסקה!",
}


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_message_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    template_key: Mapped[str] = mapped_column(String(50))  # מפתח מתוך MESSAGE_TEMPLATES
    content: Mapped[str] = mapped_column(String(200))      # הטקסט שנשלח בפועל

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
