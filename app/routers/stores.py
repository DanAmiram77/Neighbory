"""ניהול חנויות"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_child, get_current_user
from app.models.store import Store
from app.models.user import User
from app.schemas.marketplace import StoreCreate, StoreUpdate, StoreResponse

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.post("/", response_model=StoreResponse, status_code=201)
def create_store(
    data: StoreCreate,
    db: Session = Depends(get_db),
    child: User = Depends(require_child),
):
    """יצירת חנות - ילד יכול לפתוח חנות אחת בלבד"""
    existing = db.query(Store).filter(Store.owner_id == child.id).first()
    if existing:
        raise HTTPException(400, "כבר יש לך חנות. ניתן לערוך אותה במקום.")

    store = Store(owner_id=child.id, **data.model_dump())
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@router.get("/me", response_model=StoreResponse)
def get_my_store(
    db: Session = Depends(get_db),
    child: User = Depends(require_child),
):
    store = db.query(Store).filter(Store.owner_id == child.id).first()
    if not store:
        raise HTTPException(404, "עדיין לא יצרת חנות")
    return store


@router.patch("/me", response_model=StoreResponse)
def update_my_store(
    data: StoreUpdate,
    db: Session = Depends(get_db),
    child: User = Depends(require_child),
):
    store = db.query(Store).filter(Store.owner_id == child.id).first()
    if not store:
        raise HTTPException(404, "עדיין לא יצרת חנות")

    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(store, key, value)

    db.commit()
    db.refresh(store)
    return store


@router.get("/{store_id}", response_model=StoreResponse)
def get_store(
    store_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(404, "חנות לא נמצאה")
    return store
