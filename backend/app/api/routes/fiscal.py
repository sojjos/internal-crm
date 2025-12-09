"""Fiscal module API routes for Belgian ISoc and tax declarations."""
from datetime import date, datetime
from typing import Any, List, Optional
import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.fiscal import (
    TaxDeclaration, ISocCalculation, TaxDeclarationItem, TaxMapping, Prepayment,
    TaxDeclarationStatus, TaxDeclarationType, BiztaxStatus,
    ISOC_FORM_STRUCTURE, DNA_CATEGORIES, PREPAYMENT_BONUS_RATES
)
from app.models.annual_accounts import FiscalYear

router = APIRouter()


# Pydantic schemas
class TaxDeclarationCreate(BaseModel):
    fiscal_year_id: int
    declaration_type: TaxDeclarationType
    period_start: date
    period_end: date
    enterprise_number: str
    company_name: Optional[str] = None


class TaxDeclarationResponse(BaseModel):
    id: int
    fiscal_year_id: int
    reference: str
    declaration_type: TaxDeclarationType
    status: TaxDeclarationStatus
    period_start: date
    period_end: date
    due_date: Optional[date]
    enterprise_number: str
    company_name: Optional[str]
    biztax_status: BiztaxStatus
    biztax_submission_date: Optional[datetime]
    biztax_reference: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ISocCalculationResponse(BaseModel):
    id: int
    declaration_id: int
    accounting_result: float
    dna_total: float
    deduction_rdt: float
    deduction_innovation: float
    deduction_investment: float
    other_deductions: float
    carried_forward_losses: float
    losses_used: float
    taxable_base: float
    standard_rate: float
    sme_rate: float
    sme_threshold: float
    tax_at_standard_rate: float
    tax_at_sme_rate: float
    total_tax: float
    prepayments_q1: float
    prepayments_q2: float
    prepayments_q3: float
    prepayments_q4: float
    total_prepayments: float
    prepayment_bonus: float
    tax_balance: float
    is_sme: bool

    class Config:
        from_attributes = True


class ISocCalculationUpdate(BaseModel):
    accounting_result: Optional[float] = None
    dna_total: Optional[float] = None
    dna_details: Optional[dict] = None
    deduction_rdt: Optional[float] = None
    deduction_innovation: Optional[float] = None
    deduction_investment: Optional[float] = None
    other_deductions: Optional[float] = None
    carried_forward_losses: Optional[float] = None
    losses_used: Optional[float] = None
    is_sme: Optional[bool] = None


class PrepaymentCreate(BaseModel):
    fiscal_year_id: int
    quarter: int
    due_date: date
    estimated_tax: Optional[float] = 0.0


class PrepaymentUpdate(BaseModel):
    payment_date: Optional[date] = None
    amount_paid: Optional[float] = None
    payment_reference: Optional[str] = None
    is_paid: Optional[bool] = None


class PrepaymentResponse(BaseModel):
    id: int
    fiscal_year_id: int
    quarter: int
    reference: Optional[str]
    due_date: date
    payment_date: Optional[date]
    estimated_tax: float
    amount_paid: float
    bonus_rate: float
    bonus_amount: float
    is_paid: bool

    class Config:
        from_attributes = True


class TaxMappingCreate(BaseModel):
    pcmn_account: str
    pcmn_label: Optional[str] = None
    declaration_type: TaxDeclarationType
    tax_code: str
    tax_label: Optional[str] = None
    coefficient: float = 1.0
    is_deductible: bool = True
    dna_percentage: float = 0.0


class TaxMappingResponse(BaseModel):
    id: int
    pcmn_account: str
    pcmn_label: Optional[str]
    declaration_type: TaxDeclarationType
    tax_code: str
    tax_label: Optional[str]
    coefficient: float
    is_deductible: bool
    dna_percentage: float
    is_active: bool

    class Config:
        from_attributes = True


