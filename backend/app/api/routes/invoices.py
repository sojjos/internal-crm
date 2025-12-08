"""Invoice routes."""
from datetime import date, datetime
from typing import Any, List, Optional
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from app.models.client import Client
from app.models.company import CompanySettings
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    InvoiceLineCreate, InvoiceLineUpdate, InvoiceLineResponse
)
from app.services.pdf_service import generate_invoice_pdf
from app.services.email_service import send_invoice_email
from app.services.peppol_service import generate_ubl_invoice, send_peppol_invoice

router = APIRouter()


def get_company_settings(db: Session) -> CompanySettings:
    """Get company settings."""
    company = db.query(CompanySettings).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company settings not configured"
        )
    return company


@router.get("/", response_model=List[InvoiceResponse])
def get_invoices(
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[int] = None,
    status_filter: Optional[InvoiceStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all invoices with optional filtering."""
    query = db.query(Invoice).options(joinedload(Invoice.lines))

    if client_id:
        query = query.filter(Invoice.client_id == client_id)

    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    if date_from:
        query = query.filter(Invoice.invoice_date >= date_from)

    if date_to:
        query = query.filter(Invoice.invoice_date <= date_to)

    invoices = query.order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit).all()
    return invoices


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice_in: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new invoice."""
    # Verify client exists
    client = db.query(Client).filter(Client.id == invoice_in.client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Get company settings for invoice number
    company = get_company_settings(db)

    # Create invoice
    invoice_data = invoice_in.model_dump(exclude={"lines"})
    invoice_data["invoice_number"] = company.get_next_invoice_number()
    invoice_data["created_by_id"] = current_user.id

    invoice = Invoice(**invoice_data)
    db.add(invoice)

    # Update next invoice number
    company.invoice_next_number += 1

    # Add lines
    for i, line_data in enumerate(invoice_in.lines, 1):
        line = InvoiceLine(
            **line_data.model_dump(),
            line_number=i
        )
        line.calculate_totals()
        invoice.lines.append(line)

    # Calculate invoice totals
    invoice.calculate_totals()

    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a specific invoice."""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.lines),
        joinedload(Invoice.client)
    ).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int,
    invoice_in: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update an invoice (only if draft)."""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.lines)
    ).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    if invoice.status != InvoiceStatus.DRAFT and invoice_in.status is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a non-draft invoice"
        )

    update_data = invoice_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    db.commit()
    db.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/lines", response_model=InvoiceLineResponse)
def add_invoice_line(
    invoice_id: int,
    line_in: InvoiceLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Add a line to an invoice."""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.lines)
    ).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a non-draft invoice"
        )

    # Get next line number
    max_line = max([l.line_number for l in invoice.lines], default=0)

    line = InvoiceLine(
        **line_in.model_dump(),
        invoice_id=invoice_id,
        line_number=max_line + 1
    )
    line.calculate_totals()
    db.add(line)

    # Recalculate invoice totals
    invoice.lines.append(line)
    invoice.calculate_totals()

    db.commit()
    db.refresh(line)
    return line


@router.delete("/{invoice_id}/lines/{line_id}")
def delete_invoice_line(
    invoice_id: int,
    line_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete a line from an invoice."""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.lines)
    ).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a non-draft invoice"
        )

    line = db.query(InvoiceLine).filter(
        InvoiceLine.id == line_id,
        InvoiceLine.invoice_id == invoice_id
    ).first()

    if not line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice line not found"
        )

    db.delete(line)
    invoice.calculate_totals()
    db.commit()

    return {"message": "Line deleted"}


@router.post("/{invoice_id}/generate-pdf")
def generate_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Generate PDF for an invoice."""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.lines),
        joinedload(Invoice.client)
    ).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    company = get_company_settings(db)

    try:
        pdf_path = generate_invoice_pdf(invoice, company)
        invoice.pdf_path = pdf_path
        db.commit()
        return {"pdf_path": pdf_path}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: int,
    background_tasks: BackgroundTasks,
    send_email: bool = True,
    send_peppol: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Send invoice via email and/or Peppol."""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.lines),
        joinedload(Invoice.client)
    ).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    company = get_company_settings(db)

    # Generate PDF if not exists
    if not invoice.pdf_path:
        invoice.pdf_path = generate_invoice_pdf(invoice, company)

    # Generate UBL if Peppol
    if send_peppol and company.peppol_enabled:
        if not invoice.ubl_path:
            invoice.ubl_path = generate_ubl_invoice(invoice, company)

    # Update status
    if invoice.status == InvoiceStatus.DRAFT:
        invoice.status = InvoiceStatus.SENT

    # Send email
    if send_email and invoice.client.email:
        background_tasks.add_task(
            send_invoice_email,
            invoice,
            company
        )
        invoice.sent_via_email = True
        invoice.email_sent_at = datetime.utcnow()

    # Send Peppol
    if send_peppol and company.peppol_enabled and invoice.client.peppol_id:
        background_tasks.add_task(
            send_peppol_invoice,
            invoice,
            company
        )
        invoice.sent_via_peppol = True
        invoice.peppol_sent_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Invoice sending initiated",
        "email": send_email and bool(invoice.client.email),
        "peppol": send_peppol and company.peppol_enabled and bool(invoice.client.peppol_id)
    }


@router.post("/{invoice_id}/mark-paid")
def mark_invoice_paid(
    invoice_id: int,
    payment_date: Optional[date] = None,
    payment_reference: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Mark an invoice as paid."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    invoice.status = InvoiceStatus.PAID
    invoice.payment_date = payment_date or date.today()
    invoice.payment_reference = payment_reference

    db.commit()

    return {"message": "Invoice marked as paid"}


@router.delete("/{invoice_id}")
def cancel_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Cancel an invoice."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a paid invoice"
        )

    invoice.status = InvoiceStatus.CANCELLED
    db.commit()

    return {"message": "Invoice cancelled"}
