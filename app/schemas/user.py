"""סכמות Pydantic למשתמשים"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class ChildRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    username: str = Field(min_length=3, max_length=30)
    full_name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=13, le=18)  # רק 13-18 ב-MVP
    city: str
    neighborhood: Optional[str] = None
    parent_email: EmailStr  # חובה - אימייל של הורה
    parent_phone: str = Field(min_length=9, max_length=15)

    @field_validator("username")
    @classmethod
    def username_not_real_name(cls, v: str) -> str:
        """אסור לכלול שם מלא אמיתי בשם משתמש (הנחיה בסיסית)"""
        if " " in v:
            raise ValueError("שם משתמש לא יכול להכיל רווחים")
        return v.lower()


class ParentRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=9, max_length=15)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    """מידע שנחשף לציבור - ללא פרטים רגישים"""
    id: int
    username: str
    city: Optional[str] = None
    role: str

    class Config:
        from_attributes = True


class UserPrivate(UserPublic):
    """מידע מלא - רק למשתמש עצמו או להורה"""
    email: str
    full_name: str
    age: Optional[int] = None
    is_approved: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPrivate


class ApprovalRequest(BaseModel):
    """בקשה לאישור ילד ע״י הורה"""
    approval_code: str
