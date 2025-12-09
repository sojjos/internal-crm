"""Integration models for external services (Belcotax, Caseware, accounting imports)."""
from datetime import datetime, date
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Text, Boolean,
    ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class IntegrationStatus(str, Enum):
    """Integration status."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BelcotaxFormType(str, Enum):
    """Belcotax form types."""
    FICHE_281_10 = "281_10"  # Salaires
    FICHE_281_20 = "281_20"  # Administrateurs
    FICHE_281_30 = "281_30"  # Honoraires
    FICHE_281_50 = "281_50"  # Commissions, etc.


class ImportSourceType(str, Enum):
    """Accounting import source types."""
    WINBOOKS = "WINBOOKS"
    BOB = "BOB50"
    EXACT = "EXACT"
    SAGE = "SAGE"
    HORUS = "HORUS"
    POPSY = "POPSY"
    CSV_GENERIC = "CSV_GENERIC"
    CODA = "CODA"  # Belgian bank format


class ExternalIntegration(Base):
    """Configuration for external service integrations."""
    __tablename__ = "external_integrations"

    id = Column(Integer, primary_key=True, index=True)

    # Integration info
    name = Column(String(100), nullable=False)
    service_type = Column(String(50), nullable=False)  # belcotax, caseware, biztax, etc.
    is_active = Column(Boolean, default=False)

    # API configuration
    api_url = Column(String(500), nullable=True)
    api_key = Column(String(500), nullable=True)
    api_secret = Column(String(500), nullable=True)
    certificate_path = Column(String(500), nullable=True)

    # Authentication
    username = Column(String(255), nullable=True)
    password_encrypted = Column(String(500), nullable=True)  # Encrypted storage
    token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Configuration
    config = Column(JSON, nullable=True)

    # Testing
    test_mode = Column(Boolean, default=True)
    last_test_date = Column(DateTime, nullable=True)
    last_test_success = Column(Boolean, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ExternalIntegration {self.name}>"


class BelcotaxDeclaration(Base):
    """Belcotaxonweb declarations."""
    __tablename__ = "belcotax_declarations"

    id = Column(Integer, primary_key=True, index=True)

    # Declaration info
    reference = Column(String(50), unique=True, nullable=False)
    fiscal_year = Column(Integer, nullable=False)  # Income year
    form_type = Column(SQLEnum(BelcotaxFormType), nullable=False)
    status = Column(SQLEnum(IntegrationStatus), default=IntegrationStatus.PENDING)

    # Declarant info
    enterprise_number = Column(String(20), nullable=False)
    declarant_name = Column(String(255), nullable=False)

    # Submission
    submission_date = Column(DateTime, nullable=True)
    submission_reference = Column(String(100), nullable=True)
    acknowledgment_number = Column(String(100), nullable=True)

    # Response
    response_date = Column(DateTime, nullable=True)
    response_status = Column(String(50), nullable=True)
    error_messages = Column(JSON, nullable=True)

    # Files
    xml_file_path = Column(String(500), nullable=True)
    acknowledgment_file_path = Column(String(500), nullable=True)

    # Summary
    total_fiches = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    total_tax_withheld = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    fiches = relationship("BelcotaxFiche", back_populates="declaration", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BelcotaxDeclaration {self.reference}>"


class BelcotaxFiche(Base):
    """Individual fiche for Belcotax declaration."""
    __tablename__ = "belcotax_fiches"

    id = Column(Integer, primary_key=True, index=True)
    declaration_id = Column(Integer, ForeignKey("belcotax_declarations.id"), nullable=False)

    # Beneficiary info
    beneficiary_type = Column(String(20), nullable=False)  # PP (personne physique) or PM
    national_number = Column(String(20), nullable=True)  # For individuals
    enterprise_number = Column(String(20), nullable=True)  # For companies
    name = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=True)
    address_street = Column(String(255), nullable=True)
    address_postal_code = Column(String(20), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_country = Column(String(10), default="BE")

    # Amounts (depending on form type)
    gross_amount = Column(Float, default=0.0)  # Montant brut
    tax_withheld = Column(Float, default=0.0)  # Precompte retenu
    net_amount = Column(Float, default=0.0)  # Montant net

    # Additional fields for specific form types
    # 281.10 - Salaries
    professional_expenses = Column(Float, nullable=True)
    social_contributions = Column(Float, nullable=True)

    # 281.20 - Administrators
    attendance_fees = Column(Float, nullable=True)  # Jetons de presence
    profit_sharing = Column(Float, nullable=True)  # Tantièmes

    # 281.30 - Fees
    service_type = Column(String(100), nullable=True)

    # 281.50 - Commissions
    commission_type = Column(String(100), nullable=True)

    # Validation
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(JSON, nullable=True)

    # Source reference
    source_document = Column(String(255), nullable=True)  # Invoice/payslip reference

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    declaration = relationship("BelcotaxDeclaration", back_populates="fiches")

    def __repr__(self):
        return f"<BelcotaxFiche {self.name}>"


class CasewareProject(Base):
    """Caseware Cloud project integration."""
    __tablename__ = "caseware_projects"

    id = Column(Integer, primary_key=True, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=True)

    # Project info
    reference = Column(String(50), unique=True, nullable=False)
    caseware_project_id = Column(String(100), nullable=True)  # ID in Caseware
    name = Column(String(255), nullable=False)
    status = Column(SQLEnum(IntegrationStatus), default=IntegrationStatus.PENDING)

    # Client info (from Caseware)
    client_name = Column(String(255), nullable=True)
    client_enterprise_number = Column(String(20), nullable=True)

    # Sync info
    last_sync_date = Column(DateTime, nullable=True)
    last_sync_status = Column(String(50), nullable=True)
    sync_errors = Column(JSON, nullable=True)

    # Data mappings
    account_mapping = Column(JSON, nullable=True)  # Map local accounts to Caseware

    # Working papers
    working_papers_synced = Column(Boolean, default=False)
    trial_balance_synced = Column(Boolean, default=False)
    adjustments_synced = Column(Boolean, default=False)

    # Files
    export_file_path = Column(String(500), nullable=True)
    import_file_path = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sync_logs = relationship("CasewareSyncLog", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CasewareProject {self.reference}>"


class CasewareSyncLog(Base):
    """Sync log for Caseware operations."""
    __tablename__ = "caseware_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("caseware_projects.id"), nullable=False)

    # Sync info
    sync_type = Column(String(50), nullable=False)  # export, import, full_sync
    status = Column(SQLEnum(IntegrationStatus), nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Details
    records_processed = Column(Integer, default=0)
    records_success = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Errors
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # User who initiated
    initiated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    project = relationship("CasewareProject", back_populates="sync_logs")

    def __repr__(self):
        return f"<CasewareSyncLog {self.id}>"


class AccountingImport(Base):
    """Accounting data imports from external software."""
    __tablename__ = "accounting_imports"

    id = Column(Integer, primary_key=True, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=True)

    # Import info
    reference = Column(String(50), unique=True, nullable=False)
    source_type = Column(SQLEnum(ImportSourceType), nullable=False)
    status = Column(SQLEnum(IntegrationStatus), default=IntegrationStatus.PENDING)

    # File info
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_encoding = Column(String(20), default="UTF-8")

    # Import period
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)

    # Mapping
    column_mapping = Column(JSON, nullable=True)  # Map file columns to system fields
    account_mapping = Column(JSON, nullable=True)  # Map external accounts to PCMN

    # Processing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Results
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    success_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    duplicate_rows = Column(Integer, default=0)

    # Errors
    errors = Column(JSON, nullable=True)

    # Import summary
    summary = Column(JSON, nullable=True)  # Totals by account, etc.

    # User
    imported_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entries = relationship("ImportedAccountingEntry", back_populates="import_batch", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AccountingImport {self.reference}>"


class ImportedAccountingEntry(Base):
    """Individual accounting entries from import."""
    __tablename__ = "imported_accounting_entries"

    id = Column(Integer, primary_key=True, index=True)
    import_id = Column(Integer, ForeignKey("accounting_imports.id"), nullable=False)

    # Entry identification
    row_number = Column(Integer, nullable=False)
    external_reference = Column(String(100), nullable=True)

    # Date
    entry_date = Column(Date, nullable=False)
    period = Column(String(10), nullable=True)  # YYYYMM

    # Journal
    journal_code = Column(String(20), nullable=True)
    journal_name = Column(String(100), nullable=True)

    # Account
    account_number = Column(String(20), nullable=False)
    account_name = Column(String(255), nullable=True)
    mapped_pcmn_account = Column(String(20), nullable=True)

    # Amounts
    debit_amount = Column(Float, default=0.0)
    credit_amount = Column(Float, default=0.0)

    # Description
    description = Column(String(500), nullable=True)
    document_reference = Column(String(100), nullable=True)

    # Third party
    third_party_code = Column(String(50), nullable=True)
    third_party_name = Column(String(255), nullable=True)
    vat_number = Column(String(50), nullable=True)

    # VAT
    vat_code = Column(String(20), nullable=True)
    vat_base = Column(Float, nullable=True)
    vat_amount = Column(Float, nullable=True)

    # Status
    is_processed = Column(Boolean, default=False)
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(JSON, nullable=True)
    is_duplicate = Column(Boolean, default=False)

    # Created record reference
    created_invoice_id = Column(Integer, nullable=True)
    created_expense_id = Column(Integer, nullable=True)

    # Relationships
    import_batch = relationship("AccountingImport", back_populates="entries")

    def __repr__(self):
        return f"<ImportedAccountingEntry Row {self.row_number}>"


class CODAImport(Base):
    """CODA (Belgian bank statement) imports."""
    __tablename__ = "coda_imports"

    id = Column(Integer, primary_key=True, index=True)
    bank_account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=True)

    # Import info
    reference = Column(String(50), unique=True, nullable=False)
    status = Column(SQLEnum(IntegrationStatus), default=IntegrationStatus.PENDING)

    # File info
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)

    # CODA header info
    coda_version = Column(String(10), nullable=True)
    creation_date = Column(Date, nullable=True)
    bank_id = Column(String(20), nullable=True)  # BIC
    account_number = Column(String(50), nullable=True)  # IBAN

    # Statement info
    statement_number = Column(Integer, nullable=True)
    statement_date = Column(Date, nullable=True)
    opening_balance = Column(Float, nullable=True)
    closing_balance = Column(Float, nullable=True)

    # Processing
    processed_at = Column(DateTime, nullable=True)
    total_movements = Column(Integer, default=0)
    matched_movements = Column(Integer, default=0)
    unmatched_movements = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    movements = relationship("CODAMovement", back_populates="coda_import", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CODAImport {self.reference}>"


class CODAMovement(Base):
    """Individual CODA bank movements."""
    __tablename__ = "coda_movements"

    id = Column(Integer, primary_key=True, index=True)
    coda_import_id = Column(Integer, ForeignKey("coda_imports.id"), nullable=False)

    # Movement info
    sequence_number = Column(Integer, nullable=False)
    movement_date = Column(Date, nullable=False)
    value_date = Column(Date, nullable=True)

    # Amount
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="EUR")

    # Transaction type
    transaction_code = Column(String(10), nullable=True)
    transaction_family = Column(String(10), nullable=True)
    transaction_type_description = Column(String(255), nullable=True)

    # Counterparty
    counterparty_account = Column(String(50), nullable=True)
    counterparty_name = Column(String(255), nullable=True)
    counterparty_bic = Column(String(20), nullable=True)

    # Communication
    communication = Column(Text, nullable=True)
    structured_communication = Column(String(50), nullable=True)  # +++xxx/xxxx/xxxxx+++

    # Matching
    is_matched = Column(Boolean, default=False)
    matched_invoice_id = Column(Integer, nullable=True)
    matched_expense_id = Column(Integer, nullable=True)
    matched_type = Column(String(50), nullable=True)  # invoice, expense, manual

    # Reconciliation
    is_reconciled = Column(Boolean, default=False)
    reconciled_at = Column(DateTime, nullable=True)
    reconciled_by_id = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    coda_import = relationship("CODAImport", back_populates="movements")

    def __repr__(self):
        return f"<CODAMovement {self.sequence_number}>"


# Import column mappings for different accounting software
IMPORT_COLUMN_MAPPINGS = {
    "WINBOOKS": {
        "JRNL": "journal_code",
        "YEAR": "fiscal_year",
        "MONTH": "period",
        "DOC": "document_reference",
        "DATE": "entry_date",
        "ACCOUNT": "account_number",
        "AMOUNTEUR": "amount",
        "DC": "debit_credit",
        "COMMENT": "description",
        "CUSTOMER": "third_party_code",
        "VATCODE": "vat_code",
    },
    "BOB50": {
        "Journal": "journal_code",
        "Piece": "document_reference",
        "Date": "entry_date",
        "Compte": "account_number",
        "Debit": "debit_amount",
        "Credit": "credit_amount",
        "Libelle": "description",
        "Client": "third_party_code",
        "TVA": "vat_code",
    },
    "EXACT": {
        "JournalCode": "journal_code",
        "EntryNumber": "document_reference",
        "Date": "entry_date",
        "GLAccount": "account_number",
        "Debit": "debit_amount",
        "Credit": "credit_amount",
        "Description": "description",
        "AccountCode": "third_party_code",
    },
    "CSV_GENERIC": {
        "date": "entry_date",
        "account": "account_number",
        "debit": "debit_amount",
        "credit": "credit_amount",
        "description": "description",
        "reference": "document_reference",
    },
}

# Belgian bank transaction codes (CODA)
CODA_TRANSACTION_CODES = {
    "01": "Virement national",
    "03": "Virement SEPA",
    "05": "Paiement Bancontact",
    "07": "Domiciliation",
    "11": "Cheque",
    "13": "Virement international",
    "35": "Frais bancaires",
    "37": "Interets",
    "41": "Retrait especes",
    "43": "Versement especes",
    "80": "Divers",
}
