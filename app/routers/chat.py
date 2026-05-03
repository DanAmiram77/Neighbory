"""צ'אט - הודעות תבנית בלבד, ללא טקסט חופשי"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.chat import Conversation, Message, MESSAGE_TEMPLATES
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.schemas.chat import (
    MessageSend,
    MessageResponse,
    ConversationResponse,
)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/templates")
def get_templates(_: User = Depends(get_current_user)):
    """רשימת התבניות הזמינות"""
    return MESSAGE_TEMPLATES


@router.post("/send", response_model=MessageResponse)
def send_message(
    data: MessageSend,
    db: Session = Depends(get_db),
    sender: User = Depends(get_current_user),
):
    """
    שליחת הודעה. רק מתוך תבניות מוגדרות מראש.
    אם לא קיימת שיחה - נוצרת חדשה.
    """
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(404, "מוצר לא נמצא")

    if product.status != "active":
        raise HTTPException(400, "לא ניתן לשלוח הודעות על מוצר שאינו פעיל")

    seller = db.query(User).join(Store).filter(Store.id == product.store_id).first()
    if not seller:
        raise HTTPException(404, "מוכר לא נמצא")

    # קונה = שולח ההודעה (אם הוא לא המוכר)
    if sender.id == seller.id:
        raise HTTPException(400, "לא ניתן לשלוח הודעה לעצמך")

    # חיפוש שיחה קיימת
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.product_id == data.product_id,
            or_(
                and_(Conversation.buyer_id == sender.id, Conversation.seller_id == seller.id),
                and_(Conversation.buyer_id == seller.id, Conversation.seller_id == sender.id),
            ),
        )
        .first()
    )

    if not conversation:
        conversation = Conversation(
            product_id=data.product_id,
            buyer_id=sender.id,
            seller_id=seller.id,
        )
        db.add(conversation)
        db.flush()

    # יצירת ההודעה - התוכן מגיע מהתבנית (לא מהמשתמש)
    content = MESSAGE_TEMPLATES[data.template_key]
    message = Message(
        conversation_id=conversation.id,
        sender_id=sender.id,
        template_key=data.template_key,
        content=content,
    )
    db.add(message)
    conversation.last_message_at = datetime.utcnow()

    db.commit()
    db.refresh(message)

    # TODO: שלח push notification לנמען
    return message


@router.get("/conversations", response_model=List[ConversationResponse])
def list_my_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """רשימת השיחות של המשתמש"""
    return (
        db.query(Conversation)
        .filter(or_(Conversation.buyer_id == user.id, Conversation.seller_id == user.id))
        .order_by(Conversation.last_message_at.desc())
        .all()
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """צפייה בשיחה ספציפית"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(404, "שיחה לא נמצאה")

    if user.id not in (conversation.buyer_id, conversation.seller_id):
        # הורים יכולים גם לראות שיחות של ילדיהם
        if user.role == "parent":
            buyer = db.query(User).filter(User.id == conversation.buyer_id).first()
            seller = db.query(User).filter(User.id == conversation.seller_id).first()
            if buyer.parent_id != user.id and seller.parent_id != user.id:
                raise HTTPException(403, "אין לך גישה לשיחה זו")
        else:
            raise HTTPException(403, "אין לך גישה לשיחה זו")

    return conversation
