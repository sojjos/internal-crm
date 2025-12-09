"""Collaborator and payroll routes."""
from datetime import date, datetime
from typing import Any, List, Optional
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
import io

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.models.collaborator import Collaborator, ContractType, PayrollPeriod, Payslip
from app.models.expense import Expense
from app.schemas.collaborator import (
    CollaboratorCreate, CollaboratorUpdate, CollaboratorResponse,
    PayrollPeriodCreate, PayrollPeriodResponse,
    PayslipCreate, PayslipResponse,
    PayrollSummary
)
from app.services.export_service import export_payroll_to_excel

router = APIRouter()


# Collaborators
@router.get("/", response_model=List[CollaboratorResponse])
def get_collaborators(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    contract_type: Optional[ContractType] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all collaborators with optional filtering."""
    query = db.query(Collaborator)

    if search:
        query = query.filter(
            Collaborator.first_name.ilike(f"%{search}%") |
            Collaborator.last_name.ilike(f"%{search}%") |
            Collaborator.email.ilike(f"%{search}%")
        )

    if contract_type:
        query = query.filter(Collaborator.contract_type == contract_type)

    if is_active is not None:
        query = query.filter(Collaborator.is_active == is_active)

    collaborators = query.order_by(
        Collaborator.last_name, Collaborator.first_name
    ).offset(skip).limit(limit).all()
    return collaborators


@router.post("/", response_model=CollaboratorResponse, status_code=status.HTTP_201_CREATED)
def create_collaborator(
    collaborator_in: CollaboratorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new collaborator, optionally with a user account."""
    # Extract user creation fields
    create_user = collaborator_in.create_user_account
    user_password = collaborator_in.user_password

    # Prepare collaborator data (exclude user-related fields)
    collab_data = collaborator_in.model_dump(exclude={'create_user_account', 'user_password'})

    user_id = None

    # Create user account if requested
    if create_user and collaborator_in.email:
        # Check if user with this email already exists
        existing_user = db.query(User).filter(User.email == collaborator_in.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un utilisateur avec cet email existe déjà"
            )

        # Create user
        password = user_password or "changeme123"  # Default password if not provided
        new_user = User(
            email=collaborator_in.email,
            hashed_password=get_password_hash(password),
            first_name=collaborator_in.first_name,
            last_name=collaborator_in.last_name,
            phone=collaborator_in.phone,
            is_active=True
        )
        db.add(new_user)
        db.flush()  # Get the user ID
        user_id = new_user.id

    # Create collaborator
    collaborator = Collaborator(**collab_data, user_id=user_id)
    db.add(collaborator)
    db.commit()
    db.refresh(collaborator)
    return collaborator


@router.get("/{collaborator_id}", response_model=CollaboratorResponse)
def get_collaborator(
    collaborator_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a specific collaborator."""
    collaborator = db.query(Collaborator).filter(
        Collaborator.id == collaborator_id
    ).first()
    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborator not found"
        )
    return collaborator


@router.put("/{collaborator_id}", response_model=CollaboratorResponse)
def update_collaborator(
    collaborator_id: int,
    collaborator_in: CollaboratorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a collaborator."""
    collaborator = db.query(Collaborator).filter(
        Collaborator.id == collaborator_id
    ).first()
    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborator not found"
        )

    update_data = collaborator_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(collaborator, field, value)

    db.commit()
    db.refresh(collaborator)
    return collaborator


@router.delete("/{collaborator_id}")
def delete_collaborator(
    collaborator_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Deactivate a collaborator."""
    collaborator = db.query(Collaborator).filter(
        Collaborator.id == collaborator_id
    ).first()
    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborator not found"
        )

    collaborator.is_active = False
    db.commit()

    return {"message": "Collaborator deactivated"}


# Payroll Periods
@router.get("/payroll/periods", response_model=List[PayrollPeriodResponse])
def get_payroll_periods(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all payroll periods."""
    query = db.query(PayrollPeriod)
    if year:
        query = query.filter(PayrollPeriod.year == year)
    return query.order_by(PayrollPeriod.period.desc()).all()


@router.post("/payroll/periods", response_model=PayrollPeriodResponse, status_code=status.HTTP_201_CREATED)
def create_payroll_period(
    period_in: PayrollPeriodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new payroll period."""
    existing = db.query(PayrollPeriod).filter(
        PayrollPeriod.period == period_in.period
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payroll period already exists"
        )

    period = PayrollPeriod(**period_in.model_dump())
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


@router.get("/payroll/periods/{period}/summary", response_model=List[PayrollSummary])
def get_payroll_summary(
    period: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get payroll summary for a period."""
    # Get active collaborators
    collaborators = db.query(Collaborator).filter(
        Collaborator.is_active == True
    ).all()

    summaries = []
    for collab in collaborators:
        # Get total expenses for this period
        total_expenses = db.query(func.sum(Expense.amount_tvac)).filter(
            Expense.collaborator_id == collab.id,
            Expense.payroll_period == period,
            Expense.is_validated == True
        ).scalar() or 0.0

        summary = PayrollSummary(
            collaborator_id=collab.id,
            collaborator_name=collab.full_name,
            contract_type=collab.contract_type,
            gross_salary=collab.gross_salary,
            total_expenses=float(total_expenses),
            bonus=0.0,  # Can be set manually
            total_to_pay=float(total_expenses)  # Simplified
        )
        summaries.append(summary)

    return summaries


@router.get("/payroll/periods/{period}/export")
def export_payroll(
    period: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Export payroll data to Excel."""
    # Get expenses for this period
    expenses = db.query(Expense).options(
        joinedload(Expense.collaborator),
        joinedload(Expense.expense_type)
    ).filter(
        Expense.payroll_period == period
    ).all()

    # Generate Excel
    excel_buffer = export_payroll_to_excel(expenses, period)

    return StreamingResponse(
        io.BytesIO(excel_buffer),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=payroll_{period}.xlsx"
        }
    )


# Payslips
@router.get("/{collaborator_id}/payslips", response_model=List[PayslipResponse])
def get_payslips(
    collaborator_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get payslips for a collaborator."""
    payslips = db.query(Payslip).filter(
        Payslip.collaborator_id == collaborator_id
    ).order_by(Payslip.period.desc()).all()
    return payslips


@router.post("/{collaborator_id}/payslips")
async def upload_payslip(
    collaborator_id: int,
    period: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Upload a payslip for a collaborator."""
    collaborator = db.query(Collaborator).filter(
        Collaborator.id == collaborator_id
    ).first()
    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborator not found"
        )

    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    # Create upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, "payslips", str(collaborator_id))
    os.makedirs(upload_dir, exist_ok=True)

    # Generate filename
    filename = f"payslip_{period}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(upload_dir, filename)

    # Save file
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Create payslip record
    payslip = Payslip(
        collaborator_id=collaborator_id,
        period=period,
        file_path=filepath,
        file_name=file.filename or filename,
        uploaded_by_id=current_user.id
    )
    db.add(payslip)
    db.commit()
    db.refresh(payslip)

    return PayslipResponse.model_validate(payslip)
