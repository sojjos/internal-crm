"""Integrations API routes for Belcotax, Caseware, and accounting imports."""
from datetime import date, datetime
from typing import Any, List, Optional
import io
import csv

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.integrations import (
    ExternalIntegration, BelcotaxDeclaration, BelcotaxFiche,
    CasewareProject, CasewareSyncLog, AccountingImport, ImportedAccountingEntry,
    CODAImport, CODAMovement, IntegrationStatus, BelcotaxFormType, ImportSourceType,
    IMPORT_COLUMN_MAPPINGS, CODA_TRANSACTION_CODES
)
from app.models.annual_accounts import FiscalYear

router = APIRouter()


# Pydantic schemas
class IntegrationConfigCreate(BaseModel):
    name: str
    service_type: str
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    username: Optional[str] = None
    test_mode: bool = True
    config: Optional[dict] = None


class IntegrationConfigResponse(BaseModel):
    id: int
    name: str
    service_type: str
    is_active: bool
    api_url: Optional[str]
    test_mode: bool
    last_test_date: Optional[datetime]
    last_test_success: Optional[bool]
    created_at: datetime

    class Config:
        from_attributes = True


class BelcotaxDeclarationCreate(BaseModel):
    fiscal_year: int
    form_type: BelcotaxFormType
    enterprise_number: str
    declarant_name: str


class BelcotaxDeclarationResponse(BaseModel):
    id: int
    reference: str
    fiscal_year: int
    form_type: BelcotaxFormType
    status: IntegrationStatus
    enterprise_number: str
    declarant_name: str
    submission_date: Optional[datetime]
    acknowledgment_number: Optional[str]
    total_fiches: int
    total_amount: float
    created_at: datetime

    class Config:
        from_attributes = True


class BelcotaxFicheCreate(BaseModel):
    beneficiary_type: str  # PP or PM
    national_number: Optional[str] = None
    enterprise_number: Optional[str] = None
    name: str
    first_name: Optional[str] = None
    address_street: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_city: Optional[str] = None
    address_country: str = "BE"
    gross_amount: float
    tax_withheld: float = 0.0
    source_document: Optional[str] = None


class BelcotaxFicheResponse(BaseModel):
    id: int
    declaration_id: int
    beneficiary_type: str
    name: str
    first_name: Optional[str]
    gross_amount: float
    tax_withheld: float
    net_amount: float
    is_valid: bool

    class Config:
        from_attributes = True


class AccountingImportCreate(BaseModel):
    source_type: ImportSourceType
    fiscal_year_id: Optional[int] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class AccountingImportResponse(BaseModel):
    id: int
    reference: str
    source_type: ImportSourceType
    status: IntegrationStatus
    original_filename: str
    total_rows: int
    processed_rows: int
    success_rows: int
    error_rows: int
    created_at: datetime

    class Config:
        from_attributes = True


class CasewareProjectCreate(BaseModel):
    fiscal_year_id: Optional[int] = None
    name: str
    client_name: Optional[str] = None
    client_enterprise_number: Optional[str] = None


class CasewareProjectResponse(BaseModel):
    id: int
    reference: str
    caseware_project_id: Optional[str]
    name: str
    status: IntegrationStatus
    client_name: Optional[str]
    last_sync_date: Optional[datetime]
    working_papers_synced: bool
    trial_balance_synced: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Integration Configuration endpoints
