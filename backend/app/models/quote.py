"""Quote (Devis) models."""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Boolean, Enum, Numeric
from sqlalchemy.orm import relationship

from app.db.database import Base


class QuoteStatus(str, PyEnum):
    """Quote status."""
    BROUILLON = "BROUILLON"      # Draft
    ENVOYE = "ENVOYE"            # Sent to client
    EN_ATTENTE = "EN_ATTENTE"    # Awaiting response
    ACCEPTE = "ACCEPTE"          # Accepted by client
    REFUSE = "REFUSE"            # Rejected by client
    EXPIRE = "EXPIRE"            # Expired (validity date passed)
    CONVERTI = "CONVERTI"        # Converted to invoice
    ANNULE = "ANNULE"            # Cancelled


class Quote(Base):
    """Quote / estimate model."""
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)

    # Quote number
    quote_number = Column(String(50), unique=True, nullable=False)

    # Client
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    client_contact_name = Column(String(100), nullable=True)
    client_email = Column(String(255), nullable=True)  # For sending quote

    # Dates
    quote_date = Column(Date, nullable=False, default=date.today)
    validity_date = Column(Date, nullable=True)  # Quote valid until
    expected_start_date = Column(Date, nullable=True)  # When work would start

    # Status
    status = Column(Enum(QuoteStatus), default=QuoteStatus.BROUILLON)
    accepted_at = Column(DateTime, nullable=True)
    accepted_by = Column(String(100), nullable=True)  # Name of person who accepted

    # Amounts (calculated from lines)
    total_htva = Column(Numeric(12, 2), default=0)
    total_vat = Column(Numeric(12, 2), default=0)
    total_tvac = Column(Numeric(12, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)

    # Content
    subject = Column(String(255), nullable=True)
    introduction = Column(Text, nullable=True)  # Intro text before lines
    terms = Column(Text, nullable=True)  # Terms and conditions
    notes = Column(Text, nullable=True)  # Internal notes

    # Payment terms (to copy to invoice)
    payment_terms_days = Column(Integer, default=30)

    # Conversion tracking
    converted_to_invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    converted_at = Column(DateTime, nullable=True)

    # PDF storage
    pdf_path = Column(String(500), nullable=True)
    pdf_generated_at = Column(DateTime, nullable=True)

    # Client interaction
    sent_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    validation_token = Column(String(100), nullable=True)  # For client validation link

    # Metadata
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", backref="quotes")
    converted_to_invoice = relationship("Invoice", backref="source_quote", foreign_keys=[converted_to_invoice_id])
    created_by = relationship("User", backref="created_quotes")
    lines = relationship("QuoteLine", back_populates="quote", cascade="all, delete-orphan")
    interventions = relationship("Intervention", backref="quote", foreign_keys="Intervention.quote_id")


class QuoteLine(Base):
    """Line item for a quote."""
    __tablename__ = "quote_lines"

    id = Column(Integer, primary_key=True, index=True)

    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    position = Column(Integer, default=0)  # Order of lines

    # Item details
    description = Column(String(500), nullable=False)
    long_description = Column(Text, nullable=True)  # Detailed description
    quantity = Column(Numeric(10, 2), default=1)
    unit = Column(String(20), default="unité")
    unit_price_htva = Column(Numeric(10, 2), nullable=False)
    vat_rate = Column(Numeric(5, 2), default=21.00)
    discount_percent = Column(Numeric(5, 2), default=0)

    # Link to catalog article
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)

    # Optional section/group
    section = Column(String(100), nullable=True)  # Group lines by section
    is_optional = Column(Boolean, default=False)  # Optional line (not included in total)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    quote = relationship("Quote", back_populates="lines")
    article = relationship("Article")

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
