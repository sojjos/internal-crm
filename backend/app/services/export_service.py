"""Export services for generating Excel/CSV files."""
from datetime import date
from typing import List, TYPE_CHECKING
import io

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.expense import Expense


def export_invoices_to_excel(invoices: List["Invoice"]) -> bytes:
    """Export invoices to Excel format.

    Args:
        invoices: List of Invoice models with client loaded

    Returns:
        Excel file as bytes
    """
    # Prepare data
    data = []
    for inv in invoices:
        data.append({
            "Numéro": inv.invoice_number,
            "Date": inv.invoice_date.strftime("%d/%m/%Y"),
            "Client": inv.client.name if inv.client else "",
            "TVA Client": inv.client.vat_number if inv.client else "",
            "Montant HTVA": inv.total_htva,
            "TVA": inv.total_vat,
            "Montant TVAC": inv.total_tvac,
            "Statut": inv.status.value,
            "Date Paiement": inv.payment_date.strftime("%d/%m/%Y") if inv.payment_date else "",
            "Référence Paiement": inv.payment_reference or "",
        })

    df = pd.DataFrame(data)

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Factures"

    # Add header styling
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Write data
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=value)
            cell.border = thin_border
            if r_idx == 1:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")

    # Adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column_letter].width = max_length + 2

    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def export_expenses_to_excel(expenses: List["Expense"]) -> bytes:
    """Export expenses to Excel format.

    Args:
        expenses: List of Expense models with relations loaded

    Returns:
        Excel file as bytes
    """
    data = []
    for exp in expenses:
        data.append({
            "Date": exp.expense_date.strftime("%d/%m/%Y"),
            "Collaborateur": exp.collaborator.full_name if exp.collaborator else "",
            "Type": exp.expense_type.name if exp.expense_type else "",
            "Description": exp.description or "",
            "Fournisseur": exp.supplier.name if exp.supplier else "",
            "Montant HTVA": exp.amount_htva,
            "TVA": exp.vat_amount,
            "Montant TVAC": exp.amount_tvac,
            "Période Paie": exp.payroll_period or "",
            "Validé": "Oui" if exp.is_validated else "Non",
            "Remboursé": "Oui" if exp.is_reimbursed else "Non",
        })

    df = pd.DataFrame(data)

    wb = Workbook()
    ws = wb.active
    ws.title = "Notes de Frais"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=value)
            cell.border = thin_border
            if r_idx == 1:
                cell.font = header_font
                cell.fill = header_fill

    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column_letter].width = max_length + 2

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def export_payroll_to_excel(expenses: List["Expense"], period: str) -> bytes:
    """Export payroll data to Excel.

    Args:
        expenses: List of Expense models for the period
        period: Payroll period string (e.g., "2025-03")

    Returns:
        Excel file as bytes
    """
    data = []
    for exp in expenses:
        data.append({
            "Collaborateur": exp.collaborator.full_name if exp.collaborator else "",
            "Type de Frais": exp.expense_type.name if exp.expense_type else "",
            "Date": exp.expense_date.strftime("%d/%m/%Y"),
            "Description": exp.description or "",
            "Montant TVAC": exp.amount_tvac,
            "Commentaire": exp.notes or "",
        })

    df = pd.DataFrame(data)

    wb = Workbook()
    ws = wb.active
    ws.title = f"Paie {period}"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=value)
            cell.border = thin_border
            if r_idx == 1:
                cell.font = header_font
                cell.fill = header_fill

    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column_letter].width = max_length + 2

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def export_vat_report(
    invoices: List["Invoice"],
    expenses: List["Expense"],
    date_from: date,
    date_to: date
) -> bytes:
    """Export VAT report to Excel.

    Args:
        invoices: List of invoices
        expenses: List of expenses
        date_from: Period start date
        date_to: Period end date

    Returns:
        Excel file as bytes
    """
    wb = Workbook()

    # Summary sheet
    ws_summary = wb.active
    ws_summary.title = "Résumé TVA"

    total_vat_collected = sum(inv.total_vat for inv in invoices)
    total_vat_deductible = sum(exp.vat_amount for exp in expenses)
    total_base_sales = sum(inv.total_htva for inv in invoices)
    total_base_purchases = sum(exp.amount_htva for exp in expenses)

    ws_summary["A1"] = "Rapport TVA"
    ws_summary["A1"].font = Font(bold=True, size=14)

    ws_summary["A3"] = "Période:"
    ws_summary["B3"] = f"{date_from.strftime('%d/%m/%Y')} - {date_to.strftime('%d/%m/%Y')}"

    ws_summary["A5"] = "TVA Collectée (Ventes)"
    ws_summary["A5"].font = Font(bold=True)
    ws_summary["A6"] = "Base imposable:"
    ws_summary["B6"] = total_base_sales
    ws_summary["A7"] = "TVA:"
    ws_summary["B7"] = total_vat_collected

    ws_summary["A9"] = "TVA Déductible (Achats)"
    ws_summary["A9"].font = Font(bold=True)
    ws_summary["A10"] = "Base imposable:"
    ws_summary["B10"] = total_base_purchases
    ws_summary["A11"] = "TVA:"
    ws_summary["B11"] = total_vat_deductible

    ws_summary["A13"] = "Solde TVA"
    ws_summary["A13"].font = Font(bold=True)
    ws_summary["A14"] = "À payer:" if total_vat_collected >= total_vat_deductible else "À récupérer:"
    ws_summary["B14"] = abs(total_vat_collected - total_vat_deductible)

    # Sales detail sheet
    ws_sales = wb.create_sheet("Ventes")
    sales_data = []
    for inv in invoices:
        sales_data.append({
            "Numéro": inv.invoice_number,
            "Date": inv.invoice_date.strftime("%d/%m/%Y"),
            "Client": inv.client.name if inv.client else "",
            "TVA Client": inv.client.vat_number if inv.client else "",
            "Base HTVA": inv.total_htva,
            "TVA": inv.total_vat,
            "Total TVAC": inv.total_tvac,
        })

    df_sales = pd.DataFrame(sales_data)
    for r_idx, row in enumerate(dataframe_to_rows(df_sales, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            ws_sales.cell(row=r_idx, column=c_idx, value=value)

    # Purchases detail sheet
    ws_purchases = wb.create_sheet("Achats")
    purchases_data = []
    for exp in expenses:
        purchases_data.append({
            "Date": exp.expense_date.strftime("%d/%m/%Y"),
            "Fournisseur": exp.supplier.name if exp.supplier else "",
            "Description": exp.description or "",
            "Base HTVA": exp.amount_htva,
            "TVA": exp.vat_amount,
            "Total TVAC": exp.amount_tvac,
        })

    df_purchases = pd.DataFrame(purchases_data)
    for r_idx, row in enumerate(dataframe_to_rows(df_purchases, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            ws_purchases.cell(row=r_idx, column=c_idx, value=value)

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
