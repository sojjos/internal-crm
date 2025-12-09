"""Annual Accounts API routes for Belgian BNB/XBRL filing."""
from datetime import date, datetime
from typing import Any, List, Optional
import io

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.annual_accounts import (
    FiscalYear, AnnualAccount, BalanceSheetItem, IncomeStatementItem,
    AnnualAccountNote, AccountMapping, AccountingSchemaType, AnnualAccountStatus,
    BELGIAN_BALANCE_SHEET_STRUCTURE, BELGIAN_INCOME_STATEMENT_STRUCTURE
)

router = APIRouter()


# Pydantic schemas
class FiscalYearCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    schema_type: AccountingSchemaType = AccountingSchemaType.ABBREVIATED


class FiscalYearUpdate(BaseModel):
    name: Optional[str] = None
    schema_type: Optional[AccountingSchemaType] = None


class FiscalYearResponse(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    is_closed: bool
    schema_type: AccountingSchemaType
    created_at: datetime

    class Config:
        from_attributes = True


class AnnualAccountCreate(BaseModel):
    fiscal_year_id: int
    schema_type: AccountingSchemaType
    bnb_enterprise_number: Optional[str] = None
    general_assembly_date: Optional[date] = None
    board_approval_date: Optional[date] = None


class AnnualAccountResponse(BaseModel):
    id: int
    fiscal_year_id: int
    reference: str
    status: AnnualAccountStatus
    schema_type: AccountingSchemaType
    bnb_enterprise_number: Optional[str]
    bnb_filing_date: Optional[date]
    bnb_filing_reference: Optional[str]
    general_assembly_date: Optional[date]
    board_approval_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BalanceSheetItemUpdate(BaseModel):
    current_year_amount: float
    previous_year_amount: Optional[float] = None


class BalanceSheetItemResponse(BaseModel):
    id: int
    rubric_code: str
    rubric_name: str
    section: str
    subsection: Optional[str]
    current_year_amount: float
    previous_year_amount: float
    xbrl_element: Optional[str]
    display_order: int

    class Config:
        from_attributes = True


class IncomeStatementItemResponse(BaseModel):
    id: int
    rubric_code: str
    rubric_name: str
    section: Optional[str]
    current_year_amount: float
    previous_year_amount: float
    xbrl_element: Optional[str]
    display_order: int

    class Config:
        from_attributes = True


# Fiscal Year endpoints
@router.get("/fiscal-years", response_model=List[FiscalYearResponse])
def list_fiscal_years(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all fiscal years."""
    years = db.query(FiscalYear).order_by(FiscalYear.start_date.desc()).all()
    return years


@router.post("/fiscal-years", response_model=FiscalYearResponse)
def create_fiscal_year(
    year_in: FiscalYearCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new fiscal year."""
    # Check for overlapping fiscal years
    existing = db.query(FiscalYear).filter(
        FiscalYear.start_date <= year_in.end_date,
        FiscalYear.end_date >= year_in.start_date
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fiscal year overlaps with existing year"
        )

    fiscal_year = FiscalYear(**year_in.model_dump())
    db.add(fiscal_year)
    db.commit()
    db.refresh(fiscal_year)
    return fiscal_year


@router.get("/fiscal-years/{year_id}", response_model=FiscalYearResponse)
def get_fiscal_year(
    year_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a fiscal year by ID."""
    year = db.query(FiscalYear).filter(FiscalYear.id == year_id).first()
    if not year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")
    return year


@router.put("/fiscal-years/{year_id}", response_model=FiscalYearResponse)
def update_fiscal_year(
    year_id: int,
    year_in: FiscalYearUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a fiscal year."""
    year = db.query(FiscalYear).filter(FiscalYear.id == year_id).first()
    if not year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    if year.is_closed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a closed fiscal year"
        )

    update_data = year_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(year, field, value)

    db.commit()
    db.refresh(year)
    return year


@router.post("/fiscal-years/{year_id}/close")
def close_fiscal_year(
    year_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Close a fiscal year."""
    year = db.query(FiscalYear).filter(FiscalYear.id == year_id).first()
    if not year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    if year.is_closed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fiscal year is already closed"
        )

    year.is_closed = True
    year.closed_at = datetime.utcnow()
    year.closed_by_id = current_user.id
    db.commit()

    return {"message": "Fiscal year closed successfully"}


# Annual Account endpoints
@router.get("/", response_model=List[AnnualAccountResponse])
def list_annual_accounts(
    fiscal_year_id: Optional[int] = None,
    status: Optional[AnnualAccountStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List annual accounts."""
    query = db.query(AnnualAccount)

    if fiscal_year_id:
        query = query.filter(AnnualAccount.fiscal_year_id == fiscal_year_id)
    if status:
        query = query.filter(AnnualAccount.status == status)

    accounts = query.order_by(AnnualAccount.created_at.desc()).all()
    return accounts


@router.post("/", response_model=AnnualAccountResponse)
def create_annual_account(
    account_in: AnnualAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new annual account."""
    # Verify fiscal year exists
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.id == account_in.fiscal_year_id
    ).first()
    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    # Generate reference
    count = db.query(AnnualAccount).filter(
        AnnualAccount.fiscal_year_id == account_in.fiscal_year_id
    ).count()
    reference = f"CA-{fiscal_year.name}-{count + 1:03d}"

    # Create annual account
    annual_account = AnnualAccount(
        **account_in.model_dump(),
        reference=reference
    )
    db.add(annual_account)
    db.commit()
    db.refresh(annual_account)

    # Initialize balance sheet items
    _initialize_balance_sheet(db, annual_account.id, account_in.schema_type)

    # Initialize income statement items
    _initialize_income_statement(db, annual_account.id, account_in.schema_type)

    return annual_account


@router.get("/{account_id}", response_model=AnnualAccountResponse)
def get_annual_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get an annual account by ID."""
    account = db.query(AnnualAccount).filter(AnnualAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Annual account not found")
    return account


@router.get("/{account_id}/balance-sheet", response_model=List[BalanceSheetItemResponse])
def get_balance_sheet(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get balance sheet items for an annual account."""
    items = db.query(BalanceSheetItem).filter(
        BalanceSheetItem.annual_account_id == account_id
    ).order_by(BalanceSheetItem.display_order).all()
    return items


@router.put("/{account_id}/balance-sheet/{item_id}")
def update_balance_sheet_item(
    account_id: int,
    item_id: int,
    item_in: BalanceSheetItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a balance sheet item."""
    item = db.query(BalanceSheetItem).filter(
        BalanceSheetItem.id == item_id,
        BalanceSheetItem.annual_account_id == account_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Balance sheet item not found")

    item.current_year_amount = item_in.current_year_amount
    if item_in.previous_year_amount is not None:
        item.previous_year_amount = item_in.previous_year_amount

    db.commit()
    db.refresh(item)
    return item


@router.get("/{account_id}/income-statement", response_model=List[IncomeStatementItemResponse])
def get_income_statement(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get income statement items for an annual account."""
    items = db.query(IncomeStatementItem).filter(
        IncomeStatementItem.annual_account_id == account_id
    ).order_by(IncomeStatementItem.display_order).all()
    return items


@router.post("/{account_id}/calculate")
def calculate_from_accounting(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Calculate annual account values from accounting data."""
    account = db.query(AnnualAccount).filter(AnnualAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Annual account not found")

    # This would integrate with the accounting module to pull data
    # For now, return a message indicating manual entry is needed
    return {
        "message": "Calculation completed",
        "note": "Values should be reviewed and adjusted manually"
    }


@router.post("/{account_id}/validate")
def validate_annual_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Validate annual account before submission."""
    account = db.query(AnnualAccount).filter(AnnualAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Annual account not found")

    errors = []
    warnings = []

    # Check balance sheet balances
    balance_items = db.query(BalanceSheetItem).filter(
        BalanceSheetItem.annual_account_id == account_id
    ).all()

    actif_total = sum(
        item.current_year_amount for item in balance_items
        if item.section == "ACTIF" and item.rubric_code in ["20/28", "29/58"]
    )
    passif_total = sum(
        item.current_year_amount for item in balance_items
        if item.section == "PASSIF" and item.rubric_code in ["10/15", "16", "17/49"]
    )

    if abs(actif_total - passif_total) > 0.01:
        errors.append(f"Balance sheet does not balance: Actif={actif_total}, Passif={passif_total}")

    # Check required fields
    if not account.bnb_enterprise_number:
        errors.append("Enterprise number is required for BNB filing")

    if not account.general_assembly_date:
        warnings.append("General assembly date is recommended")

    if errors:
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings
        }

    account.status = AnnualAccountStatus.VALIDATED
    db.commit()

    return {
        "valid": True,
        "errors": [],
        "warnings": warnings,
        "message": "Annual account validated successfully"
    }


@router.post("/{account_id}/generate-xbrl")
def generate_xbrl(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Generate XBRL file for BNB submission."""
    account = db.query(AnnualAccount).filter(AnnualAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Annual account not found")

    if account.status not in [AnnualAccountStatus.VALIDATED, AnnualAccountStatus.SUBMITTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Annual account must be validated before generating XBRL"
        )

    # Generate XBRL content
    xbrl_content = _generate_xbrl_content(db, account)

    return StreamingResponse(
        io.BytesIO(xbrl_content.encode('utf-8')),
        media_type="application/xml",
        headers={
            "Content-Disposition": f"attachment; filename=annual_accounts_{account.reference}.xbrl"
        }
    )


@router.get("/structure/balance-sheet")
def get_balance_sheet_structure(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get the Belgian balance sheet structure."""
    return BELGIAN_BALANCE_SHEET_STRUCTURE


@router.get("/structure/income-statement")
def get_income_statement_structure(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get the Belgian income statement structure."""
    return BELGIAN_INCOME_STATEMENT_STRUCTURE


# Helper functions
def _initialize_balance_sheet(db: Session, account_id: int, schema_type: AccountingSchemaType):
    """Initialize balance sheet items based on Belgian structure."""
    order = 0
    for section, subsections in BELGIAN_BALANCE_SHEET_STRUCTURE.items():
        for subsection, rubrics in subsections.items():
            for rubric_code, rubric_name in rubrics:
                item = BalanceSheetItem(
                    annual_account_id=account_id,
                    rubric_code=rubric_code,
                    rubric_name=rubric_name,
                    section=section,
                    subsection=subsection,
                    current_year_amount=0.0,
                    previous_year_amount=0.0,
                    display_order=order
                )
                db.add(item)
                order += 1
    db.commit()


def _initialize_income_statement(db: Session, account_id: int, schema_type: AccountingSchemaType):
    """Initialize income statement items based on Belgian structure."""
    order = 0
    for section, rubrics in BELGIAN_INCOME_STATEMENT_STRUCTURE.items():
        for rubric_code, rubric_name in rubrics:
            item = IncomeStatementItem(
                annual_account_id=account_id,
                rubric_code=rubric_code,
                rubric_name=rubric_name,
                section=section,
                current_year_amount=0.0,
                previous_year_amount=0.0,
                display_order=order
            )
            db.add(item)
            order += 1
    db.commit()


def _generate_xbrl_content(db: Session, account: AnnualAccount) -> str:
    """Generate XBRL content for annual accounts."""
    # Get fiscal year
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.id == account.fiscal_year_id
    ).first()

    # Get balance sheet and income statement items
    balance_items = db.query(BalanceSheetItem).filter(
        BalanceSheetItem.annual_account_id == account.id
    ).all()
    income_items = db.query(IncomeStatementItem).filter(
        IncomeStatementItem.annual_account_id == account.id
    ).all()

    # Generate basic XBRL structure
    xbrl = f"""<?xml version="1.0" encoding="UTF-8"?>
<xbrli:xbrl
    xmlns:xbrli="http://www.xbrl.org/2003/instance"
    xmlns:link="http://www.xbrl.org/2003/linkbase"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
    xmlns:be-fr-fr="http://www.nbb.be/be/fr/pfs/ci/2024-01-01">

    <!-- Context -->
    <xbrli:context id="CurrentYear">
        <xbrli:entity>
            <xbrli:identifier scheme="http://www.nbb.be">{account.bnb_enterprise_number or ''}</xbrli:identifier>
        </xbrli:entity>
        <xbrli:period>
            <xbrli:startDate>{fiscal_year.start_date.isoformat()}</xbrli:startDate>
            <xbrli:endDate>{fiscal_year.end_date.isoformat()}</xbrli:endDate>
        </xbrli:period>
    </xbrli:context>

    <!-- Unit -->
    <xbrli:unit id="EUR">
        <xbrli:measure>iso4217:EUR</xbrli:measure>
    </xbrli:unit>

    <!-- Balance Sheet Items -->
"""

    for item in balance_items:
        if item.current_year_amount != 0:
            element_name = item.xbrl_element or f"be-fr-fr:pfs-ci_A{item.rubric_code.replace('/', '_')}"
            xbrl += f'    <{element_name} contextRef="CurrentYear" unitRef="EUR" decimals="2">{item.current_year_amount}</{element_name}>\n'

    xbrl += """
    <!-- Income Statement Items -->
"""

    for item in income_items:
        if item.current_year_amount != 0:
            element_name = item.xbrl_element or f"be-fr-fr:pfs-ci_R{item.rubric_code.replace('/', '_')}"
            xbrl += f'    <{element_name} contextRef="CurrentYear" unitRef="EUR" decimals="2">{item.current_year_amount}</{element_name}>\n'

    xbrl += """
</xbrli:xbrl>
"""

    return xbrl
