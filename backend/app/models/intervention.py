"""Intervention and planning models."""
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Time, ForeignKey, Boolean, Enum, Numeric
from sqlalchemy.orm import relationship

from app.db.database import Base


class InterventionStatus(str, PyEnum):
    """Intervention status."""
    PLANIFIEE = "PLANIFIEE"      # Scheduled
    EN_COURS = "EN_COURS"        # In progress
    TERMINEE = "TERMINEE"        # Completed
    FACTUREE = "FACTUREE"        # Invoiced
    ANNULEE = "ANNULEE"          # Cancelled


class InterventionType(str, PyEnum):
    """Type of intervention."""
    PRESTATION = "PRESTATION"
    MAINTENANCE = "MAINTENANCE"
    REPARATION = "REPARATION"
    INSTALLATION = "INSTALLATION"
    LIVRAISON = "LIVRAISON"
    CONSULTATION = "CONSULTATION"
    FORMATION = "FORMATION"
    AUTRE = "AUTRE"


class InterventionPriority(str, PyEnum):
    """Priority level."""
    BASSE = "BASSE"
    NORMALE = "NORMALE"
    HAUTE = "HAUTE"
    URGENTE = "URGENTE"


class Intervention(Base):
    """Intervention / service appointment model."""
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True)

    # Reference
    reference = Column(String(50), unique=True, nullable=True)

    # Client and location
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    address = Column(String(500), nullable=True)  # Override client address
    contact_name = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)

    # Planning
    scheduled_date = Column(Date, nullable=False)
    scheduled_start_time = Column(Time, nullable=True)
    scheduled_end_time = Column(Time, nullable=True)
    estimated_duration_minutes = Column(Integer, default=60)

    # Actual timing
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)

    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("collaborators.id"), nullable=True)

    # Details
    intervention_type = Column(Enum(InterventionType), default=InterventionType.PRESTATION)
    priority = Column(Enum(InterventionPriority), default=InterventionPriority.NORMALE)
    status = Column(Enum(InterventionStatus), default=InterventionStatus.PLANIFIEE)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)  # Not visible to client

    # Work done
    work_performed = Column(Text, nullable=True)
    client_signature = Column(Text, nullable=True)  # Base64 signature image

    # Linked equipment (if applicable)
    fixed_asset_id = Column(Integer, ForeignKey("fixed_assets.id"), nullable=True)

    # Billing
    is_billable = Column(Boolean, default=True)
    hourly_rate = Column(Numeric(10, 2), nullable=True)
    flat_rate = Column(Numeric(10, 2), nullable=True)
    travel_cost = Column(Numeric(10, 2), default=0)

    # Linked invoice (after billing)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)

    # Linked quote (if created from quote)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True)

    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(50), nullable=True)  # weekly, monthly, etc.
    recurrence_end_date = Column(Date, nullable=True)
    parent_intervention_id = Column(Integer, ForeignKey("interventions.id"), nullable=True)

    # Metadata
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", backref="interventions")
    assigned_to = relationship("Collaborator", backref="assigned_interventions")
    fixed_asset = relationship("FixedAsset", backref="interventions")
    invoice = relationship("Invoice", backref="source_interventions", foreign_keys=[invoice_id])
    created_by = relationship("User", backref="created_interventions")
    parent = relationship("Intervention", remote_side=[id], backref="recurring_instances")
    lines = relationship("InterventionLine", back_populates="intervention", cascade="all, delete-orphan")


class InterventionLine(Base):
    """Line item for an intervention (articles/services used)."""
    __tablename__ = "intervention_lines"

    id = Column(Integer, primary_key=True, index=True)

    intervention_id = Column(Integer, ForeignKey("interventions.id"), nullable=False)

    # Item details
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(10, 2), default=1)
    unit = Column(String(20), default="unité")
    unit_price_htva = Column(Numeric(10, 2), nullable=False)
    vat_rate = Column(Numeric(5, 2), default=21.00)
    discount_percent = Column(Numeric(5, 2), default=0)

    # Link to article (for stock deduction)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)
    stock_article_id = Column(Integer, ForeignKey("stock_articles.id"), nullable=True)

    # Stock movement tracking
    stock_deducted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    intervention = relationship("Intervention", back_populates="lines")
    article = relationship("Article")
    stock_article = relationship("StockArticle")

    @property
    def total_htva(self):
        """Calculate line total HTVA."""
        base = self.quantity * self.unit_price_htva
        discount = base * (self.discount_percent / 100)
        return base - discount

    @property
    def total_vat(self):
        """Calculate line VAT amount."""
        return self.total_htva * (self.vat_rate / 100)

    @property
    def total_tvac(self):
        """Calculate line total TVAC."""
        return self.total_htva + self.total_vat
