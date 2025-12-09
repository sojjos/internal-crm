"""Quote (Devis) routes."""
import os
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from fastapi.responses import FileResponse

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.quote import Quote, QuoteLine, QuoteStatus
from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from app.models.company import CompanySettings
from app.models.document import Document, DocumentType
from app.schemas.quote import (
    QuoteCreate, QuoteUpdate, QuoteResponse,
    QuoteLineCreate, QuoteLineUpdate, QuoteLineResponse,
    QuoteConvertRequest
)
from app.services.pdf_service import generate_quote_pdf
from app.core.config import settings

router = APIRouter()


def generate_quote_number(db: Session) -> str:
    """Generate a unique quote number."""
    year = datetime.now().year
    count = db.query(func.count(Quote.id)).filter(
        func.extract('year', Quote.created_at) == year
    ).scalar() or 0
    return f"DEV-{year}-{str(count + 1).zfill(4)}"


def calculate_quote_totals(quote: Quote) -> None:
    """Calculate and update quote totals from lines."""
    total_htva = Decimal("0")
    total_vat = Decimal("0")

    for line in quote.lines:
        if not line.is_optional:  # Don't include optional lines in total
            total_htva += line.total_htva
            total_vat += line.total_vat

    quote.total_htva = total_htva - quote.discount_amount
    quote.total_vat = total_vat
    quote.total_tvac = quote.total_htva + quote.total_vat


