"""Client schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.models.client import SendMethod


class ClientBase(BaseModel):
    """Base client schema."""
    name: str
    contact_name: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = "Belgique"
    vat_number: Optional[str] = None
    is_business: bool = True
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_send_method: SendMethod = SendMethod.EMAIL
    peppol_id: Optional[str] = None
    custom_payment_terms: Optional[int] = None
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    """Schema for creating a client."""
    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client."""
    name: Optional[str] = None
    contact_name: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
    vat_number: Optional[str] = None
    is_business: Optional[bool] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_send_method: Optional[SendMethod] = None
    peppol_id: Optional[str] = None
    custom_payment_terms: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ClientResponse(ClientBase):
    """Schema for client response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
