"""Expense schemas."""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class ExpenseTypeBase(BaseModel):
    """Base expense type schema."""
    name: str
    description: Optional[str] = None


class ExpenseTypeCreate(ExpenseTypeBase):
    """Schema for creating an expense type."""
    pass


class ExpenseTypeUpdate(BaseModel):
    """Schema for updating an expense type."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ExpenseTypeResponse(ExpenseTypeBase):
    """Schema for expense type response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpenseBase(BaseModel):
    """Base expense schema."""
    collaborator_id: int
    expense_date: date
    expense_type_id: int
    description: Optional[str] = None
    amount_htva: float
    vat_amount: float = 0.0
    amount_tvac: float
    supplier_id: Optional[int] = None
    payroll_period: Optional[str] = None
    notes: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    """Schema for creating an expense."""
    pass


class ExpenseUpdate(BaseModel):
    """Schema for updating an expense."""
    collaborator_id: Optional[int] = None
    expense_date: Optional[date] = None
    expense_type_id: Optional[int] = None
    description: Optional[str] = None
    amount_htva: Optional[float] = None
    vat_amount: Optional[float] = None
    amount_tvac: Optional[float] = None
    supplier_id: Optional[int] = None
    payroll_period: Optional[str] = None
    notes: Optional[str] = None
    is_validated: Optional[bool] = None
    is_reimbursed: Optional[bool] = None


class ExpenseResponse(ExpenseBase):
    """Schema for expense response."""
    id: int
    receipt_path: Optional[str] = None
    is_validated: bool
    validated_at: Optional[datetime] = None
    is_reimbursed: bool
    reimbursed_at: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpenseWithDetails(ExpenseResponse):
    """Expense response with related details."""
    expense_type: ExpenseTypeResponse
    collaborator_name: Optional[str] = None
    supplier_name: Optional[str] = None

    class Config:
        from_attributes = True
