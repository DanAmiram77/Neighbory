"""מפגשים פיזיים בנקודות בטוחות + דירוגים"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.meeting import Meeting, SafePoint
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.schemas.chat import (
    MeetingCreate,
    MeetingResponse,
    SafePointResponse,
    RatingSubmit,
)

router = APIRouter(tags=["Meetings & Safe Points"])


@router.get("/safe-points", response_model=List[SafePointResponse])
def list_safe_points(
    city: str = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """רשימת נקודות מפגש בטוחות מאושרות מראש"""
    query = db.query(SafePoint)
    if city:
        query = query.filter(SafePoint.city == city)
    return query.all()


@router.post("/meetings", response_model=MeetingResponse, status_code=201)
def schedule_meeting(
    data: MeetingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """קביעת מפגש בנקודה בטוחה"""
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product or product.status != "active":
        raise HTTPException(404, "מוצר לא נמצא או לא פעיל")

    safe_point = db.query(SafePoint).filter(SafePoint.id == data.safe_point_id).first()
    if not safe_point:
        raise HTTPException(404, "נקודת המפגש לא קיימת")

    # תאריך המפגש חייב להיות בעתיד
    if data.scheduled_at <= datetime.utcnow():
        raise HTTPException(400, "זמן המפגש חייב להיות בעתיד")

    seller = db.query(User).join(Store).filter(Store.id == product.store_id).first()
    if user.id == seller.id:
        raise HTTPException(400, "אתה המוכר - הקונה הוא זה שצריך לבקש מפגש")

    meeting = Meeting(
        product_id=product.id,
        buyer_id=user.id,
        seller_id=seller.id,
        safe_point_id=safe_point.id,
        scheduled_at=data.scheduled_at,
        status="scheduled",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # TODO: שלח התראה למוכר, לקונה, ולשני ההורים
    return meeting


@router.get("/meetings", response_model=List[MeetingResponse])
def list_my_meetings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """רשימת המפגשים של המשתמש"""
    return (
        db.query(Meeting)
        .filter(or_(Meeting.buyer_id == user.id, Meeting.seller_id == user.id))
        .order_by(Meeting.scheduled_at.desc())
        .all()
    )


@router.post("/meetings/{meeting_id}/complete", response_model=MeetingResponse)
def complete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """סימון מפגש כהושלם - המוצר עובר לסטטוס sold"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(404, "מפגש לא נמצא")

    if user.id not in (meeting.buyer_id, meeting.seller_id):
        raise HTTPException(403, "אינך משתתף במפגש זה")

    if meeting.status != "scheduled":
        raise HTTPException(400, f"לא ניתן להשלים מפגש בסטטוס {meeting.status}")

    meeting.status = "completed"

    # עדכון המוצר
    product = db.query(Product).filter(Product.id == meeting.product_id).first()
    if product:
        product.status = "sold"

    # עדכון סטטיסטיקות החנות
    store = db.query(Store).filter(Store.id == product.store_id).first()
    if store:
        store.total_sales += 1

    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("/meetings/{meeting_id}/rate")
def rate_meeting(
    meeting_id: int,
    data: RatingSubmit,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """דירוג הצד השני לאחר מפגש שהושלם"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(404, "מפגש לא נמצא")

    if meeting.status != "completed":
        raise HTTPException(400, "אפשר לדרג רק מפגשים שהושלמו")

    if user.id == meeting.buyer_id:
        if meeting.buyer_rating is not None:
            raise HTTPException(400, "כבר דירגת את המפגש")
        meeting.buyer_rating = data.rating  # הקונה מדרג את המוכר
        rated_user_id = meeting.seller_id
    elif user.id == meeting.seller_id:
        if meeting.seller_rating is not None:
            raise HTTPException(400, "כבר דירגת את המפגש")
        meeting.seller_rating = data.rating  # המוכר מדרג את הקונה
        rated_user_id = meeting.buyer_id
    else:
        raise HTTPException(403, "אינך משתתף במפגש זה")

    # עדכון ממוצע הדירוג של החנות של המדורג (אם יש לו)
    store = db.query(Store).filter(Store.owner_id == rated_user_id).first()
    if store:
        # חישוב ממוצע פשוט - במציאות עדיף incremental update
        all_meetings = (
            db.query(Meeting)
            .filter(
                or_(
                    Meeting.seller_id == rated_user_id,
                    Meeting.buyer_id == rated_user_id,
                ),
                Meeting.status == "completed",
            )
            .all()
        )
        ratings = []
        for m in all_meetings:
            if m.seller_id == rated_user_id and m.buyer_rating is not None:
                ratings.append(m.buyer_rating)
            elif m.buyer_id == rated_user_id and m.seller_rating is not None:
                ratings.append(m.seller_rating)
        if ratings:
            store.rating = sum(ratings) / len(ratings)

    db.commit()
    return {"message": "הדירוג נקלט בהצלחה"}
