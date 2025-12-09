"""Quote (Devis) schemas."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel

from app.models.quote import QuoteStatus


class QuoteLineBase(BaseModel):
    description: str
    long_description: Optional[str] = None
    quantity: Decimal = Decimal("1")
    unit: str = "unite"
    unit_price_htva: Decimal
    vat_rate: Decimal = Decimal("21.00")
    discount_percent: Decimal = Decimal("0")
    article_id: Optional[int] = None
    section: Optional[str] = None
    is_optional: bool = False


class QuoteLineCreate(QuoteLineBase):
    pass


class QuoteLineUpdate(BaseModel):
    description: Optional[str] = None
    long_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price_htva: Optional[Decimal] = None
    vat_rate: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = None
    article_id: Optional[int] = None
    section: Optional[str] = None
    is_optional: Optional[bool] = None
    position: Optional[int] = None


class QuoteLineResponse(QuoteLineBase):
    id: int
    quote_id: int
    position: int
    total_htva: Decimal
    total_vat: Decimal
    total_tvac: Decimal

    class Config:
        from_attributes = True


class QuoteBase(BaseModel):
    client_id: int
    quote_date: date
    validity_date: Optional[date] = None
    expected_start_date: Optional[date] = None
    subject: Optional[str] = None
    introduction: Optional[str] = None
    terms: Optional[str] = None
    notes: Optional[str] = None
    payment_terms_days: int = 30
    client_contact_name: Optional[str] = None
    client_email: Optional[str] = None


class QuoteCreate(QuoteBase):
    lines: List[QuoteLineCreate] = []


class QuoteUpdate(BaseModel):
    client_id: Optional[int] = None
    quote_date: Optional[date] = None
    validity_date: Optional[date] = None
    expected_start_date: Optional[date] = None
    status: Optional[QuoteStatus] = None
    subject: Optional[str] = None
    introduction: Optional[str] = None
    terms: Optional[str] = None
    notes: Optional[str] = None
    payment_terms_days: Optional[int] = None
    client_contact_name: Optional[str] = None
    client_email: Optional[str] = None
    discount_amount: Optional[Decimal] = None


class QuoteResponse(QuoteBase):
    id: int
    quote_number: str
    status: QuoteStatus
    total_htva: Decimal
    total_vat: Decimal
    total_tvac: Decimal
    discount_amount: Decimal
    accepted_at: Optional[datetime]
    accepted_by: Optional[str]
    sent_at: Optional[datetime]
    viewed_at: Optional[datetime]
    converted_to_invoice_id: Optional[int]
    converted_at: Optional[datetime]
    pdf_path: Optional[str]
    created_at: datetime

    # Related
    client_name: Optional[str] = None
    lines: List[QuoteLineResponse] = []

    class Config:
        from_attributes = True


class QuoteConvertRequest(BaseModel):
    """Request to convert quote to invoice."""
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    include_optional_lines: bool = False
