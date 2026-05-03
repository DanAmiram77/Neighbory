"""סכמות צ'אט ומפגשים"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

from app.models.chat import MESSAGE_TEMPLATES


class MessageSend(BaseModel):
    """שליחת הודעה - תבנית בלבד, ללא טקסט חופשי"""
    product_id: int
    template_key: str

    @field_validator("template_key")
    @classmethod
    def valid_template(cls, v: str) -> str:
        if v not in MESSAGE_TEMPLATES:
            raise ValueError(f"תבנית לא חוקית. מותרות: {list(MESSAGE_TEMPLATES.keys())}")
        return v


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    template_key: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    product_id: int
    buyer_id: int
    seller_id: int
    last_message_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class SafePointResponse(BaseModel):
    id: int
    name: str
    address: str
    city: str
    type: str
    latitude: float
    longitude: float

    class Config:
        from_attributes = True


class MeetingCreate(BaseModel):
    product_id: int
    safe_point_id: int
    scheduled_at: datetime


class MeetingResponse(BaseModel):
    id: int
    product_id: int
    buyer_id: int
    seller_id: int
    safe_point_id: int
    scheduled_at: datetime
    status: str
    buyer_rating: Optional[int] = None
    seller_rating: Optional[int] = None

    class Config:
        from_attributes = True


class RatingSubmit(BaseModel):
    rating: int = Field(ge=1, le=5)
