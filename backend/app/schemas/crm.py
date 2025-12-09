"""CRM and pipeline schemas."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel

from app.models.crm import (
    LeadSource, PipelineStage, ContactType, TaskPriority, TaskStatus
)


class ClientTagBase(BaseModel):
    name: str
    color: str = "#6B7280"
    description: Optional[str] = None


class ClientTagCreate(ClientTagBase):
    pass


class ClientTagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None


class ClientTagResponse(ClientTagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class OpportunityBase(BaseModel):
    name: str
    description: Optional[str] = None
    client_id: Optional[int] = None
    prospect_company: Optional[str] = None
    prospect_contact: Optional[str] = None
    prospect_email: Optional[str] = None
    prospect_phone: Optional[str] = None
    stage: PipelineStage = PipelineStage.PROSPECT
    source: Optional[LeadSource] = None
    probability: int = 10
    estimated_value: Optional[Decimal] = None
    estimated_close_date: Optional[date] = None
    assigned_to_id: Optional[int] = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    client_id: Optional[int] = None
    prospect_company: Optional[str] = None
    prospect_contact: Optional[str] = None
    prospect_email: Optional[str] = None
    prospect_phone: Optional[str] = None
    stage: Optional[PipelineStage] = None
    source: Optional[LeadSource] = None
    probability: Optional[int] = None
    estimated_value: Optional[Decimal] = None
    estimated_close_date: Optional[date] = None
    assigned_to_id: Optional[int] = None
    lost_reason: Optional[str] = None


class OpportunityResponse(OpportunityBase):
    id: int
    won_at: Optional[datetime]
    lost_at: Optional[datetime]
    lost_reason: Optional[str]
    quote_id: Optional[int]
    invoice_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    # Related
    client_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    weighted_value: Optional[Decimal] = None  # estimated_value * probability / 100

    class Config:
        from_attributes = True


class ContactActivityBase(BaseModel):
    activity_type: ContactType = ContactType.AUTRE
    subject: str
    description: Optional[str] = None
    activity_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    client_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    contact_name: Optional[str] = None


class ContactActivityCreate(ContactActivityBase):
    pass


class ContactActivityResponse(ContactActivityBase):
    id: int
    email_id: Optional[int]
    created_by_id: Optional[int]
    created_at: datetime

    client_name: Optional[str] = None

    class Config:
        from_attributes = True


class CRMTaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMALE
    due_date: Optional[datetime] = None
    reminder_date: Optional[datetime] = None
    assigned_to_id: Optional[int] = None
    client_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    quote_id: Optional[int] = None
    invoice_id: Optional[int] = None


class CRMTaskCreate(CRMTaskBase):
    pass


class CRMTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    reminder_date: Optional[datetime] = None
    assigned_to_id: Optional[int] = None


class CRMTaskResponse(CRMTaskBase):
    id: int
    status: TaskStatus
    completed_at: Optional[datetime]
    completed_by_id: Optional[int]
    created_at: datetime

    # Related
    client_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    opportunity_name: Optional[str] = None

    class Config:
        from_attributes = True


class PipelineSummary(BaseModel):
    """Pipeline summary for dashboard."""
    stage: PipelineStage
    count: int
    total_value: Decimal
    weighted_value: Decimal


class CRMDashboard(BaseModel):
    """CRM dashboard data."""
    pipeline_summary: List[PipelineSummary]
    total_opportunities: int
    total_value: Decimal
    weighted_value: Decimal
    tasks_due_today: int
    tasks_overdue: int
    recent_activities: List[ContactActivityResponse]
