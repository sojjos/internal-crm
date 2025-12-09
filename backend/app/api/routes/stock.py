"""Stock management routes."""
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.stock import (
    StockLocation, StockCategory, StockArticle, StockItem, StockMovement,
    StockMovementType, StockMovementReason
)
from app.schemas.stock import (
    StockLocationCreate, StockLocationUpdate, StockLocationResponse,
    StockCategoryCreate, StockCategoryUpdate, StockCategoryResponse,
    StockArticleCreate, StockArticleUpdate, StockArticleResponse,
    StockItemResponse, StockMovementCreate, StockMovementResponse, StockAlert
)

router = APIRouter()


# ============ Locations ============

@router.get("/locations", response_model=List[StockLocationResponse])
def get_locations(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    query = db.query(StockLocation)
    if is_active is not None:
        query = query.filter(StockLocation.is_active == is_active)
    return query.order_by(StockLocation.name).all()


@router.post("/locations", response_model=StockLocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    location_in: StockLocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    location = StockLocation(**location_in.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.put("/locations/{location_id}", response_model=StockLocationResponse)
def update_location(
    location_id: int,
    location_in: StockLocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    location = db.query(StockLocation).filter(StockLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    for field, value in location_in.model_dump(exclude_unset=True).items():
        setattr(location, field, value)

    db.commit()
    db.refresh(location)
    return location


# ============ Categories ============

@router.get("/categories", response_model=List[StockCategoryResponse])
def get_categories(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    query = db.query(StockCategory)
    if is_active is not None:
        query = query.filter(StockCategory.is_active == is_active)
    return query.order_by(StockCategory.name).all()


@router.post("/categories", response_model=StockCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: StockCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    category = StockCategory(**category_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# ============ Articles ============

@router.get("/articles", response_model=List[StockArticleResponse])
def get_articles(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    below_minimum: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    query = db.query(StockArticle).options(
        joinedload(StockArticle.category),
        joinedload(StockArticle.default_supplier)
    )

    if category_id:
        query = query.filter(StockArticle.category_id == category_id)
    if supplier_id:
        query = query.filter(StockArticle.default_supplier_id == supplier_id)
    if is_active is not None:
        query = query.filter(StockArticle.is_active == is_active)
    if search:
        query = query.filter(
            (StockArticle.reference.ilike(f"%{search}%")) |
            (StockArticle.name.ilike(f"%{search}%")) |
            (StockArticle.barcode.ilike(f"%{search}%"))
        )

    articles = query.order_by(StockArticle.name).offset(skip).limit(limit).all()

    # Add computed fields
    result = []
    for article in articles:
        # Get total quantity across all locations
        total_qty = db.query(func.sum(StockItem.quantity)).filter(
            StockItem.article_id == article.id
        ).scalar() or Decimal("0")

        article_dict = {
            **article.__dict__,
            "total_quantity": total_qty,
            "is_below_minimum": total_qty < article.min_stock_level,
            "category_name": article.category.name if article.category else None,
            "supplier_name": article.default_supplier.name if article.default_supplier else None,
        }

        if below_minimum is not None:
            if below_minimum and not article_dict["is_below_minimum"]:
                continue
            if not below_minimum and article_dict["is_below_minimum"]:
                continue

        result.append(article_dict)

    return result


@router.post("/articles", response_model=StockArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article(
    article_in: StockArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Check reference uniqueness
    existing = db.query(StockArticle).filter(
        StockArticle.reference == article_in.reference
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Reference already exists")

    article = StockArticle(**article_in.model_dump())
    db.add(article)
    db.commit()
    db.refresh(article)

    # Create initial stock items for default location
    default_location = db.query(StockLocation).filter(
        StockLocation.is_default == True
    ).first()
    if default_location:
        stock_item = StockItem(
            article_id=article.id,
            location_id=default_location.id,
            quantity=Decimal("0")
        )
        db.add(stock_item)
        db.commit()

    return article


@router.get("/articles/{article_id}", response_model=StockArticleResponse)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    article = db.query(StockArticle).options(
        joinedload(StockArticle.category),
        joinedload(StockArticle.default_supplier)
    ).filter(StockArticle.id == article_id).first()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    total_qty = db.query(func.sum(StockItem.quantity)).filter(
        StockItem.article_id == article.id
    ).scalar() or Decimal("0")

    return {
        **article.__dict__,
        "total_quantity": total_qty,
        "is_below_minimum": total_qty < article.min_stock_level,
        "category_name": article.category.name if article.category else None,
        "supplier_name": article.default_supplier.name if article.default_supplier else None,
    }


@router.put("/articles/{article_id}", response_model=StockArticleResponse)
def update_article(
    article_id: int,
    article_in: StockArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    article = db.query(StockArticle).filter(StockArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    for field, value in article_in.model_dump(exclude_unset=True).items():
        setattr(article, field, value)

    db.commit()
    db.refresh(article)
    return article


# ============ Stock Items ============

@router.get("/items", response_model=List[StockItemResponse])
def get_stock_items(
    article_id: Optional[int] = None,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    query = db.query(StockItem).options(
        joinedload(StockItem.article),
        joinedload(StockItem.location)
    )

    if article_id:
        query = query.filter(StockItem.article_id == article_id)
    if location_id:
        query = query.filter(StockItem.location_id == location_id)

    items = query.all()

    return [
        {
            **item.__dict__,
            "available_quantity": item.quantity - item.reserved_quantity,
            "article_name": item.article.name if item.article else None,
            "location_name": item.location.name if item.location else None,
        }
        for item in items
    ]


# ============ Movements ============

@router.get("/movements", response_model=List[StockMovementResponse])
def get_movements(
    skip: int = 0,
    limit: int = 100,
    article_id: Optional[int] = None,
    location_id: Optional[int] = None,
    movement_type: Optional[StockMovementType] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    query = db.query(StockMovement).options(
        joinedload(StockMovement.article),
        joinedload(StockMovement.location)
    )

    if article_id:
        query = query.filter(StockMovement.article_id == article_id)
    if location_id:
        query = query.filter(StockMovement.location_id == location_id)
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)
    if date_from:
        query = query.filter(StockMovement.movement_date >= date_from)
    if date_to:
        query = query.filter(StockMovement.movement_date <= date_to)

    movements = query.order_by(StockMovement.movement_date.desc()).offset(skip).limit(limit).all()

    return [
        {
            **m.__dict__,
            "article_name": m.article.name if m.article else None,
            "location_name": m.location.name if m.location else None,
        }
        for m in movements
    ]


@router.post("/movements", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
def create_movement(
    movement_in: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a stock movement and update stock levels."""
    # Get or create stock item
    stock_item = db.query(StockItem).filter(
        StockItem.article_id == movement_in.article_id,
        StockItem.location_id == movement_in.location_id
    ).first()

    if not stock_item:
        stock_item = StockItem(
            article_id=movement_in.article_id,
            location_id=movement_in.location_id,
            quantity=Decimal("0")
        )
        db.add(stock_item)
        db.flush()

    quantity_before = stock_item.quantity

    # Apply movement
    if movement_in.movement_type == StockMovementType.ENTREE:
        stock_item.quantity += movement_in.quantity
    elif movement_in.movement_type == StockMovementType.SORTIE:
        if stock_item.quantity < movement_in.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {stock_item.quantity}"
            )
        stock_item.quantity -= movement_in.quantity
    elif movement_in.movement_type in [StockMovementType.AJUSTEMENT, StockMovementType.INVENTAIRE]:
        stock_item.quantity = movement_in.quantity

    stock_item.last_movement_date = datetime.utcnow()

    # Create movement record
    movement = StockMovement(
        **movement_in.model_dump(),
        quantity_before=quantity_before,
        quantity_after=stock_item.quantity,
        created_by_id=current_user.id
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)

    return movement


# ============ Alerts ============

@router.get("/alerts", response_model=List[StockAlert])
def get_stock_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get articles below minimum stock level."""
    articles = db.query(StockArticle).filter(
        StockArticle.is_active == True
    ).options(
        joinedload(StockArticle.default_supplier)
    ).all()

    alerts = []
    for article in articles:
        total_qty = db.query(func.sum(StockItem.quantity)).filter(
            StockItem.article_id == article.id
        ).scalar() or Decimal("0")

        if total_qty < article.min_stock_level:
            alerts.append(StockAlert(
                article_id=article.id,
                article_reference=article.reference,
                article_name=article.name,
                current_quantity=total_qty,
                min_stock_level=article.min_stock_level,
                reorder_quantity=article.reorder_quantity,
                supplier_name=article.default_supplier.name if article.default_supplier else None
            ))

    return alerts
