"""ניהול מוצרים - כולל זרימת אישור הורי"""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.security import require_child, require_parent, get_current_user
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.schemas.marketplace import ProductCreate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    child: User = Depends(require_child),
):
    """
    העלאת מוצר. הסטטוס ההתחלתי הוא pending_parent.
    ההורה חייב לאשר לפני שהמוצר יופיע בחיפוש.
    """
    store = db.query(Store).filter(Store.owner_id == child.id).first()
    if not store:
        raise HTTPException(400, "עליך ליצור חנות לפני העלאת מוצרים")

    product = Product(
        store_id=store.id,
        status="pending_parent",
        **data.model_dump(),
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # TODO: שלח התראה להורה לאישור המוצר
    return product


@router.get("/", response_model=List[ProductResponse])
def search_products(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    condition: Optional[str] = None,
    search: Optional[str] = Query(None, description="חיפוש בכותרת או בתיאור"),
    limit: int = Query(20, le=100),
    offset: int = 0,
):
    """חיפוש מוצרים פעילים בלבד (שאושרו)"""
    query = db.query(Product).filter(Product.status == "active")

    if category:
        query = query.filter(Product.category == category)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if condition:
        query = query.filter(Product.condition == condition)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Product.title.like(like), Product.description.like(like)))

    return query.order_by(Product.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/pending-approval", response_model=List[ProductResponse])
def get_pending_products_for_parent(
    db: Session = Depends(get_db),
    parent: User = Depends(require_parent),
):
    """הורה רואה את כל המוצרים שממתינים לאישורו"""
    children_ids = [c.id for c in db.query(User).filter(User.parent_id == parent.id).all()]
    if not children_ids:
        return []

    return (
        db.query(Product)
        .join(Store)
        .filter(Store.owner_id.in_(children_ids))
        .filter(Product.status == "pending_parent")
        .all()
    )


@router.post("/{product_id}/approve", response_model=ProductResponse)
def approve_product(
    product_id: int,
    db: Session = Depends(get_db),
    parent: User = Depends(require_parent),
):
    """הורה מאשר מוצר של ילדו"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "מוצר לא נמצא")

    store = db.query(Store).filter(Store.id == product.store_id).first()
    child = db.query(User).filter(User.id == store.owner_id).first()

    if child.parent_id != parent.id:
        raise HTTPException(403, "אינך ההורה של בעל המוצר")

    if product.status != "pending_parent":
        raise HTTPException(400, f"לא ניתן לאשר מוצר בסטטוס {product.status}")

    product.status = "active"
    product.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    return product


@router.post("/{product_id}/reject")
def reject_product(
    product_id: int,
    db: Session = Depends(get_db),
    parent: User = Depends(require_parent),
):
    """הורה דוחה מוצר"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "מוצר לא נמצא")

    store = db.query(Store).filter(Store.id == product.store_id).first()
    child = db.query(User).filter(User.id == store.owner_id).first()

    if child.parent_id != parent.id:
        raise HTTPException(403, "אינך ההורה של בעל המוצר")

    product.status = "removed"
    db.commit()
    return {"message": "המוצר נדחה והוסר"}


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "מוצר לא נמצא")
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    child: User = Depends(require_child),
):
    """ילד יכול להסיר מוצר שלו"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "מוצר לא נמצא")

    store = db.query(Store).filter(Store.id == product.store_id).first()
    if store.owner_id != child.id:
        raise HTTPException(403, "זה לא המוצר שלך")

    product.status = "removed"
    db.commit()
    return {"message": "המוצר הוסר"}
