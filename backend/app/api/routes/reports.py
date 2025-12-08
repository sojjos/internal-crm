"""Reporting and export routes."""
from datetime import date
from typing import Any, List, Optional
import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.invoice import Invoice, InvoiceStatus
from app.models.expense import Expense
from app.services.export_service import (
    export_invoices_to_excel,
    export_expenses_to_excel,
    export_vat_report
)

router = APIRouter()


class MonthlySummary(BaseModel):
    """Monthly summary statistics."""
    year: int
    month: int
    revenue_htva: float
    revenue_tvac: float
    vat_collected: float
    expenses_htva: float
    expenses_tvac: float
    vat_deductible: float
    invoices_count: int
    invoices_paid: int
    invoices_overdue: int


class VATSummary(BaseModel):
    """VAT summary for a period."""
    period_start: date
    period_end: date
    vat_collected: float  # TVA sur ventes
    vat_deductible: float  # TVA sur achats
    vat_balance: float  # À payer ou à récupérer


class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_revenue_ytd: float
    total_expenses_ytd: float
    outstanding_invoices: float
    overdue_invoices: float
    invoices_this_month: int
    expenses_this_month: int


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get dashboard statistics."""
    today = date.today()
    year_start = date(today.year, 1, 1)
    month_start = date(today.year, today.month, 1)

    # YTD Revenue
    total_revenue = db.query(func.sum(Invoice.total_tvac)).filter(
        Invoice.invoice_date >= year_start,
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PAID])
    ).scalar() or 0.0

    # YTD Expenses
    total_expenses = db.query(func.sum(Expense.amount_tvac)).filter(
        Expense.expense_date >= year_start
    ).scalar() or 0.0

    # Outstanding invoices
    outstanding = db.query(func.sum(Invoice.total_tvac)).filter(
        Invoice.status == InvoiceStatus.SENT
    ).scalar() or 0.0

    # Overdue invoices
    overdue = db.query(func.sum(Invoice.total_tvac)).filter(
        Invoice.status == InvoiceStatus.SENT,
        Invoice.due_date < today
    ).scalar() or 0.0

    # Invoices this month
    invoices_month = db.query(func.count(Invoice.id)).filter(
        Invoice.invoice_date >= month_start
    ).scalar() or 0

    # Expenses this month
    expenses_month = db.query(func.count(Expense.id)).filter(
        Expense.expense_date >= month_start
    ).scalar() or 0

    return DashboardStats(
        total_revenue_ytd=float(total_revenue),
        total_expenses_ytd=float(total_expenses),
        outstanding_invoices=float(outstanding),
        overdue_invoices=float(overdue),
        invoices_this_month=invoices_month,
        expenses_this_month=expenses_month
    )


@router.get("/monthly", response_model=List[MonthlySummary])
def get_monthly_summary(
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get monthly summary for a year."""
    summaries = []

    for month in range(1, 13):
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1)
        else:
            month_end = date(year, month + 1, 1)

        # Invoice stats
        invoice_stats = db.query(
            func.sum(Invoice.total_htva).label("htva"),
            func.sum(Invoice.total_tvac).label("tvac"),
            func.sum(Invoice.total_vat).label("vat"),
            func.count(Invoice.id).label("count")
        ).filter(
            Invoice.invoice_date >= month_start,
            Invoice.invoice_date < month_end,
            Invoice.status != InvoiceStatus.CANCELLED
        ).first()

        # Paid invoices
        paid_count = db.query(func.count(Invoice.id)).filter(
            Invoice.invoice_date >= month_start,
            Invoice.invoice_date < month_end,
            Invoice.status == InvoiceStatus.PAID
        ).scalar() or 0

        # Overdue invoices
        today = date.today()
        overdue_count = db.query(func.count(Invoice.id)).filter(
            Invoice.invoice_date >= month_start,
            Invoice.invoice_date < month_end,
            Invoice.status == InvoiceStatus.SENT,
            Invoice.due_date < today
        ).scalar() or 0

        # Expense stats
        expense_stats = db.query(
            func.sum(Expense.amount_htva).label("htva"),
            func.sum(Expense.amount_tvac).label("tvac"),
            func.sum(Expense.vat_amount).label("vat")
        ).filter(
            Expense.expense_date >= month_start,
            Expense.expense_date < month_end
        ).first()

        summaries.append(MonthlySummary(
            year=year,
            month=month,
            revenue_htva=float(invoice_stats.htva or 0),
            revenue_tvac=float(invoice_stats.tvac or 0),
            vat_collected=float(invoice_stats.vat or 0),
            expenses_htva=float(expense_stats.htva or 0),
            expenses_tvac=float(expense_stats.tvac or 0),
            vat_deductible=float(expense_stats.vat or 0),
            invoices_count=invoice_stats.count or 0,
            invoices_paid=paid_count,
            invoices_overdue=overdue_count
        ))

    return summaries


