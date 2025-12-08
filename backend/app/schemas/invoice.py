"""Invoice schemas."""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel

from app.models.invoice import InvoiceStatus


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    description: str
    unit: str = "u"
    quantity: float = 1.0
    unit_price: float
    discount_percent: float = 0.0
    vat_rate: float = 21.0
    article_id: Optional[int] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""
    pass


class InvoiceLineUpdate(BaseModel):
    """Schema for updating an invoice line."""
    description: Optional[str] = None
    unit: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    discount_percent: Optional[float] = None
    vat_rate: Optional[float] = None
    article_id: Optional[int] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""
    id: int
    invoice_id: int
    line_number: int
    line_total_htva: float
    line_total_vat: float
    line_total_tvac: float

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    client_id: int
    invoice_date: date
    due_date: date
    notes: Optional[str] = None
    footer_notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    lines: List[InvoiceLineCreate]


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""
    client_id: Optional[int] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[InvoiceStatus] = None
    notes: Optional[str] = None
    footer_notes: Optional[str] = None
    payment_date: Optional[date] = None
    payment_reference: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""
    id: int
    invoice_number: str
    status: InvoiceStatus
    total_htva: float
    total_vat: float
    total_tvac: float
    payment_date: Optional[date] = None
    payment_reference: Optional[str] = None
    pdf_path: Optional[str] = None
    ubl_path: Optional[str] = None
    sent_via_email: bool
    sent_via_peppol: bool
    email_sent_at: Optional[datetime] = None
    peppol_sent_at: Optional[datetime] = None
    paypal_payment_link: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []

    class Config:
        from_attributes = True


class InvoiceWithClient(InvoiceResponse):
    """Invoice response with client details."""
    from app.schemas.client import ClientResponse
    client: ClientResponse

    class Config:
        from_attributes = True
