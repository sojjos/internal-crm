"""Purchase models for the Purchases & Investments module."""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date,
    ForeignKey, Enum, Numeric, JSON
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class PurchaseType(str, PyEnum):
    """Type of purchase."""
    DEPENSE = "depense"  # Regular expense
    INVESTISSEMENT = "investissement"  # Capital investment
    ABONNEMENT = "abonnement"  # Subscription
    LEASING_VOITURE = "leasing_voiture"  # Car leasing
    SERVICE = "service"  # Service
    MARCHANDISE = "marchandise"  # Goods for resale
    MATIERE_PREMIERE = "matiere_premiere"  # Raw materials
    FOURNITURE = "fourniture"  # Supplies


class ContractType(str, PyEnum):
    """Type of recurring contract."""
    ABONNEMENT_SAAS = "abonnement_saas"
    LEASING_VOITURE = "leasing_voiture"
    ASSURANCE = "assurance"
    LOCATION = "location"
    TELECOM = "telecom"
    MAINTENANCE = "maintenance"
    AUTRE = "autre"


class ContractPeriodicity(str, PyEnum):
    """Contract payment periodicity."""
    MENSUEL = "mensuel"
    TRIMESTRIEL = "trimestriel"
    SEMESTRIEL = "semestriel"
    ANNUEL = "annuel"


class PaymentMethod(str, PyEnum):
    """Payment method."""
    VIREMENT = "virement"
    DOMICILIATION = "domiciliation"
    CARTE = "carte"
    ESPECES = "especes"
    CHEQUE = "cheque"
    PAYPAL = "paypal"


class PurchaseStatus(str, PyEnum):
    """Purchase status."""
    BROUILLON = "brouillon"
    VALIDE = "valide"
    PAYE = "paye"
    ANNULE = "annule"


class AssetType(str, PyEnum):
    """Type of fixed asset."""
    MACHINE = "machine"
    VEHICULE = "vehicule"
    MOBILIER = "mobilier"
    INFORMATIQUE = "informatique"
    IMMOBILIER = "immobilier"
    LOGICIEL = "logiciel"
    AUTRE = "autre"


class DepreciationMethod(str, PyEnum):
    """Depreciation method."""
    LINEAIRE = "lineaire"
    DEGRESSIF = "degressif"


class VehicleType(str, PyEnum):
    """Vehicle type for car-related purchases."""
    THERMIQUE = "thermique"
    HYBRIDE = "hybride"
    ELECTRIQUE = "electrique"


class PurchaseCategory(Base):
    """Purchase category with VAT and fiscal deductibility rules."""
    __tablename__ = "purchase_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Purchase type
    purchase_type = Column(Enum(PurchaseType), default=PurchaseType.DEPENSE)

    # Belgian PCMN account (Plan Comptable Minimum Normalisé)
    pcmn_account = Column(String(20), nullable=True)  # e.g., "600", "61", "613", "24"
    pcmn_label = Column(String(255), nullable=True)  # Account label

    # VAT settings
    default_vat_rate = Column(Numeric(5, 2), default=21.00)  # 21%, 12%, 6%, 0%
    default_vat_deductible_rate = Column(Numeric(5, 2), default=100.00)  # % of VAT that's deductible

    # Fiscal deductibility (for income tax)
    default_fiscal_deductible_rate = Column(Numeric(5, 2), default=100.00)  # % deductible for taxes

    # Investment rules
    is_potential_investment = Column(Boolean, default=False)
    investment_threshold_htva = Column(Numeric(10, 2), default=1000.00)  # Threshold in € HTVA

    # Default depreciation settings (for investments)
    default_depreciation_years = Column(Integer, nullable=True)
    default_depreciation_method = Column(Enum(DepreciationMethod), default=DepreciationMethod.LINEAIRE)
    default_asset_type = Column(Enum(AssetType), nullable=True)

    # Active flag
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    purchases = relationship("Purchase", back_populates="category")
    contracts = relationship("PurchaseContract", back_populates="category")


