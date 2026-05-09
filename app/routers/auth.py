"""נקודות קצה של אימות והרשמה"""
import secrets
from datetime import datetime, timedelta, timezone

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
from app.core.email import send_parent_approval_email, send_password_reset_email
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
    existing = db.query(User).filter(User.email == data.email).first()

    if existing:
        # Allow claiming a placeholder account created when a child registered first
        if existing.role == "parent" and existing.full_name == "Parent Pending":
            existing.hashed_password = hash_password(data.password)
            existing.full_name = data.full_name
            existing.is_approved = True
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(400, "האימייל כבר קיים במערכת")

    parent = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        role="parent",
        username=f"parent_{secrets.token_hex(4)}",
        full_name=data.full_name,
        is_approved=True,
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

    # יצירת username אוטומטי מהאימייל
    prefix = ''.join(c for c in data.email.split('@')[0].lower() if c.isalnum() or c == '_')[:15]
    username = f"{prefix}_{secrets.token_hex(3)}"

    # חיפוש/יצירת הורה
    parent = db.query(User).filter(User.email == data.parent_email).first()
    if not parent:
        parent = User(
            email=data.parent_email,
            hashed_password=hash_password(secrets.token_urlsafe(16)),
            role="parent",
            username=f"parent_{secrets.token_hex(4)}",
            full_name="Parent Pending",
            is_approved=False,
        )
        db.add(parent)
        db.flush()

    # יצירת קוד אישור
    approval_code = secrets.token_hex(3).upper()  # 6 תווים

    child = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        role="child",
        username=username,
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
    }


@router.get("/parent/pending-children")
def get_pending_children(
    db: Session = Depends(get_db),
    parent: User = Depends(require_parent),
):
    """רשימת ילדים שממתינים לאישור ההורה"""
    children = db.query(User).filter(
        User.parent_id == parent.id,
        User.role == "child",
        User.is_approved == False,  # noqa: E712
    ).all()
    return [{"id": c.id, "username": c.username, "full_name": c.full_name, "age": c.age} for c in children]


@router.post("/parent/resend-approval/{child_id}")
def resend_approval(
    child_id: int,
    db: Session = Depends(get_db),
    parent: User = Depends(require_parent),
):
    """שליחה מחדש של קוד אישור לילד"""
    child = db.query(User).filter(
        User.id == child_id,
        User.role == "child",
        User.parent_id == parent.id,
    ).first()
    if not child:
        raise HTTPException(404, "ילד לא נמצא או שאינך ההורה שלו")
    if child.is_approved:
        raise HTTPException(400, "החשבון כבר מאושר")

    approval_code = secrets.token_hex(3).upper()
    child.approval_code = approval_code
    db.commit()

    send_parent_approval_email(
        parent_email=parent.email,
        child_name=child.full_name,
        child_username=child.username,
        approval_code=approval_code,
    )
    return {"message": f"קוד אישור חדש נשלח לאימייל {parent.email}"}


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


@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "אם האימייל קיים, ישלח קישור לאיפוס סיסמה."}

    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    send_password_reset_email(
        to_email=user.email,
        full_name=user.full_name,
        reset_token=token,
    )
    return {"message": "אם האימייל קיים, ישלח קישור לאיפוס סיסמה."}


@router.post("/reset-password")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    if len(new_password) < 8:
        raise HTTPException(400, "הסיסמה חייבת להכיל לפחות 8 תווים")

    user = db.query(User).filter(User.password_reset_token == token).first()
    if not user or not user.password_reset_expires:
        raise HTTPException(400, "קישור לא תקין")

    if datetime.now(timezone.utc) > user.password_reset_expires.replace(tzinfo=timezone.utc):
        raise HTTPException(400, "הקישור פג תוקף. בקשו קישור חדש.")

    user.hashed_password = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()

    return {"message": "הסיסמה עודכנה בהצלחה"}
