"""Purchase service for calculations and business logic."""
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.purchase import (
    Purchase, PurchaseCategory, PurchaseContract, FixedAsset, DepreciationEntry,
    PurchaseStatus, ContractPeriodicity
)
from app.models.invoice import Invoice, InvoiceStatus
from app.models.expense import Expense


def calculate_vat_amounts(
    amount_htva: Decimal,
    vat_rate: Decimal,
    vat_deductible_rate: Decimal
) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
    """
    Calculate VAT amounts.

    Returns:
        (vat_amount, vat_deductible, vat_non_deductible, amount_ttc)
    """
    vat_amount = (amount_htva * vat_rate / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    vat_deductible = (vat_amount * vat_deductible_rate / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    vat_non_deductible = vat_amount - vat_deductible
    amount_ttc = amount_htva + vat_amount

    return vat_amount, vat_deductible, vat_non_deductible, amount_ttc


def should_be_investment(category: PurchaseCategory, amount_htva: Decimal) -> bool:
    """Check if a purchase should be classified as an investment."""
    if not category.is_potential_investment:
        return False
    return amount_htva >= category.investment_threshold_htva


def get_category_defaults(category: PurchaseCategory) -> dict:
    """Get default values from a category for a new purchase."""
    return {
        "vat_rate": category.default_vat_rate,
        "vat_deductible_rate": category.default_vat_deductible_rate,
        "fiscal_deductible_rate": category.default_fiscal_deductible_rate,
        "pcmn_account": category.pcmn_account,
        "is_potential_investment": category.is_potential_investment,
        "investment_threshold": category.investment_threshold_htva,
    }


def create_depreciation_schedule(asset: FixedAsset) -> List[dict]:
    """
    Generate a depreciation schedule for a fixed asset.

    Returns list of depreciation entries (not saved to DB).
    """
    entries = []
    depreciable_value = asset.acquisition_value - (asset.residual_value or Decimal(0))
    annual_amount = (depreciable_value / asset.depreciation_years).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    cumulative = Decimal(0)
    current_date = asset.service_start_date

    for year in range(1, asset.depreciation_years + 1):
        # Calculate period dates
        period_start = date(current_date.year + year - 1, 1, 1)
        period_end = date(current_date.year + year - 1, 12, 31)

        # First year: prorate from service start date
        if year == 1:
            period_start = asset.service_start_date
            # Prorate first year
            days_in_year = 365
            days_remaining = (period_end - period_start).days + 1
            year_amount = (annual_amount * days_remaining / days_in_year).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        elif year == asset.depreciation_years:
            # Last year: remainder
            year_amount = depreciable_value - cumulative
        else:
            year_amount = annual_amount

        cumulative += year_amount
        book_value = asset.acquisition_value - cumulative

        entries.append({
            "fiscal_year": period_start.year,
            "period_start": period_start,
            "period_end": period_end,
            "amount": year_amount,
            "cumulative_amount": cumulative,
            "book_value_after": book_value,
        })

    return entries


def save_depreciation_schedule(db: Session, asset: FixedAsset) -> List[DepreciationEntry]:
    """Generate and save depreciation entries for an asset."""
    # Remove existing entries
    db.query(DepreciationEntry).filter(DepreciationEntry.asset_id == asset.id).delete()

    schedule = create_depreciation_schedule(asset)
    entries = []

    for entry_data in schedule:
        entry = DepreciationEntry(
            asset_id=asset.id,
            **entry_data
        )
        db.add(entry)
        entries.append(entry)

    db.commit()
    return entries


def get_next_billing_dates(contract: PurchaseContract) -> List[date]:
    """Get the next billing dates for a contract."""
    if not contract.is_active:
        return []

    today = date.today()
    dates = []

    # Calculate period delta
    if contract.periodicity == ContractPeriodicity.MENSUEL:
        delta = relativedelta(months=1)
    elif contract.periodicity == ContractPeriodicity.TRIMESTRIEL:
        delta = relativedelta(months=3)
    elif contract.periodicity == ContractPeriodicity.SEMESTRIEL:
        delta = relativedelta(months=6)
    else:  # ANNUEL
        delta = relativedelta(years=1)

    # Find next date
    current = contract.start_date
    while current < today:
        current += delta

    # Get next 12 occurrences
    for _ in range(12):
        if contract.end_date and current > contract.end_date:
            break
        dates.append(current)
        current += delta

    return dates


def generate_purchases_from_contracts(
    db: Session,
    contracts: List[PurchaseContract],
    for_date: date
) -> List[Purchase]:
    """
    Generate purchase entries from contracts for a specific date.

    Used for automatic generation of recurring purchases.
    """
    generated = []

    for contract in contracts:
        if not contract.is_active:
            continue

        # Check if purchase already exists for this period
        existing = db.query(Purchase).filter(
            Purchase.contract_id == contract.id,
            Purchase.purchase_date == for_date
        ).first()

        if existing:
            continue

        # Get category defaults
        category = contract.category

        # Calculate amounts
        vat_amount, vat_deductible, vat_non_deductible, amount_ttc = calculate_vat_amounts(
            contract.amount_htva,
            contract.vat_rate,
            category.default_vat_deductible_rate
        )

        # Create purchase
        purchase = Purchase(
            supplier_id=contract.supplier_id,
            category_id=contract.category_id,
            contract_id=contract.id,
            purchase_date=for_date,
            description=f"{contract.name} - {for_date.strftime('%m/%Y')}",
            amount_htva=contract.amount_htva,
            vat_rate=contract.vat_rate,
            vat_amount=vat_amount,
            vat_deductible_rate=category.default_vat_deductible_rate,
            vat_deductible_amount=vat_deductible,
            vat_non_deductible_amount=vat_non_deductible,
            fiscal_deductible_rate=category.default_fiscal_deductible_rate,
            pcmn_account=category.pcmn_account,
            payment_method=contract.payment_method,
            status=PurchaseStatus.BROUILLON,
        )
        db.add(purchase)
        generated.append(purchase)

    db.commit()
    return generated


def get_purchases_summary(
    db: Session,
    start_date: date,
    end_date: date
) -> dict:
    """Get summary of purchases for a period."""
    purchases = db.query(Purchase).filter(
        Purchase.purchase_date >= start_date,
        Purchase.purchase_date <= end_date,
        Purchase.status != PurchaseStatus.ANNULE
    ).all()

    total_htva = sum(p.amount_htva for p in purchases)
    total_vat = sum(p.vat_amount for p in purchases)
    total_vat_deductible = sum(p.vat_deductible_amount for p in purchases)
    total_vat_non_deductible = sum(p.vat_non_deductible_amount for p in purchases)

    # By category
    by_category = {}
    for p in purchases:
        cat_id = p.category_id
        if cat_id not in by_category:
            by_category[cat_id] = {
                "category_id": cat_id,
                "category_name": p.category.name if p.category else "Unknown",
                "total_htva": Decimal(0),
                "count": 0
            }
        by_category[cat_id]["total_htva"] += p.amount_htva
        by_category[cat_id]["count"] += 1

    # By PCMN account
    by_pcmn = {}
    for p in purchases:
        account = p.pcmn_account or "Unknown"
        if account not in by_pcmn:
            by_pcmn[account] = {
                "account": account,
                "total_htva": Decimal(0),
                "count": 0
            }
        by_pcmn[account]["total_htva"] += p.amount_htva
        by_pcmn[account]["count"] += 1

    return {
        "period_start": start_date,
        "period_end": end_date,
        "total_htva": total_htva,
        "total_vat": total_vat,
        "total_vat_deductible": total_vat_deductible,
        "total_vat_non_deductible": total_vat_non_deductible,
        "total_ttc": total_htva + total_vat,
        "purchase_count": len(purchases),
        "by_category": list(by_category.values()),
        "by_pcmn": list(by_pcmn.values()),
    }


def get_vat_report(
    db: Session,
    start_date: date,
    end_date: date
) -> dict:
    """Generate VAT report including purchases, expenses, and sales."""
    # Purchases
    purchases = db.query(Purchase).filter(
        Purchase.purchase_date >= start_date,
        Purchase.purchase_date <= end_date,
        Purchase.status != PurchaseStatus.ANNULE
    ).all()

    purchases_htva = sum(p.amount_htva for p in purchases)
    purchases_vat_total = sum(p.vat_amount for p in purchases)
    purchases_vat_deductible = sum(p.vat_deductible_amount for p in purchases)
    purchases_vat_non_deductible = sum(p.vat_non_deductible_amount for p in purchases)

    # Expenses (notes de frais) - add to purchases
    expenses = db.query(Expense).filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).all()

    for e in expenses:
        # Expenses are typically TTC, need to extract VAT
        if e.vat_rate and e.vat_rate > 0:
            htva = e.amount / (1 + e.vat_rate / 100)
            vat = e.amount - htva
            purchases_htva += htva
            purchases_vat_total += vat
            # Assume expenses are fully deductible unless specified otherwise
            purchases_vat_deductible += vat

    # Sales (invoices)
    invoices = db.query(Invoice).filter(
        Invoice.invoice_date >= start_date,
        Invoice.invoice_date <= end_date,
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PAID])
    ).all()

    sales_htva = sum(i.total_htva for i in invoices)
    sales_vat_collected = sum(i.total_vat for i in invoices)

    # VAT balance (positive = owe to state, negative = refund due)
    vat_balance = sales_vat_collected - purchases_vat_deductible

    return {
        "period_start": start_date,
        "period_end": end_date,
        "purchases_htva": purchases_htva,
        "purchases_vat_total": purchases_vat_total,
        "purchases_vat_deductible": purchases_vat_deductible,
        "purchases_vat_non_deductible": purchases_vat_non_deductible,
        "sales_htva": sales_htva,
        "sales_vat_collected": sales_vat_collected,
        "vat_balance": vat_balance,
    }


