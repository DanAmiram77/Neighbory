"""נקודות קצה של אימות והרשמה"""
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    get_current_user,
    require_parent,
)
from app.models.user import User
from app.core.email import send_parent_approval_email
from app.schemas.user import (
    ChildRegister,
    ParentRegister,
    Token,
    UserPrivate,
    ApprovalRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register/parent", response_model=UserPrivate, status_code=201)
def register_parent(data: ParentRegister, db: Session = Depends(get_db)):
    """הרשמת הורה - מאושר מיד"""
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "האימייל כבר קיים במערכת")

    parent = User(
        email=data.email,
        phone=data.phone,
        hashed_password=hash_password(data.password),
        role="parent",
        username=f"parent_{secrets.token_hex(4)}",
        full_name=data.full_name,
        is_approved=True,  # הורים מאושרים מיד
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent


@router.post("/register/child", status_code=201)
def register_child(data: ChildRegister, db: Session = Depends(get_db)):
    """
    הרשמת ילד. החשבון לא פעיל עד שההורה מאשר.
    מחזיר קוד אישור שיש להעביר להורה (במציאות - יישלח ב-SMS/אימייל).
    """
    # בדיקה שהאימייל לא קיים
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "האימייל כבר קיים במערכת")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "שם המשתמש כבר תפוס")

    # חיפוש/יצירת הורה
    parent = db.query(User).filter(User.email == data.parent_email).first()
    if not parent:
        # יוצרים הורה placeholder - הוא יצטרך להירשם כדי לאשר
        parent = User(
            email=data.parent_email,
            phone=data.parent_phone,
            hashed_password=hash_password(secrets.token_urlsafe(16)),  # סיסמה זמנית
            role="parent",
            username=f"parent_{secrets.token_hex(4)}",
            full_name="Parent Pending",
            is_approved=False,  # צריך להירשם בעצמו
        )
        db.add(parent)
        db.flush()

    # יצירת קוד אישור
    approval_code = secrets.token_hex(3).upper()  # 6 תווים

    child = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        role="child",
        username=data.username,
        full_name=data.full_name,
        age=data.age,
        city=data.city,
        neighborhood=data.neighborhood,
        parent_id=parent.id,
        is_approved=False,
        approval_code=approval_code,
    )
    db.add(child)
    db.commit()
    db.refresh(child)

    send_parent_approval_email(
        parent_email=parent.email,
        child_name=child.full_name,
        child_username=child.username,
        approval_code=approval_code,
    )
    return {
        "message": "הרשמה הצליחה. ההורה צריך לאשר את החשבון.",
        "child_id": child.id,
        "parent_email": parent.email,
        "approval_code_for_testing": approval_code,  # רק לבדיקות!
    }


@router.post("/parent/approve/{child_id}")
def approve_child(
    child_id: int,
    data: ApprovalRequest,
    db: Session = Depends(get_db),
    parent: User = Depends(require_parent),
):
    """אישור ילד ע״י הורה שמחובר למערכת"""
    child = db.query(User).filter(
        User.id == child_id,
        User.role == "child",
        User.parent_id == parent.id,
    ).first()

    if not child:
        raise HTTPException(404, "ילד לא נמצא או שאינך ההורה שלו")

    if child.is_approved:
        raise HTTPException(400, "החשבון כבר מאושר")

    if child.approval_code != data.approval_code.upper():
        raise HTTPException(400, "קוד אישור שגוי")

    child.is_approved = True
    child.approval_code = None
    db.commit()

    return {"message": f"החשבון של {child.username} אושר בהצלחה"}


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    התחברות. משתמש ב-OAuth2PasswordRequestForm:
    - username = email
    - password = password
    """
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "אימייל או סיסמה שגויים")

    if not user.is_approved:
        raise HTTPException(
            403,
            "החשבון לא אושר. אם אתה ילד - ההורה צריך לאשר. אם אתה הורה - צור קשר עם התמיכה.",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return Token(access_token=token, user=user)


@router.get("/me", response_model=UserPrivate)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
