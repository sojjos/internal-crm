"""Treasury and cashflow schemas."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel

from app.models.treasury import TransactionType, TransactionCategory, TransactionStatus


class BankAccountBase(BaseModel):
    name: str
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    initial_balance: Decimal = Decimal("0")
    is_default: bool = False
    color: str = "#3B82F6"


class BankAccountCreate(BankAccountBase):
    pass


class BankAccountUpdate(BaseModel):
    name: Optional[str] = None
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    initial_balance: Optional[Decimal] = None
    is_default: Optional[bool] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


class BankAccountResponse(BankAccountBase):
    id: int
    current_balance: Decimal
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CashFlowTransactionBase(BaseModel):
    description: str
    transaction_type: TransactionType
    category: TransactionCategory = TransactionCategory.AUTRE
    amount: Decimal
    expected_date: date
    bank_account_id: Optional[int] = None
    notes: Optional[str] = None


class CashFlowTransactionCreate(CashFlowTransactionBase):
    invoice_id: Optional[int] = None
    purchase_id: Optional[int] = None
    contract_id: Optional[int] = None
    expense_id: Optional[int] = None
    collaborator_id: Optional[int] = None
    is_recurring: bool = False


class CashFlowTransactionUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[TransactionCategory] = None
    status: Optional[TransactionStatus] = None
    amount: Optional[Decimal] = None
    expected_date: Optional[date] = None
    actual_date: Optional[date] = None
    bank_account_id: Optional[int] = None
    notes: Optional[str] = None


class CashFlowTransactionResponse(CashFlowTransactionBase):
    id: int
    status: TransactionStatus
    actual_date: Optional[date]
    invoice_id: Optional[int]
    purchase_id: Optional[int]
    contract_id: Optional[int]
    expense_id: Optional[int]
    collaborator_id: Optional[int]
    is_recurring: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CashFlowForecast(BaseModel):
    """Cash flow forecast for a period."""
    start_date: date
    end_date: date
    opening_balance: Decimal
    total_inflows: Decimal
    total_outflows: Decimal
    closing_balance: Decimal
    transactions: List[CashFlowTransactionResponse]


class WeeklyCashFlow(BaseModel):
    """Weekly cash flow summary."""
    week_start: date
    week_end: date
    inflows: Decimal
    outflows: Decimal
    net: Decimal
    balance: Decimal