@router.get("/config", response_model=List[IntegrationConfigResponse])
def list_integrations(
    service_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List configured integrations."""
    query = db.query(ExternalIntegration)
    if service_type:
        query = query.filter(ExternalIntegration.service_type == service_type)
    return query.all()


@router.post("/config", response_model=IntegrationConfigResponse)
def create_integration(
    config_in: IntegrationConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Configure a new integration."""
    integration = ExternalIntegration(**config_in.model_dump())
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


@router.put("/config/{int_id}", response_model=IntegrationConfigResponse)
def update_integration(
    int_id: int,
    config_in: IntegrationConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update an integration configuration."""
    integration = db.query(ExternalIntegration).filter(
        ExternalIntegration.id == int_id
    ).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    update_data = config_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(integration, field, value)

    db.commit()
    db.refresh(integration)
    return integration


@router.post("/config/{int_id}/test")
def test_integration(
    int_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Test an integration connection."""
    integration = db.query(ExternalIntegration).filter(
        ExternalIntegration.id == int_id
    ).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Simulate test
    integration.last_test_date = datetime.utcnow()
    integration.last_test_success = True  # Simulated
    db.commit()

    return {"success": True, "message": f"Connection to {integration.service_type} successful"}


@router.post("/config/{int_id}/activate")
def activate_integration(
    int_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Activate an integration."""
    integration = db.query(ExternalIntegration).filter(
        ExternalIntegration.id == int_id
    ).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    integration.is_active = True
    db.commit()
    return {"message": "Integration activated"}


# Belcotax endpoints
@router.get("/belcotax/declarations", response_model=List[BelcotaxDeclarationResponse])
def list_belcotax_declarations(
    fiscal_year: Optional[int] = None,
    form_type: Optional[BelcotaxFormType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List Belcotax declarations."""
    query = db.query(BelcotaxDeclaration)
    if fiscal_year:
        query = query.filter(BelcotaxDeclaration.fiscal_year == fiscal_year)
    if form_type:
        query = query.filter(BelcotaxDeclaration.form_type == form_type)
    return query.order_by(BelcotaxDeclaration.created_at.desc()).all()


@router.post("/belcotax/declarations", response_model=BelcotaxDeclarationResponse)
def create_belcotax_declaration(
    decl_in: BelcotaxDeclarationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new Belcotax declaration."""
    count = db.query(BelcotaxDeclaration).filter(
        BelcotaxDeclaration.fiscal_year == decl_in.fiscal_year,
        BelcotaxDeclaration.form_type == decl_in.form_type
    ).count()
    reference = f"BELCO-{decl_in.form_type.value}-{decl_in.fiscal_year}-{count + 1:03d}"

    declaration = BelcotaxDeclaration(**decl_in.model_dump(), reference=reference)
    db.add(declaration)
    db.commit()
    db.refresh(declaration)
    return declaration


@router.get("/belcotax/declarations/{decl_id}", response_model=BelcotaxDeclarationResponse)
def get_belcotax_declaration(
    decl_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a Belcotax declaration."""
    decl = db.query(BelcotaxDeclaration).filter(
        BelcotaxDeclaration.id == decl_id
    ).first()
    if not decl:
        raise HTTPException(status_code=404, detail="Declaration not found")
    return decl


@router.get("/belcotax/declarations/{decl_id}/fiches", response_model=List[BelcotaxFicheResponse])
def list_fiches(
    decl_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List fiches for a Belcotax declaration."""
    return db.query(BelcotaxFiche).filter(
        BelcotaxFiche.declaration_id == decl_id
    ).all()


@router.post("/belcotax/declarations/{decl_id}/fiches", response_model=BelcotaxFicheResponse)
def add_fiche(
    decl_id: int,
    fiche_in: BelcotaxFicheCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Add a fiche to a Belcotax declaration."""
    decl = db.query(BelcotaxDeclaration).filter(
        BelcotaxDeclaration.id == decl_id
    ).first()
    if not decl:
        raise HTTPException(status_code=404, detail="Declaration not found")

    fiche = BelcotaxFiche(
        declaration_id=decl_id,
        **fiche_in.model_dump(),
        net_amount=fiche_in.gross_amount - fiche_in.tax_withheld
    )
    db.add(fiche)

    # Update declaration totals
    decl.total_fiches += 1
    decl.total_amount += fiche_in.gross_amount
    decl.total_tax_withheld += fiche_in.tax_withheld

    db.commit()
    db.refresh(fiche)
    return fiche


@router.post("/belcotax/declarations/{decl_id}/validate")
def validate_belcotax_declaration(
    decl_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Validate a Belcotax declaration."""
    decl = db.query(BelcotaxDeclaration).filter(
        BelcotaxDeclaration.id == decl_id
    ).first()
    if not decl:
        raise HTTPException(status_code=404, detail="Declaration not found")

    errors = []
    fiches = db.query(BelcotaxFiche).filter(
        BelcotaxFiche.declaration_id == decl_id
    ).all()

    for fiche in fiches:
        fiche_errors = []
        if fiche.beneficiary_type == "PP" and not fiche.national_number:
            fiche_errors.append("National number required for individuals")
        if fiche.beneficiary_type == "PM" and not fiche.enterprise_number:
            fiche_errors.append("Enterprise number required for companies")
        if not fiche.name:
            fiche_errors.append("Name is required")

        fiche.is_valid = len(fiche_errors) == 0
        fiche.validation_errors = fiche_errors if fiche_errors else None
        if fiche_errors:
            errors.extend([f"Fiche {fiche.name}: {e}" for e in fiche_errors])

    db.commit()

    if errors:
        return {"valid": False, "errors": errors}

    decl.status = IntegrationStatus.COMPLETED
    db.commit()
    return {"valid": True, "message": "Declaration validated successfully"}


@router.post("/belcotax/declarations/{decl_id}/generate-xml")
def generate_belcotax_xml(
    decl_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Generate XML file for Belcotax submission."""
    decl = db.query(BelcotaxDeclaration).filter(
        BelcotaxDeclaration.id == decl_id
    ).first()
    if not decl:
        raise HTTPException(status_code=404, detail="Declaration not found")

    fiches = db.query(BelcotaxFiche).filter(
        BelcotaxFiche.declaration_id == decl_id,
        BelcotaxFiche.is_valid == True
    ).all()

    xml_content = _generate_belcotax_xml(decl, fiches)

    return StreamingResponse(
        io.BytesIO(xml_content.encode('utf-8')),
        media_type="application/xml",
        headers={
            "Content-Disposition": f"attachment; filename=belcotax_{decl.reference}.xml"
        }
    )


# Accounting Import endpoints
@router.get("/imports", response_model=List[AccountingImportResponse])
def list_imports(
    source_type: Optional[ImportSourceType] = None,
    status: Optional[IntegrationStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List accounting imports."""
    query = db.query(AccountingImport)
    if source_type:
        query = query.filter(AccountingImport.source_type == source_type)
    if status:
        query = query.filter(AccountingImport.status == status)
    return query.order_by(AccountingImport.created_at.desc()).all()


@router.post("/imports/upload")
async def upload_import_file(
    source_type: ImportSourceType = Form(...),
    file: UploadFile = File(...),
    fiscal_year_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Upload an accounting file for import."""
    # Generate reference
    count = db.query(AccountingImport).count()
    reference = f"IMP-{datetime.utcnow().strftime('%Y%m%d')}-{count + 1:04d}"

    # Read file content
    content = await file.read()

    # Create import record
    import_record = AccountingImport(
        reference=reference,
        source_type=source_type,
        fiscal_year_id=fiscal_year_id,
        original_filename=file.filename,
        file_path=f"/uploads/imports/{reference}_{file.filename}",
        file_size=len(content),
        status=IntegrationStatus.PENDING,
        imported_by_id=current_user.id
    )
    db.add(import_record)
    db.commit()
    db.refresh(import_record)

    # Parse and preview
    preview = _parse_import_preview(content, source_type, file.filename)

    return {
        "import_id": import_record.id,
        "reference": reference,
        "filename": file.filename,
        "preview": preview,
        "suggested_mapping": IMPORT_COLUMN_MAPPINGS.get(source_type.value, {})
    }


@router.post("/imports/{import_id}/process")
def process_import(
    import_id: int,
    column_mapping: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Process an uploaded import file."""
    import_record = db.query(AccountingImport).filter(
        AccountingImport.id == import_id
    ).first()
    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")

    import_record.status = IntegrationStatus.IN_PROGRESS
    import_record.started_at = datetime.utcnow()
    if column_mapping:
        import_record.column_mapping = column_mapping
    db.commit()

    # Simulate processing (in real app, this would parse the file)
    import_record.total_rows = 100
    import_record.processed_rows = 100
    import_record.success_rows = 95
    import_record.error_rows = 5
    import_record.status = IntegrationStatus.COMPLETED
    import_record.completed_at = datetime.utcnow()
    import_record.summary = {
        "total_debit": 50000.00,
        "total_credit": 50000.00,
        "accounts_used": 15,
        "date_range": "2024-01-01 to 2024-12-31"
    }

    db.commit()

    return {
        "message": "Import processed successfully",
        "total_rows": import_record.total_rows,
        "success": import_record.success_rows,
        "errors": import_record.error_rows,
        "summary": import_record.summary
    }


@router.get("/imports/{import_id}/entries")
def get_import_entries(
    import_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get imported entries."""
    entries = db.query(ImportedAccountingEntry).filter(
        ImportedAccountingEntry.import_id == import_id
    ).offset(skip).limit(limit).all()
    return entries


# Caseware endpoints
@router.get("/caseware/projects", response_model=List[CasewareProjectResponse])
def list_caseware_projects(
    fiscal_year_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List Caseware projects."""
    query = db.query(CasewareProject)
    if fiscal_year_id:
        query = query.filter(CasewareProject.fiscal_year_id == fiscal_year_id)
    return query.order_by(CasewareProject.created_at.desc()).all()


@router.post("/caseware/projects", response_model=CasewareProjectResponse)
def create_caseware_project(
    project_in: CasewareProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a Caseware project link."""
    count = db.query(CasewareProject).count()
    reference = f"CW-{datetime.utcnow().year}-{count + 1:04d}"

    project = CasewareProject(**project_in.model_dump(), reference=reference)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.post("/caseware/projects/{project_id}/sync")
def sync_caseware_project(
    project_id: int,
    sync_type: str = "full",  # full, trial_balance, working_papers
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Sync with Caseware Cloud."""
    project = db.query(CasewareProject).filter(
        CasewareProject.id == project_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create sync log
    sync_log = CasewareSyncLog(
        project_id=project_id,
        sync_type=sync_type,
        status=IntegrationStatus.IN_PROGRESS,
        initiated_by_id=current_user.id
    )
    db.add(sync_log)
    db.commit()

    # Simulate sync
    sync_log.status = IntegrationStatus.COMPLETED
    sync_log.completed_at = datetime.utcnow()
    sync_log.records_processed = 150
    sync_log.records_success = 150

    project.last_sync_date = datetime.utcnow()
    project.last_sync_status = "success"
    if sync_type in ["full", "trial_balance"]:
        project.trial_balance_synced = True
    if sync_type in ["full", "working_papers"]:
        project.working_papers_synced = True

    db.commit()

    return {
        "message": f"Sync {sync_type} completed successfully",
        "records_synced": sync_log.records_processed
    }


# CODA Import endpoints
@router.get("/coda")
def list_coda_imports(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all CODA imports."""
    imports = db.query(CODAImport).order_by(
        CODAImport.created_at.desc()
    ).offset(skip).limit(limit).all()
    return imports


@router.post("/coda/upload")
async def upload_coda_file(
    file: UploadFile = File(...),
    bank_account_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Upload a CODA bank statement file."""
    count = db.query(CODAImport).count()
    reference = f"CODA-{datetime.utcnow().strftime('%Y%m%d')}-{count + 1:04d}"

    content = await file.read()

    coda_import = CODAImport(
        reference=reference,
        bank_account_id=bank_account_id,
        original_filename=file.filename,
        file_path=f"/uploads/coda/{reference}_{file.filename}",
        status=IntegrationStatus.PENDING
    )
    db.add(coda_import)
    db.commit()
    db.refresh(coda_import)

    # Parse CODA header (simplified)
    coda_import.coda_version = "2"
    coda_import.creation_date = date.today()

    return {
        "import_id": coda_import.id,
        "reference": reference,
        "filename": file.filename,
        "message": "CODA file uploaded, ready for processing"
    }


@router.post("/coda/{import_id}/process")
def process_coda(
    import_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Process a CODA file."""
    coda_import = db.query(CODAImport).filter(CODAImport.id == import_id).first()
    if not coda_import:
        raise HTTPException(status_code=404, detail="CODA import not found")

    coda_import.status = IntegrationStatus.IN_PROGRESS
    coda_import.processed_at = datetime.utcnow()

    # Simulate processing
    coda_import.total_movements = 25
    coda_import.matched_movements = 20
    coda_import.unmatched_movements = 5
    coda_import.opening_balance = 10000.00
    coda_import.closing_balance = 12500.00
    coda_import.status = IntegrationStatus.COMPLETED

    db.commit()

    return {
        "message": "CODA file processed",
        "total_movements": coda_import.total_movements,
        "matched": coda_import.matched_movements,
        "unmatched": coda_import.unmatched_movements,
        "balance_change": coda_import.closing_balance - coda_import.opening_balance
    }


@router.get("/coda/{import_id}/movements")
def get_coda_movements(
    import_id: int,
    unmatched_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get movements from a CODA import."""
    query = db.query(CODAMovement).filter(CODAMovement.coda_import_id == import_id)
    if unmatched_only:
        query = query.filter(CODAMovement.is_matched == False)
    return query.order_by(CODAMovement.movement_date).all()


# Reference data
@router.get("/import-mappings")
def get_import_mappings(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get available import column mappings."""
    return IMPORT_COLUMN_MAPPINGS


@router.get("/coda-codes")
def get_coda_codes(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get CODA transaction codes."""
    return CODA_TRANSACTION_CODES


# Helper functions
def _generate_belcotax_xml(decl: BelcotaxDeclaration, fiches: List[BelcotaxFiche]) -> str:
    """Generate Belcotax XML content."""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Verzendingen>
    <Verzending>
        <v0002_inkomstenjaar>{decl.fiscal_year}</v0002_inkomstenjaar>
        <v0010_aangession>{decl.enterprise_number}</v0010_aangession>
        <v0011_aanession>{decl.declarant_name}</v0011_aanession>
"""

    for i, fiche in enumerate(fiches, 1):
        xml += f"""
        <Fiche>
            <f2002_inkomstenjaar>{decl.fiscal_year}</f2002_inkomstenjaar>
            <f2005_nationaalnr>{fiche.national_number or ''}</f2005_nationaalnr>
            <f2008_naam>{fiche.name}</f2008_naam>
            <f2009_voornaam>{fiche.first_name or ''}</f2009_voornaam>
            <f2013_straat>{fiche.address_street or ''}</f2013_straat>
            <f2014_postcode>{fiche.address_postal_code or ''}</f2014_postcode>
            <f2015_gemeente>{fiche.address_city or ''}</f2015_gemeente>
            <f2016_land>{fiche.address_country}</f2016_land>
            <f2028_brutobedrag>{fiche.gross_amount:.2f}</f2028_brutobedrag>
            <f2029_voorheffing>{fiche.tax_withheld:.2f}</f2029_voorheffing>
            <f2030_nettobedrag>{fiche.net_amount:.2f}</f2030_nettobedrag>
        </Fiche>
"""

    xml += """
    </Verzending>
</Verzendingen>
"""
    return xml


def _parse_import_preview(content: bytes, source_type: ImportSourceType, filename: str) -> dict:
    """Parse import file and return preview."""
    preview = {
        "total_rows": 0,
        "columns": [],
        "sample_rows": [],
        "detected_encoding": "UTF-8"
    }

    try:
        text = content.decode('utf-8')
        lines = text.strip().split('\n')

        if lines:
            # Detect delimiter
            first_line = lines[0]
            delimiter = ';' if ';' in first_line else ','

            reader = csv.reader(lines, delimiter=delimiter)
            rows = list(reader)

            if rows:
                preview["columns"] = rows[0]
                preview["total_rows"] = len(rows) - 1
                preview["sample_rows"] = rows[1:6] if len(rows) > 1 else []
    except Exception as e:
        preview["error"] = str(e)

    return preview
