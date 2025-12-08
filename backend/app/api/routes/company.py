"""Company settings routes."""
from typing import Any
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.company import CompanySettings
from app.schemas.company import CompanySettingsCreate, CompanySettingsUpdate, CompanySettingsResponse

router = APIRouter()


def get_or_create_settings(db: Session) -> CompanySettings:
    """Get company settings or create default."""
    company = db.query(CompanySettings).first()
    if not company:
        company = CompanySettings(company_name="Ma Société")
        db.add(company)
        db.commit()
        db.refresh(company)
    return company


@router.get("/", response_model=CompanySettingsResponse)
def get_company_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get company settings."""
    return get_or_create_settings(db)


@router.put("/", response_model=CompanySettingsResponse)
def update_company_settings(
    settings_in: CompanySettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update company settings."""
    company = get_or_create_settings(db)

    update_data = settings_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    db.commit()
    db.refresh(company)
    return company


@router.post("/logo", response_model=CompanySettingsResponse)
async def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Upload company logo."""
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed: PNG, JPEG, GIF"
        )

    # Create upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, "logos")
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"logo_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_dir, filename)

    # Save file
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Update company settings
    company = get_or_create_settings(db)
    company.logo_path = filepath
    db.commit()
    db.refresh(company)

    return company


@router.get("/next-invoice-number")
def get_next_invoice_number(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get the next invoice number preview."""
    company = get_or_create_settings(db)
    return {"next_number": company.get_next_invoice_number()}
