"""Expense routes."""
from datetime import date, datetime
from typing import Any, List, Optional
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.expense import Expense, ExpenseType
from app.models.collaborator import Collaborator
from app.schemas.expense import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse,
    ExpenseTypeCreate, ExpenseTypeUpdate, ExpenseTypeResponse
)

router = APIRouter()


# Expense Types
@router.get("/types", response_model=List[ExpenseTypeResponse])
def get_expense_types(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all expense types."""
    query = db.query(ExpenseType)
    if is_active is not None:
        query = query.filter(ExpenseType.is_active == is_active)
    return query.order_by(ExpenseType.name).all()


@router.post("/types", response_model=ExpenseTypeResponse, status_code=status.HTTP_201_CREATED)
def create_expense_type(
    type_in: ExpenseTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new expense type."""
    existing = db.query(ExpenseType).filter(ExpenseType.name == type_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expense type already exists"
        )

    expense_type = ExpenseType(**type_in.model_dump())
    db.add(expense_type)
    db.commit()
    db.refresh(expense_type)
    return expense_type


@router.put("/types/{type_id}", response_model=ExpenseTypeResponse)
def update_expense_type(
    type_id: int,
    type_in: ExpenseTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update an expense type."""
    expense_type = db.query(ExpenseType).filter(ExpenseType.id == type_id).first()
    if not expense_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense type not found"
        )

    update_data = type_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense_type, field, value)

    db.commit()
    db.refresh(expense_type)
    return expense_type


# Expenses
@router.get("/", response_model=List[ExpenseResponse])
def get_expenses(
    skip: int = 0,
    limit: int = 100,
    collaborator_id: Optional[int] = None,
    expense_type_id: Optional[int] = None,
    payroll_period: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    is_validated: Optional[bool] = None,
    is_reimbursed: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all expenses with optional filtering."""
    query = db.query(Expense).options(
        joinedload(Expense.expense_type),
        joinedload(Expense.collaborator),
        joinedload(Expense.supplier)
    )

    if collaborator_id:
        query = query.filter(Expense.collaborator_id == collaborator_id)

    if expense_type_id:
        query = query.filter(Expense.expense_type_id == expense_type_id)

    if payroll_period:
        query = query.filter(Expense.payroll_period == payroll_period)

    if date_from:
        query = query.filter(Expense.expense_date >= date_from)

    if date_to:
        query = query.filter(Expense.expense_date <= date_to)

    if is_validated is not None:
        query = query.filter(Expense.is_validated == is_validated)

    if is_reimbursed is not None:
        query = query.filter(Expense.is_reimbursed == is_reimbursed)

    expenses = query.order_by(Expense.expense_date.desc()).offset(skip).limit(limit).all()
    return expenses


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense_in: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new expense."""
    # Verify collaborator exists
    collaborator = db.query(Collaborator).filter(
        Collaborator.id == expense_in.collaborator_id
    ).first()
    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborator not found"
        )

    # Verify expense type exists
    expense_type = db.query(ExpenseType).filter(
        ExpenseType.id == expense_in.expense_type_id
    ).first()
    if not expense_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense type not found"
        )

    expense = Expense(**expense_in.model_dump())
    expense.created_by_id = current_user.id
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a specific expense."""
    expense = db.query(Expense).options(
        joinedload(Expense.expense_type),
        joinedload(Expense.collaborator),
        joinedload(Expense.supplier)
    ).filter(Expense.id == expense_id).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    return expense


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_in: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update an expense."""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    update_data = expense_in.model_dump(exclude_unset=True)

    # Handle validation
    if "is_validated" in update_data and update_data["is_validated"]:
        update_data["validated_by_id"] = current_user.id
        update_data["validated_at"] = datetime.utcnow()

    # Handle reimbursement
    if "is_reimbursed" in update_data and update_data["is_reimbursed"]:
        update_data["reimbursed_at"] = date.today()

    for field, value in update_data.items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    return expense


@router.post("/{expense_id}/receipt")
async def upload_receipt(
    expense_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Upload receipt for an expense."""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    # Validate file type
    allowed_types = [
        "image/png", "image/jpeg", "image/jpg",
        "application/pdf"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed: PNG, JPEG, PDF"
        )

    # Create upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, "receipts")
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"receipt_{expense_id}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_dir, filename)

    # Save file
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Update expense
    expense.receipt_path = filepath
    db.commit()

    return {"receipt_path": filepath}


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete an expense."""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    if expense.is_reimbursed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a reimbursed expense"
        )

    db.delete(expense)
    db.commit()

    return {"message": "Expense deleted"}
