"""Intervention and planning routes."""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.intervention import (
    Intervention, InterventionLine, InterventionStatus, InterventionType
)
from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from app.schemas.intervention import (
    InterventionCreate, InterventionUpdate, InterventionResponse,
    InterventionLineCreate, InterventionLineResponse, CalendarEvent
)

router = APIRouter()


def generate_reference(db: Session) -> str:
    """Generate a unique intervention reference."""
    year = datetime.now().year
    count = db.query(func.count(Intervention.id)).filter(
        func.extract('year', Intervention.created_at) == year
    ).scalar() or 0
    return f"INT-{year}-{str(count + 1).zfill(4)}"


@router.get("/", response_model=List[InterventionResponse])
def get_interventions(
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[int] = None,
    assigned_to_id: Optional[int] = None,
    status: Optional[InterventionStatus] = None,
    intervention_type: Optional[InterventionType] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    query = db.query(Intervention).options(
        joinedload(Intervention.client),
        joinedload(Intervention.assigned_to),
        joinedload(Intervention.lines)
    )

    if client_id:
        query = query.filter(Intervention.client_id == client_id)
    if assigned_to_id:
        query = query.filter(Intervention.assigned_to_id == assigned_to_id)
    if status:
        query = query.filter(Intervention.status == status)
    if intervention_type:
        query = query.filter(Intervention.intervention_type == intervention_type)
    if date_from:
        query = query.filter(Intervention.scheduled_date >= date_from)
    if date_to:
        query = query.filter(Intervention.scheduled_date <= date_to)

    interventions = query.order_by(
        Intervention.scheduled_date.desc()
    ).offset(skip).limit(limit).all()

    result = []
    for i in interventions:
        total_htva = sum(line.total_htva for line in i.lines)
        total_vat = sum(line.total_vat for line in i.lines)

        result.append({
            **i.__dict__,
            "client_name": i.client.name if i.client else None,
            "assigned_to_name": f"{i.assigned_to.first_name} {i.assigned_to.last_name}" if i.assigned_to else None,
            "total_htva": total_htva,
            "total_tvac": total_htva + total_vat,
            "lines": i.lines,
        })

    return result


@router.post("/", response_model=InterventionResponse, status_code=status.HTTP_201_CREATED)
def create_intervention(
    intervention_in: InterventionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Generate reference
    reference = generate_reference(db)

    # Create intervention
    intervention_data = intervention_in.model_dump(exclude={"lines"})
    intervention = Intervention(**intervention_data)
    intervention.reference = reference
    intervention.created_by_id = current_user.id
    db.add(intervention)
    db.flush()

    # Add lines
    for line_data in intervention_in.lines:
        line = InterventionLine(**line_data.model_dump())
        line.intervention_id = intervention.id
        db.add(line)

    db.commit()
    db.refresh(intervention)

    return intervention


@router.get("/{intervention_id}", response_model=InterventionResponse)
def get_intervention(
    intervention_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    intervention = db.query(Intervention).options(
        joinedload(Intervention.client),
        joinedload(Intervention.assigned_to),
        joinedload(Intervention.lines)
    ).filter(Intervention.id == intervention_id).first()

    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    total_htva = sum(line.total_htva for line in intervention.lines)
    total_vat = sum(line.total_vat for line in intervention.lines)

    return {
        **intervention.__dict__,
        "client_name": intervention.client.name if intervention.client else None,
        "assigned_to_name": f"{intervention.assigned_to.first_name} {intervention.assigned_to.last_name}" if intervention.assigned_to else None,
        "total_htva": total_htva,
        "total_tvac": total_htva + total_vat,
        "lines": intervention.lines,
    }


@router.put("/{intervention_id}", response_model=InterventionResponse)
def update_intervention(
    intervention_id: int,
    intervention_in: InterventionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id
    ).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    for field, value in intervention_in.model_dump(exclude_unset=True).items():
        setattr(intervention, field, value)

    db.commit()
    db.refresh(intervention)
    return intervention


@router.delete("/{intervention_id}")
def delete_intervention(
    intervention_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id
    ).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    if intervention.status == InterventionStatus.FACTUREE:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a billed intervention"
        )

    db.delete(intervention)
    db.commit()
    return {"message": "Intervention deleted"}


# ============ Lines ============

@router.post("/{intervention_id}/lines", response_model=InterventionLineResponse)
def add_line(
    intervention_id: int,
    line_in: InterventionLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id
    ).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    line = InterventionLine(**line_in.model_dump())
    line.intervention_id = intervention_id
    db.add(line)
    db.commit()
    db.refresh(line)
    return line


@router.delete("/{intervention_id}/lines/{line_id}")
def delete_line(
    intervention_id: int,
    line_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    line = db.query(InterventionLine).filter(
        InterventionLine.id == line_id,
        InterventionLine.intervention_id == intervention_id
    ).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")

    db.delete(line)
    db.commit()
    return {"message": "Line deleted"}


# ============ Status Actions ============

@router.post("/{intervention_id}/start")
def start_intervention(
    intervention_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id
    ).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    intervention.status = InterventionStatus.EN_COURS
    intervention.actual_start = datetime.utcnow()
    db.commit()
    return {"message": "Intervention started"}


@router.post("/{intervention_id}/complete")
def complete_intervention(
    intervention_id: int,
    work_performed: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id
    ).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    intervention.status = InterventionStatus.TERMINEE
    intervention.actual_end = datetime.utcnow()
    if work_performed:
        intervention.work_performed = work_performed
    db.commit()
    return {"message": "Intervention completed"}


@router.post("/{intervention_id}/create-invoice")
def create_invoice_from_intervention(
    intervention_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create an invoice from a completed intervention."""
    intervention = db.query(Intervention).options(
        joinedload(Intervention.client),
        joinedload(Intervention.lines)
    ).filter(Intervention.id == intervention_id).first()

    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    if intervention.status == InterventionStatus.FACTUREE:
        raise HTTPException(status_code=400, detail="Already invoiced")

    if not intervention.is_billable:
        raise HTTPException(status_code=400, detail="Intervention is not billable")

    # Generate invoice number
    year = datetime.now().year
    count = db.query(func.count(Invoice.id)).filter(
        func.extract('year', Invoice.invoice_date) == year
    ).scalar() or 0
    invoice_number = f"FAC-{year}-{str(count + 1).zfill(4)}"

    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_number,
        client_id=intervention.client_id,
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        status=InvoiceStatus.DRAFT,
        notes=f"Intervention {intervention.reference} du {intervention.scheduled_date}"
    )
    db.add(invoice)
    db.flush()

    # Add lines from intervention
    total_htva = Decimal("0")
    total_vat = Decimal("0")

    for int_line in intervention.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            description=int_line.description,
            quantity=int_line.quantity,
            unit_price_htva=int_line.unit_price_htva,
            vat_rate=int_line.vat_rate,
            discount_percent=int_line.discount_percent
        )
        db.add(line)
        total_htva += int_line.total_htva
        total_vat += int_line.total_vat

    # Add travel cost if any
    if intervention.travel_cost > 0:
        travel_line = InvoiceLine(
            invoice_id=invoice.id,
            description="Frais de deplacement",
            quantity=Decimal("1"),
            unit_price_htva=intervention.travel_cost,
            vat_rate=Decimal("21")
        )
        db.add(travel_line)
        total_htva += intervention.travel_cost
        total_vat += intervention.travel_cost * Decimal("0.21")

    # Update invoice totals
    invoice.total_htva = total_htva
    invoice.total_vat = total_vat
    invoice.total_tvac = total_htva + total_vat

    # Update intervention
    intervention.invoice_id = invoice.id
    intervention.status = InterventionStatus.FACTUREE

    db.commit()

    return {"message": "Invoice created", "invoice_id": invoice.id}


# ============ Calendar ============

@router.get("/calendar/events", response_model=List[CalendarEvent])
def get_calendar_events(
    start_date: date = Query(...),
    end_date: date = Query(...),
    assigned_to_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get interventions as calendar events."""
    query = db.query(Intervention).options(
        joinedload(Intervention.client),
        joinedload(Intervention.assigned_to)
    ).filter(
        Intervention.scheduled_date >= start_date,
        Intervention.scheduled_date <= end_date
    )

    if assigned_to_id:
        query = query.filter(Intervention.assigned_to_id == assigned_to_id)

    interventions = query.all()

    events = []
    for i in interventions:
        # Build datetime from date and time
        start_dt = datetime.combine(
            i.scheduled_date,
            i.scheduled_start_time or datetime.min.time()
        )
        end_dt = datetime.combine(
            i.scheduled_date,
            i.scheduled_end_time or (start_dt + timedelta(minutes=i.estimated_duration_minutes)).time()
        )

        # Color based on status
        color_map = {
            InterventionStatus.PLANIFIEE: "#3B82F6",  # Blue
            InterventionStatus.EN_COURS: "#F59E0B",   # Yellow
            InterventionStatus.TERMINEE: "#10B981",   # Green
            InterventionStatus.FACTUREE: "#8B5CF6",   # Purple
            InterventionStatus.ANNULEE: "#EF4444",    # Red
        }

        events.append(CalendarEvent(
            id=i.id,
            title=i.title,
            start=start_dt,
            end=end_dt,
            client_name=i.client.name if i.client else "N/A",
            status=i.status,
            priority=i.priority,
            assigned_to_name=f"{i.assigned_to.first_name} {i.assigned_to.last_name}" if i.assigned_to else None,
            color=color_map.get(i.status, "#6B7280")
        ))

    return events