def get_pcmn_report(
    db: Session,
    start_date: date,
    end_date: date
) -> dict:
    """
    Generate PCMN (Belgian chart of accounts) report.

    Includes:
    - Purchases by PCMN account
    - Expenses by type (mapped to PCMN)
    - Revenue from invoices
    """
    accounts = {}

    # Purchases (class 6 - charges)
    purchases = db.query(Purchase).filter(
        Purchase.purchase_date >= start_date,
        Purchase.purchase_date <= end_date,
        Purchase.status != PurchaseStatus.ANNULE
    ).all()

    for p in purchases:
        account = p.pcmn_account or "600000"
        if account not in accounts:
            accounts[account] = {
                "account": account,
                "label": p.category.pcmn_label if p.category else "",
                "debit": Decimal(0),
                "credit": Decimal(0),
            }
        accounts[account]["debit"] += p.amount_htva

    # Expenses (class 6)
    expenses = db.query(Expense).filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).all()

    for e in expenses:
        # Map expense type to PCMN account
        account = "612000"  # Default: services divers
        if e.expense_type:
            # Map based on expense type name
            type_name = e.expense_type.name.lower()
            if "déplacement" in type_name or "transport" in type_name:
                account = "613100"
            elif "repas" in type_name or "restaurant" in type_name:
                account = "614000"
            elif "hébergement" in type_name:
                account = "614100"
            elif "matériel" in type_name:
                account = "601000"
            elif "fourniture" in type_name:
                account = "612200"

        if account not in accounts:
            accounts[account] = {
                "account": account,
                "label": "",
                "debit": Decimal(0),
                "credit": Decimal(0),
            }

        # Expense amount (HTVA if possible)
        if e.vat_rate and e.vat_rate > 0:
            amount = e.amount / (1 + e.vat_rate / 100)
        else:
            amount = e.amount

        accounts[account]["debit"] += amount

    # Invoices (class 7 - revenue)
    invoices = db.query(Invoice).filter(
        Invoice.invoice_date >= start_date,
        Invoice.invoice_date <= end_date,
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PAID])
    ).all()

    revenue_account = "700000"  # Ventes
    if revenue_account not in accounts:
        accounts[revenue_account] = {
            "account": revenue_account,
            "label": "Chiffre d'affaires",
            "debit": Decimal(0),
            "credit": Decimal(0),
        }

    for i in invoices:
        accounts[revenue_account]["credit"] += i.total_htva

    # Sort by account number
    sorted_accounts = sorted(accounts.values(), key=lambda x: x["account"])

    total_debit = sum(a["debit"] for a in sorted_accounts)
    total_credit = sum(a["credit"] for a in sorted_accounts)

    return {
        "period_start": start_date,
        "period_end": end_date,
        "accounts": sorted_accounts,
        "total_debit": total_debit,
        "total_credit": total_credit,
    }


def get_investment_report(db: Session, as_of_date: date) -> dict:
    """Generate investment/fixed assets report."""
    assets = db.query(FixedAsset).filter(
        FixedAsset.is_active == True,
        FixedAsset.service_start_date <= as_of_date
    ).all()

    total_acquisition = sum(a.acquisition_value for a in assets)
    total_book_value = sum(a.current_book_value for a in assets)

    # Calculate this year's depreciation
    year_start = date(as_of_date.year, 1, 1)
    year_depreciation = Decimal(0)

    for asset in assets:
        for entry in asset.depreciation_entries:
            if entry.fiscal_year == as_of_date.year:
                year_depreciation += entry.amount

    return {
        "as_of_date": as_of_date,
        "assets": assets,
        "total_acquisition_value": total_acquisition,
        "total_current_book_value": total_book_value,
        "total_depreciation_this_year": year_depreciation,
    }
