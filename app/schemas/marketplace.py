"""סכמות חנות ומוצרים"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from app.models.product import ALLOWED_CATEGORIES, ALLOWED_CONDITIONS


class StoreCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    latitude: float
    longitude: float
    delivery_radius_km: int = Field(default=5, ge=1, le=50)


class StoreUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    delivery_radius_km: Optional[int] = Field(None, ge=1, le=50)


class StoreResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str]
    avatar_url: Optional[str]
    delivery_radius_km: int
    rating: float
    total_sales: int

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=10, max_length=1000)
    category: str
    condition: str
    price: float = Field(gt=0, le=settings.MAX_PRODUCT_PRICE)
    images: List[str] = Field(default_factory=list, max_length=5)

    @field_validator("category")
    @classmethod
    def valid_category(cls, v: str) -> str:
        if v not in ALLOWED_CATEGORIES:
            raise ValueError(f"קטגוריה לא חוקית. מותר: {ALLOWED_CATEGORIES}")
        return v

    @field_validator("condition")
    @classmethod
    def valid_condition(cls, v: str) -> str:
        if v not in ALLOWED_CONDITIONS:
            raise ValueError(f"מצב לא חוקי. מותר: {ALLOWED_CONDITIONS}")
        return v


class ProductResponse(BaseModel):
    id: int
    store_id: int
    title: str
    description: str
    images: List[str]
    category: str
    condition: str
    price: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProductSearchParams(BaseModel):
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    condition: Optional[str] = None
    city: Optional[str] = None
    search: Optional[str] = None  # טקסט חופשי לחיפוש בכותרת/תיאור
