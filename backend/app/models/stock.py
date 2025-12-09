"""Stock and inventory management models."""
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Boolean, Enum, Numeric
from sqlalchemy.orm import relationship

from app.db.database import Base


class StockMovementType(str, PyEnum):
    """Type of stock movement."""
    ENTREE = "ENTREE"          # Stock coming in
    SORTIE = "SORTIE"          # Stock going out
    AJUSTEMENT = "AJUSTEMENT"  # Manual adjustment
    INVENTAIRE = "INVENTAIRE"  # Inventory correction


class StockMovementReason(str, PyEnum):
    """Reason for stock movement."""
    ACHAT = "ACHAT"
    VENTE = "VENTE"
    INTERVENTION = "INTERVENTION"
    PERTE = "PERTE"
    CASSE = "CASSE"
    DON = "DON"
    RETOUR_CLIENT = "RETOUR_CLIENT"
    RETOUR_FOURNISSEUR = "RETOUR_FOURNISSEUR"
    CORRECTION = "CORRECTION"
    AUTRE = "AUTRE"


class StockLocation(Base):
    """Stock storage location."""
    __tablename__ = "stock_locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    stock_items = relationship("StockItem", back_populates="location")


class StockCategory(Base):
    """Category for stock items."""
    __tablename__ = "stock_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("stock_categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    parent = relationship("StockCategory", remote_side=[id], backref="children")
    articles = relationship("StockArticle", back_populates="category")


class StockArticle(Base):
    """Article that can be stocked."""
    __tablename__ = "stock_articles"

    id = Column(Integer, primary_key=True, index=True)

    # Identification
    reference = Column(String(50), unique=True, nullable=False)
    barcode = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Category and supplier
    category_id = Column(Integer, ForeignKey("stock_categories.id"), nullable=True)
    default_supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    # Pricing
    purchase_price_htva = Column(Numeric(10, 2), nullable=True)
    sale_price_htva = Column(Numeric(10, 2), nullable=True)
    vat_rate = Column(Numeric(5, 2), default=21.00)

    # Stock management
    unit = Column(String(20), default="pièce")  # pièce, kg, litre, m², etc.
    min_stock_level = Column(Numeric(10, 2), default=0)  # Alert threshold
    max_stock_level = Column(Numeric(10, 2), nullable=True)
    reorder_quantity = Column(Numeric(10, 2), nullable=True)  # Suggested order qty

    # Link to existing article catalog (optional)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("StockCategory", back_populates="articles")
    default_supplier = relationship("Supplier", backref="stock_articles")
    article = relationship("Article", backref="stock_article")
    stock_items = relationship("StockItem", back_populates="article")
    movements = relationship("StockMovement", back_populates="article")


class StockItem(Base):
    """Stock level for an article at a location."""
    __tablename__ = "stock_items"

    id = Column(Integer, primary_key=True, index=True)

    article_id = Column(Integer, ForeignKey("stock_articles.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("stock_locations.id"), nullable=False)

    quantity = Column(Numeric(10, 2), default=0)
    reserved_quantity = Column(Numeric(10, 2), default=0)  # Reserved for orders

    last_inventory_date = Column(DateTime, nullable=True)
    last_movement_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    article = relationship("StockArticle", back_populates="stock_items")
    location = relationship("StockLocation", back_populates="stock_items")

    @property
    def available_quantity(self):
        """Quantity available (not reserved)."""
        return self.quantity - self.reserved_quantity


class StockMovement(Base):
    """Stock movement record."""
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)

    article_id = Column(Integer, ForeignKey("stock_articles.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("stock_locations.id"), nullable=False)

    # Movement details
    movement_type = Column(Enum(StockMovementType), nullable=False)
    reason = Column(Enum(StockMovementReason), default=StockMovementReason.AUTRE)
    quantity = Column(Numeric(10, 2), nullable=False)  # Positive for IN, negative for OUT
    unit_price = Column(Numeric(10, 2), nullable=True)

    # Before/after quantities for audit
    quantity_before = Column(Numeric(10, 2), nullable=True)
    quantity_after = Column(Numeric(10, 2), nullable=True)

    # Links to source documents
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    intervention_id = Column(Integer, nullable=True)  # Link to interventions table

    # Metadata
    reference = Column(String(100), nullable=True)  # External reference
    notes = Column(Text, nullable=True)
    movement_date = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    article = relationship("StockArticle", back_populates="movements")
    location = relationship("StockLocation")
    purchase = relationship("Purchase", backref="stock_movements")
    invoice = relationship("Invoice", backref="stock_movements")
    created_by = relationship("User", backref="stock_movements")
