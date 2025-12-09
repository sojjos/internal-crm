"""Stock management schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel

from app.models.stock import StockMovementType, StockMovementReason


class StockLocationBase(BaseModel):
    name: str
    address: Optional[str] = None
    description: Optional[str] = None
    is_default: bool = False


class StockLocationCreate(StockLocationBase):
    pass


class StockLocationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class StockLocationResponse(StockLocationBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StockCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class StockCategoryCreate(StockCategoryBase):
    pass


class StockCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None


class StockCategoryResponse(StockCategoryBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StockArticleBase(BaseModel):
    reference: str
    name: str
    description: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    default_supplier_id: Optional[int] = None
    purchase_price_htva: Optional[Decimal] = None
    sale_price_htva: Optional[Decimal] = None
    vat_rate: Decimal = Decimal("21.00")
    unit: str = "piece"
    min_stock_level: Decimal = Decimal("0")
    max_stock_level: Optional[Decimal] = None
    reorder_quantity: Optional[Decimal] = None
    article_id: Optional[int] = None


class StockArticleCreate(StockArticleBase):
    pass


class StockArticleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    default_supplier_id: Optional[int] = None
    purchase_price_htva: Optional[Decimal] = None
    sale_price_htva: Optional[Decimal] = None
    vat_rate: Optional[Decimal] = None
    unit: Optional[str] = None
    min_stock_level: Optional[Decimal] = None
    max_stock_level: Optional[Decimal] = None
    reorder_quantity: Optional[Decimal] = None
    is_active: Optional[bool] = None


class StockArticleResponse(StockArticleBase):
    id: int
    is_active: bool
    created_at: datetime

    # Computed fields
    total_quantity: Optional[Decimal] = None
    is_below_minimum: Optional[bool] = None
    category_name: Optional[str] = None
    supplier_name: Optional[str] = None

    class Config:
        from_attributes = True


class StockItemResponse(BaseModel):
    id: int
    article_id: int
    location_id: int
    quantity: Decimal
    reserved_quantity: Decimal
    available_quantity: Decimal
    last_movement_date: Optional[datetime]

    article_name: Optional[str] = None
    location_name: Optional[str] = None

    class Config:
        from_attributes = True


class StockMovementBase(BaseModel):
    article_id: int
    location_id: int
    movement_type: StockMovementType
    reason: StockMovementReason = StockMovementReason.AUTRE
    quantity: Decimal
    unit_price: Optional[Decimal] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class StockMovementCreate(StockMovementBase):
    purchase_id: Optional[int] = None
    invoice_id: Optional[int] = None
    intervention_id: Optional[int] = None


class StockMovementResponse(StockMovementBase):
    id: int
    quantity_before: Optional[Decimal]
    quantity_after: Optional[Decimal]
    purchase_id: Optional[int]
    invoice_id: Optional[int]
    intervention_id: Optional[int]
    movement_date: datetime
    created_at: datetime

    article_name: Optional[str] = None
    location_name: Optional[str] = None

    class Config:
        from_attributes = True


class StockAlert(BaseModel):
    """Stock alert for low inventory."""
    article_id: int
    article_reference: str
    article_name: str
    current_quantity: Decimal
    min_stock_level: Decimal
    reorder_quantity: Optional[Decimal]
    supplier_name: Optional[str]