class PurchaseContract(Base):
    """Recurring purchase contract (subscriptions, leasing, etc.)."""
    __tablename__ = "purchase_contracts"

    id = Column(Integer, primary_key=True, index=True)

    # References
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("purchase_categories.id"), nullable=False)

    # Contract details
    contract_type = Column(Enum(ContractType), default=ContractType.AUTRE)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)  # Contract reference number

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # Billing
    periodicity = Column(Enum(ContractPeriodicity), default=ContractPeriodicity.MENSUEL)
    amount_htva = Column(Numeric(10, 2), nullable=False)
    vat_rate = Column(Numeric(5, 2), default=21.00)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.DOMICILIATION)
    billing_day = Column(Integer, default=1)  # Day of month for billing

    # Vehicle-specific (for car leasing)
    vehicle_type = Column(Enum(VehicleType), nullable=True)
    vehicle_co2 = Column(Integer, nullable=True)  # g/km
    vehicle_registration = Column(String(20), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    next_billing_date = Column(Date, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", backref="purchase_contracts")
    category = relationship("PurchaseCategory", back_populates="contracts")
    purchases = relationship("Purchase", back_populates="contract")


class Purchase(Base):
    """Individual purchase / supplier invoice."""
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)

    # References
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("purchase_categories.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("purchase_contracts.id"), nullable=True)

    # Purchase details
    purchase_date = Column(Date, nullable=False)
    supplier_invoice_number = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)

    # Amounts
    amount_htva = Column(Numeric(10, 2), nullable=False)
    vat_rate = Column(Numeric(5, 2), default=21.00)
    vat_amount = Column(Numeric(10, 2), nullable=False)  # Total VAT

    # VAT deductibility
    vat_deductible_rate = Column(Numeric(5, 2), default=100.00)  # % of VAT deductible
    vat_deductible_amount = Column(Numeric(10, 2), nullable=False)
    vat_non_deductible_amount = Column(Numeric(10, 2), nullable=False)

    # Fiscal deductibility
    fiscal_deductible_rate = Column(Numeric(5, 2), default=100.00)

    # Accounting
    pcmn_account = Column(String(20), nullable=True)  # Can override category default

    # Investment flag
    is_investment = Column(Boolean, default=False)
    fixed_asset_id = Column(Integer, ForeignKey("fixed_assets.id"), nullable=True)

    # Payment tracking
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_date = Column(Date, nullable=True)
    payment_reference = Column(String(100), nullable=True)
    status = Column(Enum(PurchaseStatus), default=PurchaseStatus.BROUILLON)

    # Document storage
    document_path = Column(String(500), nullable=True)  # Path to uploaded invoice

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", backref="purchases")
    category = relationship("PurchaseCategory", back_populates="purchases")
    contract = relationship("PurchaseContract", back_populates="purchases")
    fixed_asset = relationship("FixedAsset", back_populates="purchase", uselist=False)

    @property
    def amount_ttc(self) -> Decimal:
        """Total amount including VAT."""
        return self.amount_htva + self.vat_amount


class FixedAsset(Base):
    """Fixed asset / investment with depreciation tracking."""
    __tablename__ = "fixed_assets"

    id = Column(Integer, primary_key=True, index=True)

    # Link to purchase
    # Note: purchase_id foreign key is defined in Purchase model

    # Asset details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    asset_type = Column(Enum(AssetType), default=AssetType.AUTRE)

    # Accounting
    pcmn_account = Column(String(20), nullable=True)  # Class 2x accounts
    pcmn_depreciation_account = Column(String(20), nullable=True)  # Class 63x for depreciation

    # Values
    acquisition_value = Column(Numeric(10, 2), nullable=False)
    residual_value = Column(Numeric(10, 2), default=0)  # Value at end of depreciation

    # Depreciation
    service_start_date = Column(Date, nullable=False)
    depreciation_years = Column(Integer, nullable=False)
    depreciation_method = Column(Enum(DepreciationMethod), default=DepreciationMethod.LINEAIRE)

    # Vehicle-specific
    vehicle_type = Column(Enum(VehicleType), nullable=True)
    vehicle_co2 = Column(Integer, nullable=True)
    vehicle_registration = Column(String(20), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    disposal_date = Column(Date, nullable=True)
    disposal_value = Column(Numeric(10, 2), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    purchase = relationship("Purchase", back_populates="fixed_asset")
    depreciation_entries = relationship("DepreciationEntry", back_populates="asset", cascade="all, delete-orphan")

    @property
    def annual_depreciation(self) -> Decimal:
        """Calculate annual depreciation amount."""
        if self.depreciation_method == DepreciationMethod.LINEAIRE:
            depreciable = self.acquisition_value - (self.residual_value or 0)
            return depreciable / self.depreciation_years
        return Decimal(0)

    @property
    def current_book_value(self) -> Decimal:
        """Calculate current book value based on depreciation entries."""
        total_depreciated = sum(
            entry.amount for entry in self.depreciation_entries
            if entry.is_posted
        )
        return self.acquisition_value - total_depreciated


class DepreciationEntry(Base):
    """Individual depreciation entry for a fixed asset."""
    __tablename__ = "depreciation_entries"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("fixed_assets.id"), nullable=False)

    # Period
    fiscal_year = Column(Integer, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Amounts
    amount = Column(Numeric(10, 2), nullable=False)
    cumulative_amount = Column(Numeric(10, 2), nullable=False)
    book_value_after = Column(Numeric(10, 2), nullable=False)

    # Status
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    asset = relationship("FixedAsset", back_populates="depreciation_entries")