# Tax Declaration endpoints
@router.get("/declarations", response_model=List[TaxDeclarationResponse])
def list_declarations(
    fiscal_year_id: Optional[int] = None,
    declaration_type: Optional[TaxDeclarationType] = None,
    status: Optional[TaxDeclarationStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List tax declarations."""
    query = db.query(TaxDeclaration)

    if fiscal_year_id:
        query = query.filter(TaxDeclaration.fiscal_year_id == fiscal_year_id)
    if declaration_type:
        query = query.filter(TaxDeclaration.declaration_type == declaration_type)
    if status:
        query = query.filter(TaxDeclaration.status == status)

    return query.order_by(TaxDeclaration.created_at.desc()).all()


@router.post("/declarations", response_model=TaxDeclarationResponse)
def create_declaration(
    decl_in: TaxDeclarationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new tax declaration."""
    # Verify fiscal year
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.id == decl_in.fiscal_year_id
    ).first()
    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    # Generate reference
    count = db.query(TaxDeclaration).filter(
        TaxDeclaration.fiscal_year_id == decl_in.fiscal_year_id,
        TaxDeclaration.declaration_type == decl_in.declaration_type
    ).count()
    reference = f"{decl_in.declaration_type.value}-{fiscal_year.name}-{count + 1:03d}"

    # Calculate due date based on declaration type
    due_date = None
    if decl_in.declaration_type == TaxDeclarationType.ISOC:
        # ISoc due date: 7 months after fiscal year end
        due_date = date(
            decl_in.period_end.year if decl_in.period_end.month <= 5 else decl_in.period_end.year + 1,
            (decl_in.period_end.month + 7 - 1) % 12 + 1,
            decl_in.period_end.day
        )

    declaration = TaxDeclaration(
        **decl_in.model_dump(),
        reference=reference,
        due_date=due_date
    )
    db.add(declaration)
    db.commit()
    db.refresh(declaration)

    # Create ISoc calculation if type is ISOC
    if decl_in.declaration_type == TaxDeclarationType.ISOC:
        isoc_calc = ISocCalculation(declaration_id=declaration.id)
        db.add(isoc_calc)

        # Initialize form items
        _initialize_isoc_items(db, declaration.id)

    db.commit()
    return declaration


@router.get("/declarations/{decl_id}", response_model=TaxDeclarationResponse)
def get_declaration(
    decl_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a tax declaration by ID."""
    decl = db.query(TaxDeclaration).filter(TaxDeclaration.id == decl_id).first()
    if not decl:
        raise HTTPException(status_code=404, detail="Tax declaration not found")
    return decl


@router.delete("/declarations/{decl_id}")
def delete_declaration(
    decl_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete a tax declaration."""
    decl = db.query(TaxDeclaration).filter(TaxDeclaration.id == decl_id).first()
    if not decl:
        raise HTTPException(status_code=404, detail="Tax declaration not found")

    if decl.status not in [TaxDeclarationStatus.DRAFT, TaxDeclarationStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a validated or submitted declaration"
        )

    db.delete(decl)
    db.commit()
    return {"message": "Declaration deleted"}


# ISoc Calculation endpoints
@router.get("/declarations/{decl_id}/isoc", response_model=ISocCalculationResponse)
def get_isoc_calculation(
    decl_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get ISoc calculation for a declaration."""
    decl = db.query(TaxDeclaration).filter(TaxDeclaration.id == decl_id).first()
    if not decl:
        raise HTTPException(status_code=404, detail="Tax declaration not found")

    if decl.declaration_type != TaxDeclarationType.ISOC:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This declaration is not an ISoc declaration"
        )

    isoc = db.query(ISocCalculation).filter(
        ISocCalculation.declaration_id == decl_id
    ).first()
    if not isoc:
        raise HTTPException(status_code=404, detail="ISoc calculation not found")

    return isoc


@router.put("/declarations/{decl_id}/isoc", response_model=ISocCalculationResponse)
def update_isoc_calculation(
    decl_id: int,
    isoc_in: ISocCalculationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update ISoc calculation."""
    isoc = db.query(ISocCalculation).filter(
        ISocCalculation.declaration_id == decl_id
    ).first()
    if not isoc:
        raise HTTPException(status_code=404, detail="ISoc calculation not found")

    update_data = isoc_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(isoc, field, value)

    db.commit()
    db.refresh(isoc)
    return isoc


@router.post("/declarations/{decl_id}/isoc/calculate")
def calculate_isoc(
    decl_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Calculate ISoc tax based on current values."""
    isoc = db.query(ISocCalculation).filter(
        ISocCalculation.declaration_id == decl_id
    ).first()
    if not isoc:
        raise HTTPException(status_code=404, detail="ISoc calculation not found")

    # Calculate taxable base
    taxable_base = (
        isoc.accounting_result +
        isoc.dna_total -
        isoc.deduction_rdt -
        isoc.deduction_innovation -
        isoc.deduction_investment -
        isoc.other_deductions -
        isoc.losses_used
    )
    isoc.taxable_base = max(0, taxable_base)

    # Calculate tax
    isoc.calculate_tax()

    # Calculate prepayment bonus
    prepayment_bonus = 0
    prepayments = db.query(Prepayment).filter(
        Prepayment.fiscal_year_id == db.query(TaxDeclaration).filter(
            TaxDeclaration.id == decl_id
        ).first().fiscal_year_id,
        Prepayment.is_paid == True
    ).all()

    for prep in prepayments:
        bonus_rate = PREPAYMENT_BONUS_RATES.get(prep.quarter, 0)
        prep.bonus_rate = bonus_rate
        prep.bonus_amount = prep.amount_paid * (bonus_rate / 100)
        prepayment_bonus += prep.bonus_amount

    isoc.prepayment_bonus = prepayment_bonus
    isoc.tax_balance = isoc.total_tax - isoc.total_prepayments - isoc.prepayment_bonus
    isoc.calculated_at = datetime.utcnow()

    db.commit()
    db.refresh(isoc)

    # Update declaration status
    decl = db.query(TaxDeclaration).filter(TaxDeclaration.id == decl_id).first()
    decl.status = TaxDeclarationStatus.CALCULATED
    db.commit()

    return {
        "taxable_base": isoc.taxable_base,
        "tax_at_sme_rate": isoc.tax_at_sme_rate,
        "tax_at_standard_rate": isoc.tax_at_standard_rate,
        "total_tax": isoc.total_tax,
        "prepayment_bonus": isoc.prepayment_bonus,
        "tax_balance": isoc.tax_balance,
        "message": "ISoc calculated successfully"
    }


@router.get("/declarations/{decl_id}/items")
def get_declaration_items(
    decl_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get declaration form items."""
    items = db.query(TaxDeclarationItem).filter(
        TaxDeclarationItem.declaration_id == decl_id
    ).order_by(TaxDeclarationItem.display_order).all()
    return items


@router.post("/declarations/{decl_id}/biztax/submit")
def submit_to_biztax(
    decl_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Submit declaration to Biztax (simulated)."""
    decl = db.query(TaxDeclaration).filter(TaxDeclaration.id == decl_id).first()
    if not decl:
        raise HTTPException(status_code=404, detail="Tax declaration not found")

    if decl.status not in [TaxDeclarationStatus.CALCULATED, TaxDeclarationStatus.VALIDATED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Declaration must be calculated before submission"
        )

    # Simulate Biztax submission
    decl.biztax_status = BiztaxStatus.SUBMITTED
    decl.biztax_submission_date = datetime.utcnow()
    decl.biztax_reference = f"BTX-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    decl.status = TaxDeclarationStatus.SUBMITTED
    decl.submitted_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Declaration submitted to Biztax",
        "biztax_reference": decl.biztax_reference,
        "submission_date": decl.biztax_submission_date.isoformat()
    }


# Prepayment endpoints
@router.get("/prepayments", response_model=List[PrepaymentResponse])
def list_prepayments(
    fiscal_year_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List tax prepayments."""
    query = db.query(Prepayment)
    if fiscal_year_id:
        query = query.filter(Prepayment.fiscal_year_id == fiscal_year_id)
    return query.order_by(Prepayment.due_date).all()


@router.post("/prepayments", response_model=PrepaymentResponse)
def create_prepayment(
    prep_in: PrepaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new prepayment."""
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.id == prep_in.fiscal_year_id
    ).first()
    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    if prep_in.quarter not in [1, 2, 3, 4]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quarter must be 1, 2, 3, or 4"
        )

    reference = f"VA-{fiscal_year.name}-Q{prep_in.quarter}"

    prepayment = Prepayment(
        **prep_in.model_dump(),
        reference=reference,
        bonus_rate=PREPAYMENT_BONUS_RATES.get(prep_in.quarter, 0)
    )
    db.add(prepayment)
    db.commit()
    db.refresh(prepayment)
    return prepayment


@router.put("/prepayments/{prep_id}", response_model=PrepaymentResponse)
def update_prepayment(
    prep_id: int,
    prep_in: PrepaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a prepayment (record payment)."""
    prepayment = db.query(Prepayment).filter(Prepayment.id == prep_id).first()
    if not prepayment:
        raise HTTPException(status_code=404, detail="Prepayment not found")

    update_data = prep_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prepayment, field, value)

    # Calculate bonus
    if prepayment.is_paid and prepayment.amount_paid > 0:
        prepayment.bonus_amount = prepayment.amount_paid * (prepayment.bonus_rate / 100)

    db.commit()
    db.refresh(prepayment)
    return prepayment


# Tax Mapping endpoints
@router.get("/mappings", response_model=List[TaxMappingResponse])
def list_mappings(
    declaration_type: Optional[TaxDeclarationType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List tax mappings."""
    query = db.query(TaxMapping).filter(TaxMapping.is_active == True)
    if declaration_type:
        query = query.filter(TaxMapping.declaration_type == declaration_type)
    return query.order_by(TaxMapping.pcmn_account).all()


@router.post("/mappings", response_model=TaxMappingResponse)
def create_mapping(
    mapping_in: TaxMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new tax mapping."""
    mapping = TaxMapping(**mapping_in.model_dump())
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping


@router.delete("/mappings/{mapping_id}")
def delete_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Deactivate a tax mapping."""
    mapping = db.query(TaxMapping).filter(TaxMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")

    mapping.is_active = False
    db.commit()
    return {"message": "Mapping deactivated"}


# Reference data
@router.get("/dna-categories")
def get_dna_categories(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get DNA (Non-Deductible Expenses) categories."""
    return DNA_CATEGORIES


@router.get("/isoc-structure")
def get_isoc_structure(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get ISoc form structure."""
    return ISOC_FORM_STRUCTURE


@router.get("/prepayment-rates")
def get_prepayment_rates(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get prepayment bonus rates."""
    return {
        "rates": PREPAYMENT_BONUS_RATES,
        "due_dates": {
            1: "10 avril",
            2: "10 juillet",
            3: "10 octobre",
            4: "20 decembre"
        }
    }


# Helper functions
def _initialize_isoc_items(db: Session, declaration_id: int):
    """Initialize ISoc form items."""
    order = 0
    for section, items in ISOC_FORM_STRUCTURE.items():
        for code, label in items:
            item = TaxDeclarationItem(
                declaration_id=declaration_id,
                code=code,
                label=label,
                section=section,
                amount=0.0,
                display_order=order
            )
            db.add(item)
            order += 1
    db.commit()
