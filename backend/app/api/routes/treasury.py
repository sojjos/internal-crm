"""Treasury and cashflow routes."""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.treasury import (
    BankAccount, CashFlowTransaction, TransactionType, TransactionStatus, TransactionCategory
)
from app.models.invoice import Invoice, InvoiceStatus
from app.models.purchase import Purchase, PurchaseContract, PurchaseStatus
from app.models.expense import Expense
from app.schemas.treasury import (
    BankAccountCreate, BankAccountUpdate, BankAccountResponse,
    CashFlowTransactionCreate, CashFlowTransactionUpdate, CashFlowTransactionResponse,
    CashFlowForecast, WeeklyCashFlow
)

router = APIRouter()


# ============ Bank Accounts ============

@router.get("/accounts", response_model=List[BankAccountResponse])
def get_bank_accounts(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all bank accounts."""
    query = db.query(BankAccount)
    if is_active is not None:
        query = query.filter(BankAccount.is_active == is_active)
    return query.order_by(BankAccount.name).all()


@router.post("/accounts", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
def create_bank_account(
    account_in: BankAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new bank account."""
    account = BankAccount(**account_in.model_dump())
    account.current_balance = account.initial_balance
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.put("/accounts/{account_id}", response_model=BankAccountResponse)
def update_bank_account(
    account_id: int,
    account_in: BankAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a bank account."""
    account = db.query(BankAccount).filter(BankAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    for field, value in account_in.model_dump(exclude_unset=True).items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)
    return account


# ============ Transactions ============

@router.get("/transactions", response_model=List[CashFlowTransactionResponse])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    bank_account_id: Optional[int] = None,
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get cash flow transactions."""
    query = db.query(CashFlowTransaction)

    if bank_account_id:
        query = query.filter(CashFlowTransaction.bank_account_id == bank_account_id)
    if transaction_type:
        query = query.filter(CashFlowTransaction.transaction_type == transaction_type)
    if status:
        query = query.filter(CashFlowTransaction.status == status)
    if date_from:
        query = query.filter(CashFlowTransaction.expected_date >= date_from)
    if date_to:
        query = query.filter(CashFlowTransaction.expected_date <= date_to)

    return query.order_by(CashFlowTransaction.expected_date).offset(skip).limit(limit).all()


@router.post("/transactions", response_model=CashFlowTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_in: CashFlowTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a manual cash flow transaction."""
    transaction = CashFlowTransaction(**transaction_in.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.put("/transactions/{transaction_id}", response_model=CashFlowTransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_in: CashFlowTransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a transaction."""
    transaction = db.query(CashFlowTransaction).filter(
        CashFlowTransaction.id == transaction_id
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # If marking as realized, update bank balance
    update_data = transaction_in.model_dump(exclude_unset=True)
    if update_data.get("status") == TransactionStatus.REALISEE and transaction.bank_account_id:
        account = db.query(BankAccount).filter(
            BankAccount.id == transaction.bank_account_id
        ).first()
        if account:
            if transaction.transaction_type == TransactionType.ENCAISSEMENT:
                account.current_balance += transaction.amount
            else:
                account.current_balance -= transaction.amount

    for field, value in update_data.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete a transaction."""
    transaction = db.query(CashFlowTransaction).filter(
        CashFlowTransaction.id == transaction_id
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.status == TransactionStatus.REALISEE:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a realized transaction"
        )

    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted"}


# ============ Forecast ============

@router.get("/forecast")
def get_cashflow_forecast(
    start_date: date = Query(...),
    end_date: date = Query(...),
    bank_account_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get cash flow forecast for a period."""
    # Get opening balance
    if bank_account_id:
        account = db.query(BankAccount).filter(BankAccount.id == bank_account_id).first()
        opening_balance = Decimal(str(account.current_balance)) if account else Decimal("0")
    else:
        opening_balance = db.query(func.sum(BankAccount.current_balance)).filter(
            BankAccount.is_active == True
        ).scalar() or Decimal("0")

    # Get manual transactions
    query = db.query(CashFlowTransaction).filter(
        CashFlowTransaction.expected_date >= start_date,
        CashFlowTransaction.expected_date <= end_date
    )
    if bank_account_id:
        query = query.filter(CashFlowTransaction.bank_account_id == bank_account_id)

    manual_transactions = query.all()

    # Get expected receipts from unpaid invoices
    unpaid_invoices = db.query(Invoice).filter(
        Invoice.status == InvoiceStatus.SENT,
        Invoice.due_date >= start_date,
        Invoice.due_date <= end_date
    ).all()

    # Get expected payments from contracts
    active_contracts = db.query(PurchaseContract).filter(
        PurchaseContract.is_active == True
    ).all()

    # Build forecast
    transactions = []

    # Add manual transactions
    for t in manual_transactions:
        transactions.append({
            "id": t.id,
            "description": t.description,
            "transaction_type": t.transaction_type,
            "category": t.category,
            "amount": t.amount,
            "expected_date": t.expected_date,
            "status": t.status,
            "source": "manual"
        })

    # Add invoice receipts
    for inv in unpaid_invoices:
        transactions.append({
            "id": f"inv_{inv.id}",
            "description": f"Facture {inv.invoice_number} - {inv.client.name if inv.client else ''}",
            "transaction_type": TransactionType.ENCAISSEMENT,
            "category": TransactionCategory.FACTURE_CLIENT,
            "amount": inv.total_tvac,
            "expected_date": inv.due_date,
            "status": TransactionStatus.PREVUE,
            "source": "invoice",
            "invoice_id": inv.id
        })

    # Add contract payments
    for contract in active_contracts:
        # Simplified: add monthly payments
        current = start_date
        while current <= end_date:
            if current.day == contract.billing_day:
                transactions.append({
                    "id": f"contract_{contract.id}_{current}",
                    "description": f"{contract.name}",
                    "transaction_type": TransactionType.DECAISSEMENT,
                    "category": TransactionCategory.ABONNEMENT,
                    "amount": contract.amount_htva * (1 + contract.vat_rate / 100),
                    "expected_date": current,
                    "status": TransactionStatus.PREVUE,
                    "source": "contract",
                    "contract_id": contract.id
                })
            current += timedelta(days=1)

    # Sort by date
    transactions.sort(key=lambda x: x["expected_date"])

    # Calculate totals
    total_inflows = sum(
        t["amount"] for t in transactions
        if t["transaction_type"] == TransactionType.ENCAISSEMENT
    )
    total_outflows = sum(
        t["amount"] for t in transactions
        if t["transaction_type"] == TransactionType.DECAISSEMENT
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "opening_balance": float(opening_balance),
        "total_inflows": float(total_inflows),
        "total_outflows": float(total_outflows),
        "closing_balance": float(opening_balance + total_inflows - total_outflows),
        "transactions": transactions
    }


@router.get("/forecast/weekly", response_model=List[WeeklyCashFlow])
def get_weekly_forecast(
    weeks: int = Query(12, description="Number of weeks to forecast"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get weekly cash flow forecast."""
    today = date.today()
    # Start from beginning of current week (Monday)
    start = today - timedelta(days=today.weekday())

    # Get current balance
    current_balance = db.query(func.sum(BankAccount.current_balance)).filter(
        BankAccount.is_active == True
    ).scalar() or Decimal("0")

    result = []
    balance = Decimal(str(current_balance))

    for week in range(weeks):
        week_start = start + timedelta(weeks=week)
        week_end = week_start + timedelta(days=6)

        # Get forecast for this week
        forecast = get_cashflow_forecast(
            start_date=week_start,
            end_date=week_end,
            db=db,
            current_user=current_user
        )

        inflows = Decimal(str(forecast["total_inflows"]))
        outflows = Decimal(str(forecast["total_outflows"]))
        net = inflows - outflows
        balance = balance + net

        result.append(WeeklyCashFlow(
            week_start=week_start,
            week_end=week_end,
            inflows=inflows,
            outflows=outflows,
            net=net,
            balance=balance
        ))

    return result


@router.post("/sync-from-invoices")
def sync_transactions_from_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Sync expected receipts from unpaid invoices."""
    # Get unpaid invoices without existing transactions
    unpaid_invoices = db.query(Invoice).filter(
        Invoice.status == InvoiceStatus.SENT
    ).all()

    created = 0
    for invoice in unpaid_invoices:
        # Check if transaction already exists
        existing = db.query(CashFlowTransaction).filter(
            CashFlowTransaction.invoice_id == invoice.id
        ).first()

        if not existing and invoice.due_date:
            transaction = CashFlowTransaction(
                description=f"Facture {invoice.invoice_number}",
                transaction_type=TransactionType.ENCAISSEMENT,
                category=TransactionCategory.FACTURE_CLIENT,
                status=TransactionStatus.PREVUE,
                amount=invoice.total_tvac,
                expected_date=invoice.due_date,
                invoice_id=invoice.id
            )
            db.add(transaction)
            created += 1

    db.commit()
    return {"message": f"Created {created} transactions from invoices"}