@router.get("/vat", response_model=VATSummary)
def get_vat_summary(
    date_from: date,
    date_to: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get VAT summary for a period."""
    # VAT collected (from invoices)
    vat_collected = db.query(func.sum(Invoice.total_vat)).filter(
        Invoice.invoice_date >= date_from,
        Invoice.invoice_date <= date_to,
        Invoice.status != InvoiceStatus.CANCELLED
    ).scalar() or 0.0

    # VAT deductible (from expenses)
    vat_deductible = db.query(func.sum(Expense.vat_amount)).filter(
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to
    ).scalar() or 0.0

    return VATSummary(
        period_start=date_from,
        period_end=date_to,
        vat_collected=float(vat_collected),
        vat_deductible=float(vat_deductible),
        vat_balance=float(vat_collected) - float(vat_deductible)
    )


@router.get("/export/invoices")
def export_invoices(
    date_from: date,
    date_to: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Export invoices to Excel for accountant."""
    invoices = db.query(Invoice).options(
        joinedload(Invoice.client),
        joinedload(Invoice.lines)
    ).filter(
        Invoice.invoice_date >= date_from,
        Invoice.invoice_date <= date_to,
        Invoice.status != InvoiceStatus.CANCELLED
    ).order_by(Invoice.invoice_date).all()

    excel_buffer = export_invoices_to_excel(invoices)

    return StreamingResponse(
        io.BytesIO(excel_buffer),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=invoices_{date_from}_{date_to}.xlsx"
        }
    )


@router.get("/export/expenses")
def export_expenses(
    date_from: date,
    date_to: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Export expenses to Excel for accountant."""
    expenses = db.query(Expense).options(
        joinedload(Expense.expense_type),
        joinedload(Expense.collaborator),
        joinedload(Expense.supplier)
    ).filter(
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to
    ).order_by(Expense.expense_date).all()

    excel_buffer = export_expenses_to_excel(expenses)

    return StreamingResponse(
        io.BytesIO(excel_buffer),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=expenses_{date_from}_{date_to}.xlsx"
        }
    )


@router.get("/export/vat")
def export_vat(
    date_from: date,
    date_to: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Export VAT report to Excel for accountant."""
    # Get invoices
    invoices = db.query(Invoice).options(
        joinedload(Invoice.client)
    ).filter(
        Invoice.invoice_date >= date_from,
        Invoice.invoice_date <= date_to,
        Invoice.status != InvoiceStatus.CANCELLED
    ).order_by(Invoice.invoice_date).all()

    # Get expenses
    expenses = db.query(Expense).options(
        joinedload(Expense.supplier)
    ).filter(
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to
    ).order_by(Expense.expense_date).all()

    excel_buffer = export_vat_report(invoices, expenses, date_from, date_to)

    return StreamingResponse(
        io.BytesIO(excel_buffer),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=vat_report_{date_from}_{date_to}.xlsx"
        }
    )
