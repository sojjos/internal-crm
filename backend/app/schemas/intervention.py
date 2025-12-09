"""Intervention and planning schemas."""
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel

from app.models.intervention import InterventionStatus, InterventionType, InterventionPriority


class InterventionLineBase(BaseModel):
    description: str
    quantity: Decimal = Decimal("1")
    unit: str = "unite"
    unit_price_htva: Decimal
    vat_rate: Decimal = Decimal("21.00")
    discount_percent: Decimal = Decimal("0")
    article_id: Optional[int] = None
    stock_article_id: Optional[int] = None


class InterventionLineCreate(InterventionLineBase):
    pass


class InterventionLineResponse(InterventionLineBase):
    id: int
    intervention_id: int
    stock_deducted: bool
    total_htva: Decimal
    total_vat: Decimal
    total_tvac: Decimal

    class Config:
        from_attributes = True


class InterventionBase(BaseModel):
    client_id: int
    title: str
    scheduled_date: date
    scheduled_start_time: Optional[time] = None
    scheduled_end_time: Optional[time] = None
    estimated_duration_minutes: int = 60
    intervention_type: InterventionType = InterventionType.PRESTATION
    priority: InterventionPriority = InterventionPriority.NORMALE
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None
    internal_notes: Optional[str] = None
    assigned_to_id: Optional[int] = None
    fixed_asset_id: Optional[int] = None
    is_billable: bool = True
    hourly_rate: Optional[Decimal] = None
    flat_rate: Optional[Decimal] = None
    travel_cost: Decimal = Decimal("0")


class InterventionCreate(InterventionBase):
    lines: List[InterventionLineCreate] = []
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    recurrence_end_date: Optional[date] = None


class InterventionUpdate(BaseModel):
    client_id: Optional[int] = None
    title: Optional[str] = None
    scheduled_date: Optional[date] = None
    scheduled_start_time: Optional[time] = None
    scheduled_end_time: Optional[time] = None
    estimated_duration_minutes: Optional[int] = None
    intervention_type: Optional[InterventionType] = None
    priority: Optional[InterventionPriority] = None
    status: Optional[InterventionStatus] = None
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None
    internal_notes: Optional[str] = None
    work_performed: Optional[str] = None
    assigned_to_id: Optional[int] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    is_billable: Optional[bool] = None
    hourly_rate: Optional[Decimal] = None
    flat_rate: Optional[Decimal] = None
    travel_cost: Optional[Decimal] = None


class InterventionResponse(InterventionBase):
    id: int
    reference: Optional[str]
    status: InterventionStatus
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    work_performed: Optional[str]
    invoice_id: Optional[int]
    quote_id: Optional[int]
    is_recurring: bool
    created_at: datetime

    # Related names
    client_name: Optional[str] = None
    assigned_to_name: Optional[str] = None

    # Computed totals
    total_htva: Optional[Decimal] = None
    total_tvac: Optional[Decimal] = None

    lines: List[InterventionLineResponse] = []

    class Config:
        from_attributes = True


class CalendarEvent(BaseModel):
    """Simplified event for calendar display."""
    id: int
    title: str
    start: datetime
    end: datetime
    client_name: str
    status: InterventionStatus
    priority: InterventionPriority
    assigned_to_name: Optional[str]
    color: Optional[str] = None
