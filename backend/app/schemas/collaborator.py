"""Collaborator and payroll schemas."""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel

from app.models.collaborator import ContractType


class CollaboratorBase(BaseModel):
    """Base collaborator schema."""
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = "Belgique"
    contract_type: ContractType = ContractType.CDI
    manager_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gross_salary: Optional[float] = None
    hourly_rate: Optional[float] = None
    iban: Optional[str] = None
    notes: Optional[str] = None


class CollaboratorCreate(CollaboratorBase):
    """Schema for creating a collaborator."""
    pass


class CollaboratorUpdate(BaseModel):
    """Schema for updating a collaborator."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
    contract_type: Optional[ContractType] = None
    manager_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gross_salary: Optional[float] = None
    hourly_rate: Optional[float] = None
    iban: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CollaboratorResponse(CollaboratorBase):
    """Schema for collaborator response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PayrollPeriodCreate(BaseModel):
    """Schema for creating a payroll period."""
    period: str  # e.g., "2025-03"
    year: int
    month: int
    notes: Optional[str] = None


class PayrollPeriodResponse(BaseModel):
    """Schema for payroll period response."""
    id: int
    period: str
    year: int
    month: int
    is_closed: bool
    closed_at: Optional[datetime] = None
    exported_at: Optional[datetime] = None
    export_file_path: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PayslipCreate(BaseModel):
    """Schema for creating a payslip record."""
    collaborator_id: int
    period: str
    notes: Optional[str] = None


class PayslipResponse(BaseModel):
    """Schema for payslip response."""
    id: int
    collaborator_id: int
    period: str
    file_path: str
    file_name: str
    notes: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class PayrollSummary(BaseModel):
    """Summary for a collaborator in a payroll period."""
    collaborator_id: int
    collaborator_name: str
    contract_type: ContractType
    gross_salary: Optional[float] = None
    total_expenses: float = 0.0
    bonus: float = 0.0
    total_to_pay: float = 0.0
