"""Expense and expense type models."""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float,
    ForeignKey, Date
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class ExpenseType(Base):
    """Expense type/category."""

    __tablename__ = "expense_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ExpenseType {self.name}>"


class Expense(Base):
    """Expense/note de frais model."""

    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)

    # Collaborator
    collaborator_id = Column(Integer, ForeignKey("collaborators.id"), nullable=False)
    collaborator = relationship("Collaborator", backref="expenses")

    # Expense details
    expense_date = Column(Date, nullable=False)
    expense_type_id = Column(Integer, ForeignKey("expense_types.id"), nullable=False)
    expense_type = relationship("ExpenseType")
    description = Column(Text, nullable=True)

    # Amounts
    amount_htva = Column(Float, nullable=False)  # Amount excluding VAT
    vat_amount = Column(Float, default=0.0)  # VAT amount
    amount_tvac = Column(Float, nullable=False)  # Total including VAT

    # Supplier (optional)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier = relationship("Supplier")

    # Payroll period (e.g., "2025-03")
    payroll_period = Column(String(7), nullable=True)

    # Receipt/justification
    receipt_path = Column(String(500), nullable=True)

    # Status
    is_validated = Column(Boolean, default=False)
    validated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)

    # Reimbursement tracking
    is_reimbursed = Column(Boolean, default=False)
    reimbursed_at = Column(Date, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Expense {self.id}: {self.amount_tvac} EUR>"
