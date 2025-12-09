"""Treasury and cashflow models."""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Boolean, Enum, Numeric
from sqlalchemy.orm import relationship

from app.db.database import Base


class TransactionType(str, PyEnum):
    """Cash flow transaction type."""
    ENCAISSEMENT = "ENCAISSEMENT"  # Money coming in
    DECAISSEMENT = "DECAISSEMENT"  # Money going out


class TransactionCategory(str, PyEnum):
    """Category of transaction."""
    FACTURE_CLIENT = "FACTURE_CLIENT"
    FACTURE_FOURNISSEUR = "FACTURE_FOURNISSEUR"
    SALAIRE = "SALAIRE"
    CHARGES_SOCIALES = "CHARGES_SOCIALES"
    LOYER = "LOYER"
    ABONNEMENT = "ABONNEMENT"
    LEASING = "LEASING"
    IMPOT = "IMPOT"
    TVA = "TVA"
    REMBOURSEMENT_FRAIS = "REMBOURSEMENT_FRAIS"
    INVESTISSEMENT = "INVESTISSEMENT"
    AUTRE = "AUTRE"


class TransactionStatus(str, PyEnum):
    """Status of transaction."""
    PREVUE = "PREVUE"        # Expected/planned
    CONFIRMEE = "CONFIRMEE"  # Confirmed to happen
    REALISEE = "REALISEE"    # Already happened


class BankAccount(Base):
    """Bank account for treasury management."""
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    bank_name = Column(String(100), nullable=True)
    iban = Column(String(34), nullable=True)
    bic = Column(String(11), nullable=True)
    initial_balance = Column(Numeric(12, 2), default=0)
    current_balance = Column(Numeric(12, 2), default=0)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    color = Column(String(7), default="#3B82F6")
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("CashFlowTransaction", back_populates="bank_account")


class CashFlowTransaction(Base):
    """Cash flow transaction (real or forecast)."""
    __tablename__ = "cashflow_transactions"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    description = Column(String(255), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    category = Column(Enum(TransactionCategory), default=TransactionCategory.AUTRE)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PREVUE)

    # Amount
    amount = Column(Numeric(12, 2), nullable=False)

    # Dates
    expected_date = Column(Date, nullable=False)  # When it's expected
    actual_date = Column(Date, nullable=True)     # When it actually happened

    # Bank account
    bank_account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=True)

    # Links to source entities
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=True)
    contract_id = Column(Integer, ForeignKey("purchase_contracts.id"), nullable=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True)
    collaborator_id = Column(Integer, ForeignKey("collaborators.id"), nullable=True)  # For salaries

    # Recurrence (for auto-generation)
    is_recurring = Column(Boolean, default=False)
    recurrence_source_id = Column(Integer, nullable=True)  # Link to original recurring transaction

    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bank_account = relationship("BankAccount", back_populates="transactions")
    invoice = relationship("Invoice", backref="cashflow_transactions")
    purchase = relationship("Purchase", backref="cashflow_transactions")
    contract = relationship("PurchaseContract", backref="cashflow_transactions")
    expense = relationship("Expense", backref="cashflow_transactions")
    collaborator = relationship("Collaborator", backref="salary_transactions")
