"""Article schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.article import ArticleType, BillingMode


class ArticleBase(BaseModel):
    """Base article schema."""
    code: str
    name: str
    description: Optional[str] = None
    article_type: ArticleType = ArticleType.SERVICE
    billing_mode: BillingMode = BillingMode.HOUR
    base_price: float
    default_vat_rate: float = 21.0
    allow_price_modification: bool = True
    allow_discount: bool = True


class ArticleCreate(ArticleBase):
    """Schema for creating an article."""
    pass


class ArticleUpdate(BaseModel):
    """Schema for updating an article."""
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    article_type: Optional[ArticleType] = None
    billing_mode: Optional[BillingMode] = None
    base_price: Optional[float] = None
    default_vat_rate: Optional[float] = None
    allow_price_modification: Optional[bool] = None
    allow_discount: Optional[bool] = None
    is_active: Optional[bool] = None


class ArticleResponse(ArticleBase):
    """Schema for article response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
