"""Fiscal module models for Belgian corporate tax (ISoc) and Biztax integration."""
from datetime import datetime, date
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Text, Boolean,
    ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class TaxDeclarationStatus(str, Enum):
    """Tax declaration status."""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    CALCULATED = "CALCULATED"
    VALIDATED = "VALIDATED"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class TaxDeclarationType(str, Enum):
    """Types of tax declarations."""
    ISOC = "ISOC"  # Impot des societes
    TVA = "TVA"  # TVA periodique
    PRECOMPTE_PRO = "PRECOMPTE_PRO"  # Precompte professionnel
    PRECOMPTE_MOB = "PRECOMPTE_MOB"  # Precompte mobilier


class BiztaxStatus(str, Enum):
    """Biztax submission status."""
    NOT_SUBMITTED = "NOT_SUBMITTED"
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class TaxDeclaration(Base):
    """Tax declaration / Declaration fiscale."""
    __tablename__ = "tax_declarations"

    id = Column(Integer, primary_key=True, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Declaration info
    reference = Column(String(50), unique=True, nullable=False)  # ISOC-2024-001
    declaration_type = Column(SQLEnum(TaxDeclarationType), nullable=False)
    status = Column(SQLEnum(TaxDeclarationStatus), default=TaxDeclarationStatus.DRAFT)

    # Period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)

    # Enterprise info
    enterprise_number = Column(String(20), nullable=False)  # Numero BCE
    company_name = Column(String(255))

    # Biztax integration
    biztax_status = Column(SQLEnum(BiztaxStatus), default=BiztaxStatus.NOT_SUBMITTED)
    biztax_submission_date = Column(DateTime, nullable=True)
    biztax_reference = Column(String(100), nullable=True)
    biztax_receipt_path = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)

    # Relationships
    isoc_calculation = relationship("ISocCalculation", back_populates="declaration", uselist=False, cascade="all, delete-orphan")
    tax_items = relationship("TaxDeclarationItem", back_populates="declaration", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TaxDeclaration {self.reference}>"


class ISocCalculation(Base):
    """ISoc (Corporate Tax) calculation details."""
    __tablename__ = "isoc_calculations"

    id = Column(Integer, primary_key=True, index=True)
    declaration_id = Column(Integer, ForeignKey("tax_declarations.id"), nullable=False)

    # Base calculation - Mouvement des reserves
    accounting_result = Column(Float, default=0.0)  # Resultat comptable

    # Depenses non admises (DNA)
    dna_total = Column(Float, default=0.0)
    dna_details = Column(JSON, nullable=True)  # Detail des DNA

    # Reductions
    deduction_rdt = Column(Float, default=0.0)  # Revenus definitivement taxes
    deduction_innovation = Column(Float, default=0.0)  # Deduction pour innovation
    deduction_investment = Column(Float, default=0.0)  # Deduction pour investissement
    other_deductions = Column(Float, default=0.0)

    # Pertes anterieures
    carried_forward_losses = Column(Float, default=0.0)  # Pertes reportees
    losses_used = Column(Float, default=0.0)  # Pertes utilisees

    # Tax base and calculation
    taxable_base = Column(Float, default=0.0)  # Base imposable

    # Belgian corporate tax rates (2024)
    # Standard rate: 25%
    # SME reduced rate: 20% on first 100,000 EUR
    standard_rate = Column(Float, default=25.0)
    sme_rate = Column(Float, default=20.0)
    sme_threshold = Column(Float, default=100000.0)

    # Tax amounts
    tax_at_standard_rate = Column(Float, default=0.0)
    tax_at_sme_rate = Column(Float, default=0.0)
    total_tax = Column(Float, default=0.0)

    # Prepayments (Versements anticipes)
    prepayments_q1 = Column(Float, default=0.0)  # VA1 (10/04)
    prepayments_q2 = Column(Float, default=0.0)  # VA2 (10/07)
    prepayments_q3 = Column(Float, default=0.0)  # VA3 (10/10)
    prepayments_q4 = Column(Float, default=0.0)  # VA4 (20/12)
    total_prepayments = Column(Float, default=0.0)

    # Prepayment bonus calculation
    prepayment_bonus = Column(Float, default=0.0)

    # Final balance
    tax_balance = Column(Float, default=0.0)  # A payer ou a recuperer

    # SME criteria check
    is_sme = Column(Boolean, default=True)
    sme_criteria = Column(JSON, nullable=True)  # Details des criteres PME

    # Calculation date
    calculated_at = Column(DateTime, nullable=True)

    # Relationships
    declaration = relationship("TaxDeclaration", back_populates="isoc_calculation")

    def calculate_tax(self):
        """Calculate corporate tax with Belgian rules."""
        if self.taxable_base <= 0:
            self.total_tax = 0
            self.tax_at_standard_rate = 0
            self.tax_at_sme_rate = 0
            return

        if self.is_sme and self.taxable_base > 0:
            # SME reduced rate on first 100,000 EUR
            sme_portion = min(self.taxable_base, self.sme_threshold)
            standard_portion = max(0, self.taxable_base - self.sme_threshold)

            self.tax_at_sme_rate = sme_portion * (self.sme_rate / 100)
            self.tax_at_standard_rate = standard_portion * (self.standard_rate / 100)
        else:
            # Standard rate only
            self.tax_at_sme_rate = 0
            self.tax_at_standard_rate = self.taxable_base * (self.standard_rate / 100)

        self.total_tax = self.tax_at_sme_rate + self.tax_at_standard_rate
        self.total_prepayments = (
            self.prepayments_q1 + self.prepayments_q2 +
            self.prepayments_q3 + self.prepayments_q4
        )
        self.tax_balance = self.total_tax - self.total_prepayments - self.prepayment_bonus

    def __repr__(self):
        return f"<ISocCalculation for declaration {self.declaration_id}>"


class TaxDeclarationItem(Base):
    """Individual items/codes in a tax declaration."""
    __tablename__ = "tax_declaration_items"

    id = Column(Integer, primary_key=True, index=True)
    declaration_id = Column(Integer, ForeignKey("tax_declarations.id"), nullable=False)

    # Tax form code (e.g., 1001, 1002, etc. from ISoc form)
    code = Column(String(20), nullable=False)
    label = Column(String(255), nullable=False)
    section = Column(String(100), nullable=True)

    # Value
    amount = Column(Float, default=0.0)

    # Source
    is_calculated = Column(Boolean, default=False)
    source_description = Column(Text, nullable=True)

    # Order
    display_order = Column(Integer, default=0)

    # Relationships
    declaration = relationship("TaxDeclaration", back_populates="tax_items")

    def __repr__(self):
        return f"<TaxDeclarationItem {self.code}>"


class TaxMapping(Base):
    """Mapping between accounting accounts and tax codes."""
    __tablename__ = "tax_mappings"

    id = Column(Integer, primary_key=True, index=True)

    # Source account
    pcmn_account = Column(String(20), nullable=False)
    pcmn_label = Column(String(255), nullable=True)

    # Tax destination
    declaration_type = Column(SQLEnum(TaxDeclarationType), nullable=False)
    tax_code = Column(String(20), nullable=False)
    tax_label = Column(String(255), nullable=True)

    # Mapping rules
    coefficient = Column(Float, default=1.0)  # Multiplier
    is_deductible = Column(Boolean, default=True)
    dna_percentage = Column(Float, default=0.0)  # % DNA if not fully deductible

    # Active
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TaxMapping {self.pcmn_account} -> {self.tax_code}>"


class Prepayment(Base):
    """Tax prepayments / Versements anticipes."""
    __tablename__ = "tax_prepayments"

    id = Column(Integer, primary_key=True, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Prepayment info
    quarter = Column(Integer, nullable=False)  # 1, 2, 3, or 4
    reference = Column(String(50))  # VA-2024-Q1
    due_date = Column(Date, nullable=False)
    payment_date = Column(Date, nullable=True)

    # Amount
    estimated_tax = Column(Float, default=0.0)
    amount_paid = Column(Float, default=0.0)

    # Bonus calculation (2024 rates)
    # VA1: 9%, VA2: 7.5%, VA3: 6%, VA4: 4.5%
    bonus_rate = Column(Float, default=0.0)
    bonus_amount = Column(Float, default=0.0)

    # Payment proof
    payment_reference = Column(String(100), nullable=True)
    bank_statement_ref = Column(String(100), nullable=True)

    # Status
    is_paid = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Prepayment {self.reference}>"


# Belgian ISoc form structure (simplified)
ISOC_FORM_STRUCTURE = {
    "IDENTIFICATION": [
        ("1001", "Denomination"),
        ("1002", "Forme juridique"),
        ("1003", "Numero d'entreprise"),
        ("1004", "Adresse du siege social"),
    ],
    "MOUVEMENT DES RESERVES": [
        ("1101", "Reserves au debut de la periode imposable"),
        ("1102", "Reserves a la fin de la periode imposable"),
        ("1103", "Mouvement des reserves"),
        ("1104", "Dividendes distribues"),
        ("1105", "Benefice comptable de l'exercice"),
    ],
    "DEPENSES NON ADMISES": [
        ("1201", "Impots non deductibles"),
        ("1202", "Amendes et penalites"),
        ("1203", "Liberalites"),
        ("1204", "Frais de voiture (partie non deductible)"),
        ("1205", "Frais de restaurant (31%)"),
        ("1206", "Frais de reception"),
        ("1207", "Avantages sociaux"),
        ("1208", "Interets excessifs"),
        ("1209", "Autres DNA"),
        ("1210", "Total des DNA"),
    ],
    "REVENUS DEFINITVEMENT TAXES (RDT)": [
        ("1301", "Dividendes percus"),
        ("1302", "RDT deductibles"),
    ],
    "DEDUCTIONS": [
        ("1401", "Deduction pour investissement"),
        ("1402", "Deduction pour innovation"),
        ("1403", "Autres deductions"),
    ],
    "PERTES ANTERIEURES": [
        ("1501", "Pertes anterieures disponibles"),
        ("1502", "Pertes utilisees"),
        ("1503", "Pertes reportees"),
    ],
    "BASE IMPOSABLE ET IMPOT": [
        ("1601", "Base imposable"),
        ("1602", "Impot au taux PME (20%)"),
        ("1603", "Impot au taux normal (25%)"),
        ("1604", "Impot total"),
        ("1605", "Versements anticipes"),
        ("1606", "Bonification VA"),
        ("1607", "Solde a payer/recuperer"),
    ],
}

# DNA (Depenses Non Admises) categories with percentages
DNA_CATEGORIES = {
    "restaurant": {"label": "Frais de restaurant", "non_deductible_pct": 31},
    "reception": {"label": "Frais de reception", "non_deductible_pct": 50},
    "voiture_essence": {"label": "Frais de voiture essence", "non_deductible_pct": 25},
    "voiture_diesel": {"label": "Frais de voiture diesel", "non_deductible_pct": 40},
    "amende": {"label": "Amendes", "non_deductible_pct": 100},
    "cadeau": {"label": "Cadeaux d'affaires > 125 EUR", "non_deductible_pct": 100},
    "vetement": {"label": "Vetements non professionnels", "non_deductible_pct": 100},
}

# Prepayment bonus rates (2024)
PREPAYMENT_BONUS_RATES = {
    1: 9.0,   # VA1 - 10 avril
    2: 7.5,   # VA2 - 10 juillet
    3: 6.0,   # VA3 - 10 octobre
    4: 4.5,   # VA4 - 20 decembre
}
