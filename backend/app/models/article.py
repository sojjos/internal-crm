"""Article/Service catalog model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, Enum
import enum

from app.db.database import Base


class ArticleType(str, enum.Enum):
    """Type of article."""
    SERVICE = "service"
    PRODUCT = "product"
    EXPENSE = "expense"  # Travel, admin fees, etc.


class BillingMode(str, enum.Enum):
    """Billing mode for the article."""
    HOUR = "hour"  # Price per hour
    DAY = "day"  # Price per day
    UNIT = "unit"  # Per piece/unit
    KM = "km"  # Per kilometer
    FLAT = "flat"  # Flat rate / forfait


class Article(Base):
    """Article/Service catalog item."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)

    # Basic information
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Type and billing
    article_type = Column(Enum(ArticleType), default=ArticleType.SERVICE)
    billing_mode = Column(Enum(BillingMode), default=BillingMode.HOUR)

    # Pricing
    base_price = Column(Float, nullable=False)  # HTVA (excluding VAT)
    default_vat_rate = Column(Float, default=21.0)

    # Options
    allow_price_modification = Column(Boolean, default=True)
    allow_discount = Column(Boolean, default=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Article {self.code}: {self.name}>"

    @property
    def unit_label(self) -> str:
        """Return unit label based on billing mode."""
        labels = {
            BillingMode.HOUR: "h",
            BillingMode.DAY: "j",
            BillingMode.UNIT: "u",
            BillingMode.KM: "km",
            BillingMode.FLAT: "forfait",
        }
        return labels.get(self.billing_mode, "u")
