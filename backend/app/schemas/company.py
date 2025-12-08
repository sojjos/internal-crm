"""Company settings schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class CompanySettingsBase(BaseModel):
    """Base company settings schema."""
    company_name: str
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = "Belgique"
    vat_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class CompanySettingsCreate(CompanySettingsBase):
    """Schema for creating company settings."""
    pass


class CompanySettingsUpdate(BaseModel):
    """Schema for updating company settings."""
    company_name: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
    vat_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    # VAT settings
    vat_rates: Optional[List[float]] = None
    default_vat_rate: Optional[float] = None

    # Invoice settings
    invoice_number_format: Optional[str] = None
    default_payment_terms: Optional[int] = None

    # Peppol settings
    peppol_enabled: Optional[bool] = None
    peppol_participant_id: Optional[str] = None

    # PayPal settings
    paypal_enabled: Optional[bool] = None
    paypal_mode: Optional[str] = None
    paypal_client_id: Optional[str] = None
    paypal_client_secret: Optional[str] = None

    # Other settings
    default_currency: Optional[str] = None
    legal_mentions: Optional[str] = None
    general_terms: Optional[str] = None

    # SMTP settings
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_tls: Optional[bool] = None


class CompanySettingsResponse(CompanySettingsBase):
    """Schema for company settings response."""
    id: int
    vat_rates: List[float]
    default_vat_rate: float
    invoice_number_format: str
    invoice_next_number: int
    default_payment_terms: int
    peppol_enabled: bool
    peppol_participant_id: Optional[str] = None
    paypal_enabled: bool
    paypal_mode: str
    default_currency: str
    legal_mentions: Optional[str] = None
    general_terms: Optional[str] = None
    logo_path: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int
    smtp_from_email: Optional[str] = None
    smtp_tls: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
