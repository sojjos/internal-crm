"""Invoice and invoice line models."""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float,
    Enum, ForeignKey, Date
)
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base


class InvoiceStatus(str, enum.Enum):
    """Invoice status."""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Invoice(Base):
    """Invoice model."""

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    # Invoice identification
    invoice_number = Column(String(50), unique=True, index=True, nullable=False)

    # Client
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    client = relationship("Client", backref="invoices")

    # Dates
    invoice_date = Column(Date, default=date.today, nullable=False)
    due_date = Column(Date, nullable=False)

    # Status
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)

    # Totals (calculated from lines)
    total_htva = Column(Float, default=0.0)  # Total excluding VAT
    total_vat = Column(Float, default=0.0)  # Total VAT amount
    total_tvac = Column(Float, default=0.0)  # Total including VAT

    # Payment tracking
    payment_date = Column(Date, nullable=True)
    payment_reference = Column(String(255), nullable=True)  # PayPal transaction ID, etc.

    # File paths
    pdf_path = Column(String(500), nullable=True)
    ubl_path = Column(String(500), nullable=True)  # UBL/Peppol XML file

    # Sending tracking
    sent_via_email = Column(Boolean, default=False)
    sent_via_peppol = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    peppol_sent_at = Column(DateTime, nullable=True)

    # PayPal
    paypal_payment_link = Column(String(500), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)  # Internal notes
    footer_notes = Column(Text, nullable=True)  # Notes to appear on invoice

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice {self.invoice_number}>"

    def calculate_totals(self):
        """Recalculate totals from lines."""
        self.total_htva = sum(line.line_total_htva for line in self.lines)
        self.total_vat = sum(line.line_total_vat for line in self.lines)
        self.total_tvac = sum(line.line_total_tvac for line in self.lines)

    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if self.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
            return False
        return date.today() > self.due_date


class InvoiceLine(Base):
    """Invoice line item."""

    __tablename__ = "invoice_lines"

    id = Column(Integer, primary_key=True, index=True)

    # Parent invoice
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    invoice = relationship("Invoice", back_populates="lines")

    # Line order
    line_number = Column(Integer, default=1)

    # Article reference (optional - allows free lines)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)
    article = relationship("Article")

    # Line details
    description = Column(Text, nullable=False)
    unit = Column(String(20), default="u")  # h, j, km, u, forfait
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, nullable=False)  # HTVA

    # Discount
    discount_percent = Column(Float, default=0.0)

    # VAT
    vat_rate = Column(Float, default=21.0)

    # Calculated totals
    line_total_htva = Column(Float, default=0.0)
    line_total_vat = Column(Float, default=0.0)
    line_total_tvac = Column(Float, default=0.0)

    def __repr__(self):
        return f"<InvoiceLine {self.line_number}: {self.description[:30]}>"

    def calculate_totals(self):
        """Calculate line totals."""
        subtotal = self.quantity * self.unit_price
        if self.discount_percent > 0:
            subtotal = subtotal * (1 - self.discount_percent / 100)
        self.line_total_htva = round(subtotal, 2)
        self.line_total_vat = round(self.line_total_htva * self.vat_rate / 100, 2)
        self.line_total_tvac = round(self.line_total_htva + self.line_total_vat, 2)
