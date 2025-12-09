"""Annual Accounts models for Belgian BNB/XBRL filing."""
from datetime import datetime, date
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Text, Boolean,
    ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class AccountingSchemaType(str, Enum):
    """Belgian accounting schema types."""
    COMPLETE = "COMPLETE"  # Schema complet
    ABBREVIATED = "ABBREVIATED"  # Schema abrege
    MICRO = "MICRO"  # Micro-schema


class AnnualAccountStatus(str, Enum):
    """Annual account filing status."""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    VALIDATED = "VALIDATED"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class FiscalYear(Base):
    """Fiscal year / Exercise comptable."""
    __tablename__ = "fiscal_years"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # e.g., "2024"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime, nullable=True)
    closed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Schema type for this year
    schema_type = Column(SQLEnum(AccountingSchemaType), default=AccountingSchemaType.ABBREVIATED)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    annual_accounts = relationship("AnnualAccount", back_populates="fiscal_year")

    def __repr__(self):
        return f"<FiscalYear {self.name}>"


class AnnualAccount(Base):
    """Annual accounts / Comptes annuels."""
    __tablename__ = "annual_accounts"

    id = Column(Integer, primary_key=True, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Filing info
    reference = Column(String(50), unique=True, nullable=False)  # CA-2024-001
    status = Column(SQLEnum(AnnualAccountStatus), default=AnnualAccountStatus.DRAFT)
    schema_type = Column(SQLEnum(AccountingSchemaType), nullable=False)

    # BNB filing
    bnb_enterprise_number = Column(String(20))  # Numero d'entreprise
    bnb_filing_date = Column(Date, nullable=True)
    bnb_filing_reference = Column(String(100), nullable=True)
    xbrl_file_path = Column(String(500), nullable=True)

    # Approval info
    general_assembly_date = Column(Date, nullable=True)  # Date AG
    board_approval_date = Column(Date, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="annual_accounts")
    balance_sheet_items = relationship("BalanceSheetItem", back_populates="annual_account", cascade="all, delete-orphan")
    income_statement_items = relationship("IncomeStatementItem", back_populates="annual_account", cascade="all, delete-orphan")
    notes = relationship("AnnualAccountNote", back_populates="annual_account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AnnualAccount {self.reference}>"


class BalanceSheetItem(Base):
    """Balance sheet line item / Poste du bilan."""
    __tablename__ = "balance_sheet_items"

    id = Column(Integer, primary_key=True, index=True)
    annual_account_id = Column(Integer, ForeignKey("annual_accounts.id"), nullable=False)

    # Belgian PCMN account structure
    rubric_code = Column(String(20), nullable=False)  # e.g., "10", "20/28", "40/41"
    rubric_name = Column(String(255), nullable=False)
    section = Column(String(50), nullable=False)  # ACTIF, PASSIF
    subsection = Column(String(100), nullable=True)  # Actifs immobilises, Actifs circulants, etc.

    # Amounts
    current_year_amount = Column(Float, default=0.0)
    previous_year_amount = Column(Float, default=0.0)

    # XBRL mapping
    xbrl_element = Column(String(255), nullable=True)

    # Order for display
    display_order = Column(Integer, default=0)

    # Relationships
    annual_account = relationship("AnnualAccount", back_populates="balance_sheet_items")

    def __repr__(self):
        return f"<BalanceSheetItem {self.rubric_code} - {self.rubric_name}>"


class IncomeStatementItem(Base):
    """Income statement line item / Poste du compte de resultats."""
    __tablename__ = "income_statement_items"

    id = Column(Integer, primary_key=True, index=True)
    annual_account_id = Column(Integer, ForeignKey("annual_accounts.id"), nullable=False)

    # Belgian PCMN structure
    rubric_code = Column(String(20), nullable=False)  # e.g., "70", "60/61", "9901"
    rubric_name = Column(String(255), nullable=False)
    section = Column(String(100), nullable=True)  # Produits d'exploitation, Charges, etc.

    # Amounts
    current_year_amount = Column(Float, default=0.0)
    previous_year_amount = Column(Float, default=0.0)

    # XBRL mapping
    xbrl_element = Column(String(255), nullable=True)

    # Order
    display_order = Column(Integer, default=0)

    # Relationships
    annual_account = relationship("AnnualAccount", back_populates="income_statement_items")

    def __repr__(self):
        return f"<IncomeStatementItem {self.rubric_code}>"


class AnnualAccountNote(Base):
    """Annexes aux comptes annuels."""
    __tablename__ = "annual_account_notes"

    id = Column(Integer, primary_key=True, index=True)
    annual_account_id = Column(Integer, ForeignKey("annual_accounts.id"), nullable=False)

    note_code = Column(String(20), nullable=False)  # e.g., "5.1", "5.2.1"
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)

    # Structured data for specific notes
    structured_data = Column(JSON, nullable=True)

    # Order
    display_order = Column(Integer, default=0)

    # Relationships
    annual_account = relationship("AnnualAccount", back_populates="notes")

    def __repr__(self):
        return f"<AnnualAccountNote {self.note_code}>"


class AccountMapping(Base):
    """Mapping between PCMN accounts and annual account rubrics."""
    __tablename__ = "account_mappings"

    id = Column(Integer, primary_key=True, index=True)

    # PCMN account
    pcmn_account = Column(String(20), nullable=False)  # e.g., "700000"
    pcmn_label = Column(String(255), nullable=True)

    # Balance sheet mapping
    balance_sheet_rubric = Column(String(20), nullable=True)

    # Income statement mapping
    income_statement_rubric = Column(String(20), nullable=True)

    # XBRL mapping
    xbrl_element = Column(String(255), nullable=True)

    # Active
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AccountMapping {self.pcmn_account}>"


# Belgian PCMN standard rubrics for balance sheet
BELGIAN_BALANCE_SHEET_STRUCTURE = {
    "ACTIF": {
        "ACTIFS IMMOBILISES": [
            ("20/28", "ACTIFS IMMOBILISES"),
            ("20", "Frais d'etablissement"),
            ("21", "Immobilisations incorporelles"),
            ("22/27", "Immobilisations corporelles"),
            ("22", "Terrains et constructions"),
            ("23", "Installations, machines et outillage"),
            ("24", "Mobilier et materiel roulant"),
            ("25", "Immobilisations en cours et acomptes verses"),
            ("26", "Autres immobilisations corporelles"),
            ("27", "Location-financement et droits similaires"),
            ("28", "Immobilisations financieres"),
        ],
        "ACTIFS CIRCULANTS": [
            ("29/58", "ACTIFS CIRCULANTS"),
            ("29", "Creances a plus d'un an"),
            ("3", "Stocks et commandes en cours d'execution"),
            ("30/36", "Stocks"),
            ("37", "Commandes en cours d'execution"),
            ("40/41", "Creances a un an au plus"),
            ("40", "Creances commerciales"),
            ("41", "Autres creances"),
            ("50/53", "Placements de tresorerie"),
            ("54/58", "Valeurs disponibles"),
            ("490/1", "Comptes de regularisation"),
        ],
    },
    "PASSIF": {
        "CAPITAUX PROPRES": [
            ("10/15", "CAPITAUX PROPRES"),
            ("10", "Capital"),
            ("100", "Capital souscrit"),
            ("101", "Capital non appele"),
            ("11", "Primes d'emission"),
            ("12", "Plus-values de reevaluation"),
            ("13", "Reserves"),
            ("130", "Reserve legale"),
            ("131", "Reserves indisponibles"),
            ("132", "Reserves immunisees"),
            ("133", "Reserves disponibles"),
            ("14", "Benefice/Perte reporte(e)"),
            ("15", "Subsides en capital"),
        ],
        "PROVISIONS ET IMPOTS DIFFERES": [
            ("16", "Provisions et impots differes"),
            ("160/5", "Provisions pour risques et charges"),
            ("168", "Impots differes"),
        ],
        "DETTES": [
            ("17/49", "DETTES"),
            ("17", "Dettes a plus d'un an"),
            ("170/4", "Dettes financieres"),
            ("175", "Dettes commerciales"),
            ("176", "Acomptes recus sur commandes"),
            ("178/9", "Autres dettes"),
            ("42/48", "Dettes a un an au plus"),
            ("42", "Dettes a plus d'un an echeant dans l'annee"),
            ("43", "Dettes financieres"),
            ("44", "Dettes commerciales"),
            ("45", "Dettes fiscales, salariales et sociales"),
            ("46", "Acomptes recus sur commandes"),
            ("47/48", "Autres dettes"),
            ("492/3", "Comptes de regularisation"),
        ],
    }
}

# Belgian income statement structure
BELGIAN_INCOME_STATEMENT_STRUCTURE = {
    "PRODUITS D'EXPLOITATION": [
        ("70/76A", "Produits d'exploitation"),
        ("70", "Chiffre d'affaires"),
        ("71", "Variation des stocks et des commandes en cours"),
        ("72", "Production immobilisee"),
        ("74", "Autres produits d'exploitation"),
        ("76A", "Produits d'exploitation non recurrents"),
    ],
    "CHARGES D'EXPLOITATION": [
        ("60/66A", "Charges d'exploitation"),
        ("60", "Approvisionnements et marchandises"),
        ("61", "Services et biens divers"),
        ("62", "Remunerations, charges sociales et pensions"),
        ("630", "Amortissements et reductions de valeur sur frais d'etablissement et immobilisations"),
        ("631/4", "Reductions de valeur sur stocks et creances"),
        ("635/8", "Provisions pour risques et charges"),
        ("640/8", "Autres charges d'exploitation"),
        ("66A", "Charges d'exploitation non recurrentes"),
    ],
    "RESULTAT D'EXPLOITATION": [
        ("9901", "Benefice (Perte) d'exploitation"),
    ],
    "PRODUITS FINANCIERS": [
        ("75/76B", "Produits financiers"),
        ("750/1", "Produits des immobilisations financieres"),
        ("752/9", "Produits des actifs circulants"),
        ("76B", "Produits financiers non recurrents"),
    ],
    "CHARGES FINANCIERES": [
        ("65/66B", "Charges financieres"),
        ("650", "Charges des dettes"),
        ("651", "Reductions de valeur sur actifs circulants"),
        ("652/9", "Autres charges financieres"),
        ("66B", "Charges financieres non recurrentes"),
    ],
    "RESULTAT COURANT": [
        ("9902", "Benefice (Perte) courant(e) avant impots"),
    ],
    "IMPOTS": [
        ("780", "Prelevement sur les impots differes"),
        ("680", "Transfert aux impots differes"),
        ("67/77", "Impots sur le resultat"),
    ],
    "RESULTAT DE L'EXERCICE": [
        ("9903", "Benefice (Perte) de l'exercice"),
        ("9904", "Prelevement sur les reserves"),
        ("9905", "Affectation aux reserves"),
        ("9906", "Benefice (Perte) a reporter"),
    ],
}
