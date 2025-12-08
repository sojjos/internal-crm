"""Purchase schemas for the Purchases & Investments module."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.purchase import (
    PurchaseType, ContractType, ContractPeriodicity, PaymentMethod,
    PurchaseStatus, AssetType, DepreciationMethod, VehicleType
)


# ============ Purchase Category Schemas ============

class PurchaseCategoryBase(BaseModel):
    """Base purchase category schema."""
    name: str
    description: Optional[str] = None
    purchase_type: PurchaseType = PurchaseType.DEPENSE
    pcmn_account: Optional[str] = None
    pcmn_label: Optional[str] = None
    default_vat_rate: Decimal = Decimal("21.00")
    default_vat_deductible_rate: Decimal = Decimal("100.00")
    default_fiscal_deductible_rate: Decimal = Decimal("100.00")
    is_potential_investment: bool = False
    investment_threshold_htva: Decimal = Decimal("1000.00")
    default_depreciation_years: Optional[int] = None
    default_depreciation_method: DepreciationMethod = DepreciationMethod.LINEAIRE
    default_asset_type: Optional[AssetType] = None


class PurchaseCategoryCreate(PurchaseCategoryBase):
    """Schema for creating a purchase category."""
    pass


class PurchaseCategoryUpdate(BaseModel):
    """Schema for updating a purchase category."""
    name: Optional[str] = None
    description: Optional[str] = None
    purchase_type: Optional[PurchaseType] = None
    pcmn_account: Optional[str] = None
    pcmn_label: Optional[str] = None
    default_vat_rate: Optional[Decimal] = None
    default_vat_deductible_rate: Optional[Decimal] = None
    default_fiscal_deductible_rate: Optional[Decimal] = None
    is_potential_investment: Optional[bool] = None
    investment_threshold_htva: Optional[Decimal] = None
    default_depreciation_years: Optional[int] = None
    default_depreciation_method: Optional[DepreciationMethod] = None
    default_asset_type: Optional[AssetType] = None
    is_active: Optional[bool] = None


class PurchaseCategoryResponse(PurchaseCategoryBase):
    """Schema for purchase category response."""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Purchase Contract Schemas ============

class PurchaseContractBase(BaseModel):
    """Base purchase contract schema."""
    supplier_id: int
    category_id: int
    contract_type: ContractType = ContractType.AUTRE
    name: str
    description: Optional[str] = None
    reference: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    periodicity: ContractPeriodicity = ContractPeriodicity.MENSUEL
    amount_htva: Decimal
    vat_rate: Decimal = Decimal("21.00")
    payment_method: PaymentMethod = PaymentMethod.DOMICILIATION
    billing_day: int = 1
    vehicle_type: Optional[VehicleType] = None
    vehicle_co2: Optional[int] = None
    vehicle_registration: Optional[str] = None


class PurchaseContractCreate(PurchaseContractBase):
    """Schema for creating a purchase contract."""
    pass


class PurchaseContractUpdate(BaseModel):
    """Schema for updating a purchase contract."""
    category_id: Optional[int] = None
    contract_type: Optional[ContractType] = None
    name: Optional[str] = None
    description: Optional[str] = None
    reference: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    periodicity: Optional[ContractPeriodicity] = None
    amount_htva: Optional[Decimal] = None
    vat_rate: Optional[Decimal] = None
    payment_method: Optional[PaymentMethod] = None
    billing_day: Optional[int] = None
    vehicle_type: Optional[VehicleType] = None
    vehicle_co2: Optional[int] = None
    vehicle_registration: Optional[str] = None
    is_active: Optional[bool] = None


class PurchaseContractResponse(PurchaseContractBase):
    """Schema for purchase contract response."""
    id: int
    is_active: bool
    next_billing_date: Optional[date]
    created_at: datetime

    # Calculated fields
    amount_ttc: Optional[Decimal] = None
    monthly_amount: Optional[Decimal] = None

    class Config:
        from_attributes = True


class PurchaseContractWithSupplier(PurchaseContractResponse):
    """Contract response with supplier details."""
    supplier_name: Optional[str] = None
    category_name: Optional[str] = None


# ============ Purchase Schemas ============

class PurchaseBase(BaseModel):
    """Base purchase schema."""
    supplier_id: int
    category_id: int
    contract_id: Optional[int] = None
    purchase_date: date
    supplier_invoice_number: Optional[str] = None
    description: str
    amount_htva: Decimal
    vat_rate: Decimal = Decimal("21.00")
    vat_deductible_rate: Optional[Decimal] = None  # Will be calculated from category
    fiscal_deductible_rate: Optional[Decimal] = None  # Will be calculated from category
    pcmn_account: Optional[str] = None  # Override category default
    is_investment: bool = False
    payment_method: Optional[PaymentMethod] = None


class PurchaseCreate(PurchaseBase):
    """Schema for creating a purchase."""
    # Optional: create fixed asset at the same time
    create_fixed_asset: bool = False
    asset_name: Optional[str] = None
    asset_type: Optional[AssetType] = None
    depreciation_years: Optional[int] = None
    service_start_date: Optional[date] = None


class PurchaseUpdate(BaseModel):
    """Schema for updating a purchase."""
    category_id: Optional[int] = None
    contract_id: Optional[int] = None
    purchase_date: Optional[date] = None
    supplier_invoice_number: Optional[str] = None
    description: Optional[str] = None
    amount_htva: Optional[Decimal] = None
    vat_rate: Optional[Decimal] = None
    vat_deductible_rate: Optional[Decimal] = None
    fiscal_deductible_rate: Optional[Decimal] = None
    pcmn_account: Optional[str] = None
    is_investment: Optional[bool] = None
    payment_method: Optional[PaymentMethod] = None
    payment_date: Optional[date] = None
    payment_reference: Optional[str] = None
    status: Optional[PurchaseStatus] = None


class PurchaseResponse(BaseModel):
    """Schema for purchase response."""
    id: int
    supplier_id: int
    category_id: int
    contract_id: Optional[int]
    purchase_date: date
    supplier_invoice_number: Optional[str]
    description: str

    # Amounts
    amount_htva: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    vat_deductible_rate: Decimal
    vat_deductible_amount: Decimal
    vat_non_deductible_amount: Decimal
    fiscal_deductible_rate: Decimal

    # Calculated
    amount_ttc: Decimal

    # Accounting
    pcmn_account: Optional[str]
    is_investment: bool
    fixed_asset_id: Optional[int]

    # Payment
    payment_method: Optional[PaymentMethod]
    payment_date: Optional[date]
    payment_reference: Optional[str]
    status: PurchaseStatus

    document_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PurchaseWithDetails(PurchaseResponse):
    """Purchase response with related entity details."""
    supplier_name: Optional[str] = None
    category_name: Optional[str] = None
    contract_name: Optional[str] = None


class PurchaseCalculation(BaseModel):
    """Schema for purchase calculation request/response."""
    amount_htva: Decimal
    vat_rate: Decimal
    vat_deductible_rate: Decimal
    fiscal_deductible_rate: Decimal

    # Calculated outputs
    vat_amount: Optional[Decimal] = None
    vat_deductible_amount: Optional[Decimal] = None
    vat_non_deductible_amount: Optional[Decimal] = None
    amount_ttc: Optional[Decimal] = None
    is_above_investment_threshold: Optional[bool] = None


# ============ Fixed Asset Schemas ============

class FixedAssetBase(BaseModel):
    """Base fixed asset schema."""
    name: str
    description: Optional[str] = None
    asset_type: AssetType = AssetType.AUTRE
    pcmn_account: Optional[str] = None
    pcmn_depreciation_account: Optional[str] = None
    acquisition_value: Decimal
    residual_value: Decimal = Decimal("0")
    service_start_date: date
    depreciation_years: int
    depreciation_method: DepreciationMethod = DepreciationMethod.LINEAIRE
    vehicle_type: Optional[VehicleType] = None
    vehicle_co2: Optional[int] = None
    vehicle_registration: Optional[str] = None


class FixedAssetCreate(FixedAssetBase):
    """Schema for creating a fixed asset."""
    pass


class FixedAssetUpdate(BaseModel):
    """Schema for updating a fixed asset."""
    name: Optional[str] = None
    description: Optional[str] = None
    asset_type: Optional[AssetType] = None
    pcmn_account: Optional[str] = None
    pcmn_depreciation_account: Optional[str] = None
    residual_value: Optional[Decimal] = None
    depreciation_years: Optional[int] = None
    depreciation_method: Optional[DepreciationMethod] = None
    vehicle_type: Optional[VehicleType] = None
    vehicle_co2: Optional[int] = None
    vehicle_registration: Optional[str] = None
    is_active: Optional[bool] = None
    disposal_date: Optional[date] = None
    disposal_value: Optional[Decimal] = None


class DepreciationEntryResponse(BaseModel):
    """Schema for depreciation entry response."""
    id: int
    fiscal_year: int
    period_start: date
    period_end: date
    amount: Decimal
    cumulative_amount: Decimal
    book_value_after: Decimal
    is_posted: bool
    posted_at: Optional[datetime]

    class Config:
        from_attributes = True


class FixedAssetResponse(FixedAssetBase):
    """Schema for fixed asset response."""
    id: int
    is_active: bool
    disposal_date: Optional[date]
    disposal_value: Optional[Decimal]

    # Calculated
    annual_depreciation: Decimal
    current_book_value: Decimal

    created_at: datetime

    class Config:
        from_attributes = True


class FixedAssetWithDepreciation(FixedAssetResponse):
    """Fixed asset with depreciation schedule."""
    depreciation_entries: List[DepreciationEntryResponse] = []
    purchase: Optional[PurchaseResponse] = None


# ============ Report Schemas ============

class PurchaseSummary(BaseModel):
    """Summary of purchases for a period."""
    period_start: date
    period_end: date
    total_htva: Decimal
    total_vat: Decimal
    total_vat_deductible: Decimal
    total_vat_non_deductible: Decimal
    total_ttc: Decimal
    purchase_count: int
    by_category: List[dict]
    by_pcmn: List[dict]


class PCMNReport(BaseModel):
    """PCMN (Belgian chart of accounts) report."""
    period_start: date
    period_end: date
    accounts: List[dict]  # [{account, label, debit, credit}]
    total_debit: Decimal
    total_credit: Decimal


class VATReport(BaseModel):
    """VAT report for purchases."""
    period_start: date
    period_end: date
    purchases_htva: Decimal
    purchases_vat_total: Decimal
    purchases_vat_deductible: Decimal
    purchases_vat_non_deductible: Decimal
    # From invoices (sales)
    sales_htva: Decimal
    sales_vat_collected: Decimal
    # Net
    vat_balance: Decimal  # VAT collected - VAT deductible


class InvestmentReport(BaseModel):
    """Investment/Fixed assets report."""
    as_of_date: date
    assets: List[FixedAssetResponse]
    total_acquisition_value: Decimal
    total_current_book_value: Decimal
    total_depreciation_this_year: Decimal