@router.get("/", response_model=List[QuoteResponse])
def get_quotes(
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[int] = None,
    status: Optional[QuoteStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    query = db.query(Quote).options(
        joinedload(Quote.client),
        joinedload(Quote.lines)
    )

    if client_id:
        query = query.filter(Quote.client_id == client_id)
    if status:
        query = query.filter(Quote.status == status)
    if date_from:
        query = query.filter(Quote.quote_date >= date_from)
    if date_to:
        query = query.filter(Quote.quote_date <= date_to)

    quotes = query.order_by(Quote.quote_date.desc()).offset(skip).limit(limit).all()

    return [
        {
            **q.__dict__,
            "client_name": q.client.name if q.client else None,
            "lines": q.lines,
        }
        for q in quotes
    ]


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_quote(
    quote_in: QuoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Generate quote number
    quote_number = generate_quote_number(db)

    # Create quote
    quote_data = quote_in.model_dump(exclude={"lines"})
    quote = Quote(**quote_data)
    quote.quote_number = quote_number
    quote.validation_token = uuid.uuid4().hex
    quote.created_by_id = current_user.id
    db.add(quote)
    db.flush()

    # Add lines
    for position, line_data in enumerate(quote_in.lines):
        line = QuoteLine(**line_data.model_dump())
        line.quote_id = quote.id
        line.position = position
        db.add(line)

    db.flush()

    # Calculate totals
    db.refresh(quote)
    calculate_quote_totals(quote)

    db.commit()
    db.refresh(quote)

    return quote


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    quote = db.query(Quote).options(
        joinedload(Quote.client),
        joinedload(Quote.lines)
    ).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    return {
        **quote.__dict__,
        "client_name": quote.client.name if quote.client else None,
        "lines": sorted(quote.lines, key=lambda x: x.position),
    }


@router.put("/{quote_id}", response_model=QuoteResponse)
def update_quote(
    quote_id: int,
    quote_in: QuoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if quote.status == QuoteStatus.CONVERTI:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify a converted quote"
        )

    for field, value in quote_in.model_dump(exclude_unset=True).items():
        setattr(quote, field, value)

    # Recalculate totals if discount changed
    if "discount_amount" in quote_in.model_dump(exclude_unset=True):
        db.refresh(quote)
        calculate_quote_totals(quote)

    db.commit()
    db.refresh(quote)
    return quote


@router.delete("/{quote_id}")
def delete_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if quote.status in [QuoteStatus.ACCEPTE, QuoteStatus.CONVERTI]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete an accepted or converted quote"
        )

    db.delete(quote)
    db.commit()
    return {"message": "Quote deleted"}


# ============ Lines ============

@router.post("/{quote_id}/lines", response_model=QuoteLineResponse)
def add_line(
    quote_id: int,
    line_in: QuoteLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    # Get max position
    max_pos = db.query(func.max(QuoteLine.position)).filter(
        QuoteLine.quote_id == quote_id
    ).scalar() or -1

    line = QuoteLine(**line_in.model_dump())
    line.quote_id = quote_id
    line.position = max_pos + 1
    db.add(line)
    db.flush()

    # Recalculate totals
    db.refresh(quote)
    calculate_quote_totals(quote)

    db.commit()
    db.refresh(line)
    return line


@router.put("/{quote_id}/lines/{line_id}", response_model=QuoteLineResponse)
def update_line(
    quote_id: int,
    line_id: int,
    line_in: QuoteLineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    line = db.query(QuoteLine).filter(
        QuoteLine.id == line_id,
        QuoteLine.quote_id == quote_id
    ).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")

    for field, value in line_in.model_dump(exclude_unset=True).items():
        setattr(line, field, value)

    db.flush()

    # Recalculate totals
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    calculate_quote_totals(quote)

    db.commit()
    db.refresh(line)
    return line


@router.delete("/{quote_id}/lines/{line_id}")
def delete_line(
    quote_id: int,
    line_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    line = db.query(QuoteLine).filter(
        QuoteLine.id == line_id,
        QuoteLine.quote_id == quote_id
    ).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")

    db.delete(line)
    db.flush()

    # Recalculate totals
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    calculate_quote_totals(quote)

    db.commit()
    return {"message": "Line deleted"}


# ============ Actions ============

@router.post("/{quote_id}/send")
def send_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Mark quote as sent."""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote.status = QuoteStatus.ENVOYE
    quote.sent_at = datetime.utcnow()
    db.commit()

    # TODO: Actually send email with quote PDF

    return {"message": "Quote sent", "validation_token": quote.validation_token}


@router.post("/{quote_id}/accept")
def accept_quote(
    quote_id: int,
    accepted_by: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Accept a quote."""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote.status = QuoteStatus.ACCEPTE
    quote.accepted_at = datetime.utcnow()
    quote.accepted_by = accepted_by or current_user.email
    db.commit()

    return {"message": "Quote accepted"}


@router.post("/{quote_id}/reject")
def reject_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Reject a quote."""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote.status = QuoteStatus.REFUSE
    db.commit()

    return {"message": "Quote rejected"}


@router.post("/{quote_id}/convert-to-invoice")
def convert_to_invoice(
    quote_id: int,
    request: QuoteConvertRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Convert an accepted quote to an invoice."""
    quote = db.query(Quote).options(
        joinedload(Quote.lines)
    ).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if quote.status == QuoteStatus.CONVERTI:
        raise HTTPException(status_code=400, detail="Quote already converted")

    if quote.status not in [QuoteStatus.ACCEPTE, QuoteStatus.BROUILLON]:
        raise HTTPException(
            status_code=400,
            detail="Only accepted quotes can be converted"
        )

    # Generate invoice number
    year = datetime.now().year
    count = db.query(func.count(Invoice.id)).filter(
        func.extract('year', Invoice.invoice_date) == year
    ).scalar() or 0
    invoice_number = f"FAC-{year}-{str(count + 1).zfill(4)}"

    # Determine dates
    invoice_date = request.invoice_date if request and request.invoice_date else date.today()
    due_date = request.due_date if request and request.due_date else (
        invoice_date + timedelta(days=quote.payment_terms_days)
    )
    include_optional = request.include_optional_lines if request else False

    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_number,
        client_id=quote.client_id,
        invoice_date=invoice_date,
        due_date=due_date,
        status=InvoiceStatus.DRAFT,
        notes=f"Cree depuis devis {quote.quote_number}"
    )
    db.add(invoice)
    db.flush()

    # Add lines from quote
    total_htva = Decimal("0")
    total_vat = Decimal("0")

    for quote_line in sorted(quote.lines, key=lambda x: x.position):
        # Skip optional lines unless requested
        if quote_line.is_optional and not include_optional:
            continue

        inv_line = InvoiceLine(
            invoice_id=invoice.id,
            description=quote_line.description,
            quantity=float(quote_line.quantity),
            unit_price=float(quote_line.unit_price_htva),
            vat_rate=float(quote_line.vat_rate),
            discount_percent=float(quote_line.discount_percent),
            line_total_htva=float(quote_line.total_htva),
            line_total_vat=float(quote_line.total_vat),
            line_total_tvac=float(quote_line.total_tvac)
        )
        db.add(inv_line)
        total_htva += quote_line.total_htva
        total_vat += quote_line.total_vat

    # Apply quote discount
    total_htva -= quote.discount_amount

    # Update invoice totals
    invoice.total_htva = total_htva
    invoice.total_vat = total_vat
    invoice.total_tvac = total_htva + total_vat

    # Update quote
    quote.status = QuoteStatus.CONVERTI
    quote.converted_to_invoice_id = invoice.id
    quote.converted_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Quote converted to invoice",
        "invoice_id": invoice.id,
        "invoice_number": invoice_number
    }


# ============ Client Validation (public) ============

@router.get("/validate/{token}")
def get_quote_for_validation(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """Get quote details for client validation (public endpoint)."""
    quote = db.query(Quote).options(
        joinedload(Quote.client),
        joinedload(Quote.lines)
    ).filter(Quote.validation_token == token).first()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    # Mark as viewed
    if not quote.viewed_at:
        quote.viewed_at = datetime.utcnow()
        db.commit()

    return {
        "quote_number": quote.quote_number,
        "quote_date": quote.quote_date,
        "validity_date": quote.validity_date,
        "client_name": quote.client.name if quote.client else None,
        "subject": quote.subject,
        "introduction": quote.introduction,
        "terms": quote.terms,
        "total_htva": quote.total_htva,
        "total_vat": quote.total_vat,
        "total_tvac": quote.total_tvac,
        "lines": [
            {
                "description": l.description,
                "quantity": l.quantity,
                "unit": l.unit,
                "unit_price_htva": l.unit_price_htva,
                "total_htva": l.total_htva,
                "is_optional": l.is_optional,
                "section": l.section,
            }
            for l in sorted(quote.lines, key=lambda x: x.position)
        ]
    }


@router.post("/validate/{token}/accept")
def client_accept_quote(
    token: str,
    accepted_by: str = Query(..., description="Name of person accepting"),
    db: Session = Depends(get_db)
) -> Any:
    """Client accepts quote via validation link."""
    quote = db.query(Quote).filter(Quote.validation_token == token).first()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if quote.validity_date and quote.validity_date < date.today():
        raise HTTPException(status_code=400, detail="Quote has expired")

    quote.status = QuoteStatus.ACCEPTE
    quote.accepted_at = datetime.utcnow()
    quote.accepted_by = accepted_by
    db.commit()

    return {"message": "Quote accepted successfully"}


# ============ PDF Generation ============

def create_quote_document(db: Session, quote: Quote, pdf_path: str, user_id: int) -> Document:
    """Create or update Document record for a quote PDF."""
    # Check if document already exists for this quote
    existing_doc = db.query(Document).filter(
        Document.quote_id == quote.id,
        Document.document_type == DocumentType.DEVIS_CLIENT
    ).first()

    # Get file info
    full_path = os.path.join(settings.UPLOAD_DIR, pdf_path)
    file_size = os.path.getsize(full_path) if os.path.exists(full_path) else 0
    file_name = os.path.basename(pdf_path)

    if existing_doc:
        # Update existing document
        existing_doc.file_path = pdf_path
        existing_doc.file_name = file_name
        existing_doc.file_size = file_size
        existing_doc.updated_at = datetime.utcnow()
        return existing_doc
    else:
        # Create new document
        doc = Document(
            title=f"Devis {quote.quote_number}",
            description=f"Devis client {quote.quote_number}",
            document_type=DocumentType.DEVIS_CLIENT,
            file_path=pdf_path,
            file_name=file_name,
            file_size=file_size,
            mime_type="application/pdf",
            document_date=quote.quote_date,
            quote_id=quote.id,
            client_id=quote.client_id,
            created_by_id=user_id
        )
        db.add(doc)
        return doc


@router.post("/{quote_id}/generate-pdf")
def generate_pdf(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Generate PDF for a quote."""
    quote = db.query(Quote).options(
        joinedload(Quote.client),
        joinedload(Quote.lines)
    ).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    # Get company settings
    company = db.query(CompanySettings).first()
    if not company:
        raise HTTPException(status_code=400, detail="Company settings not configured")

    # Determine if quote is accepted
    is_accepted = quote.status == QuoteStatus.ACCEPTE
    accepted_date = quote.accepted_at.date() if quote.accepted_at else None

    # Generate PDF
    pdf_path = generate_quote_pdf(
        quote,
        company,
        is_accepted=is_accepted,
        accepted_date=accepted_date
    )

    # Update quote
    quote.pdf_path = pdf_path

    # Create Document record
    create_quote_document(db, quote, pdf_path, current_user.id)

    db.commit()

    return {
        "message": "PDF generated",
        "pdf_path": pdf_path,
        "download_url": f"/api/quotes/{quote_id}/download-pdf"
    }


@router.get("/{quote_id}/download-pdf")
def download_pdf(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Download quote PDF."""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if not quote.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not generated yet")

    import os
    file_path = os.path.join(settings.UPLOAD_DIR, quote.pdf_path)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"devis_{quote.quote_number.replace('/', '-')}.pdf"
    )
