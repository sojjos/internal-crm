"""Legal module models for Belgian corporate legal documents."""
from datetime import datetime, date
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Text, Boolean,
    ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class MeetingType(str, Enum):
    """Types of corporate meetings."""
    AG_ORDINAIRE = "AG_ORDINAIRE"  # Assemblee Generale Ordinaire
    AG_EXTRAORDINAIRE = "AG_EXTRAORDINAIRE"  # AG Extraordinaire
    CA = "CA"  # Conseil d'Administration
    COMITE_DIRECTION = "COMITE_DIRECTION"  # Comite de Direction
    AG_SPECIALE = "AG_SPECIALE"  # AG Speciale


class DocumentLegalStatus(str, Enum):
    """Status of legal documents."""
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    SIGNED = "SIGNED"
    FILED = "FILED"
    PUBLISHED = "PUBLISHED"


class PublicationType(str, Enum):
    """Types of publications in Moniteur Belge."""
    CONSTITUTION = "CONSTITUTION"
    MODIFICATION_STATUTS = "MODIFICATION_STATUTS"
    NOMINATION = "NOMINATION"
    DEMISSION = "DEMISSION"
    DISSOLUTION = "DISSOLUTION"
    COMPTES_ANNUELS = "COMPTES_ANNUELS"
    AUTRES = "AUTRES"


class BoardMeeting(Base):
    """Board meetings and general assemblies / PV d'assemblee."""
    __tablename__ = "board_meetings"

    id = Column(Integer, primary_key=True, index=True)

    # Meeting info
    reference = Column(String(50), unique=True, nullable=False)  # PV-AG-2024-001
    meeting_type = Column(SQLEnum(MeetingType), nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(SQLEnum(DocumentLegalStatus), default=DocumentLegalStatus.DRAFT)

    # Date and location
    meeting_date = Column(Date, nullable=False)
    meeting_time = Column(String(10), nullable=True)  # HH:MM
    location = Column(String(255), nullable=True)
    is_virtual = Column(Boolean, default=False)

    # Convocation
    convocation_date = Column(Date, nullable=True)
    convocation_sent = Column(Boolean, default=False)

    # Attendance
    quorum_required = Column(Boolean, default=True)
    quorum_reached = Column(Boolean, default=False)
    attendees = Column(JSON, nullable=True)  # List of attendees with roles

    # Content
    agenda = Column(Text, nullable=True)  # Order du jour
    minutes_content = Column(Text, nullable=True)  # Corps du PV
    decisions = Column(JSON, nullable=True)  # List of decisions taken

    # Signatures
    president_name = Column(String(255), nullable=True)
    secretary_name = Column(String(255), nullable=True)
    signed_at = Column(DateTime, nullable=True)
    signature_file_path = Column(String(500), nullable=True)

    # Filing
    filed_at_greffe = Column(Boolean, default=False)
    greffe_filing_date = Column(Date, nullable=True)
    greffe_reference = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resolutions = relationship("MeetingResolution", back_populates="meeting", cascade="all, delete-orphan")
    documents = relationship("LegalDocument", back_populates="meeting")

    def __repr__(self):
        return f"<BoardMeeting {self.reference}>"


class MeetingResolution(Base):
    """Resolutions taken during meetings."""
    __tablename__ = "meeting_resolutions"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("board_meetings.id"), nullable=False)

    # Resolution info
    resolution_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Voting
    votes_for = Column(Integer, default=0)
    votes_against = Column(Integer, default=0)
    votes_abstain = Column(Integer, default=0)
    is_adopted = Column(Boolean, default=False)

    # Execution
    requires_publication = Column(Boolean, default=False)
    execution_deadline = Column(Date, nullable=True)
    executed = Column(Boolean, default=False)
    executed_at = Column(DateTime, nullable=True)

    # Relationships
    meeting = relationship("BoardMeeting", back_populates="resolutions")

    def __repr__(self):
        return f"<MeetingResolution {self.resolution_number}>"


class LegalDocument(Base):
    """Corporate legal documents."""
    __tablename__ = "legal_documents"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("board_meetings.id"), nullable=True)

    # Document info
    reference = Column(String(50), unique=True, nullable=False)
    document_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(DocumentLegalStatus), default=DocumentLegalStatus.DRAFT)

    # Content
    content = Column(Text, nullable=True)  # Document content (can be template-based)
    template_used = Column(String(100), nullable=True)

    # File
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(20), nullable=True)  # PDF, DOCX, etc.

    # Signatures
    signatories = Column(JSON, nullable=True)  # List of required signatories
    signed_at = Column(DateTime, nullable=True)
    signed_file_path = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    meeting = relationship("BoardMeeting", back_populates="documents")

    def __repr__(self):
        return f"<LegalDocument {self.reference}>"


class ManagementReport(Base):
    """Annual management reports / Rapports de gestion."""
    __tablename__ = "management_reports"

    id = Column(Integer, primary_key=True, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Report info
    reference = Column(String(50), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(SQLEnum(DocumentLegalStatus), default=DocumentLegalStatus.DRAFT)

    # Sections content (structured)
    sections = Column(JSON, nullable=True)

    # Standard sections for Belgian management report
    situation_overview = Column(Text, nullable=True)  # Expose sur la situation
    significant_events = Column(Text, nullable=True)  # Evenements importants
    future_outlook = Column(Text, nullable=True)  # Evolution previsible
    rd_activities = Column(Text, nullable=True)  # Activites R&D
    branches = Column(Text, nullable=True)  # Succursales
    financial_instruments = Column(Text, nullable=True)  # Instruments financiers
    own_shares = Column(Text, nullable=True)  # Actions propres
    profit_distribution = Column(Text, nullable=True)  # Affectation du resultat
    corporate_governance = Column(Text, nullable=True)  # Gouvernance

    # Key figures
    key_figures = Column(JSON, nullable=True)

    # Approval
    board_approval_date = Column(Date, nullable=True)
    ag_approval_date = Column(Date, nullable=True)

    # File
    file_path = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ManagementReport {self.reference}>"


class MoniteurPublication(Base):
    """Publications in Moniteur Belge."""
    __tablename__ = "moniteur_publications"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("board_meetings.id"), nullable=True)

    # Publication info
    reference = Column(String(50), unique=True, nullable=False)
    publication_type = Column(SQLEnum(PublicationType), nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(SQLEnum(DocumentLegalStatus), default=DocumentLegalStatus.DRAFT)

    # Content
    content_fr = Column(Text, nullable=True)  # French text
    content_nl = Column(Text, nullable=True)  # Dutch text (if required)

    # Company info
    enterprise_number = Column(String(20), nullable=False)
    company_name = Column(String(255), nullable=False)
    legal_form = Column(String(50), nullable=True)

    # Filing
    filed_date = Column(Date, nullable=True)
    filing_reference = Column(String(100), nullable=True)

    # Publication
    published_date = Column(Date, nullable=True)
    publication_number = Column(String(50), nullable=True)  # Numero de publication MB
    publication_page = Column(Integer, nullable=True)

    # Cost
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    invoice_reference = Column(String(100), nullable=True)

    # File
    form_file_path = Column(String(500), nullable=True)
    publication_file_path = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MoniteurPublication {self.reference}>"


class CorporateOfficer(Base):
    """Corporate officers / Mandataires sociaux."""
    __tablename__ = "corporate_officers"

    id = Column(Integer, primary_key=True, index=True)

    # Person info
    name = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=True)
    national_registry_number = Column(String(20), nullable=True)  # Numero national
    address = Column(Text, nullable=True)

    # Or company (for legal person mandatary)
    is_legal_person = Column(Boolean, default=False)
    enterprise_number = Column(String(20), nullable=True)
    represented_by = Column(String(255), nullable=True)  # Representant permanent

    # Mandate
    function = Column(String(100), nullable=False)  # Administrateur, Gerant, etc.
    function_title = Column(String(100), nullable=True)  # President, etc.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    # Remuneration
    remuneration_type = Column(String(50), nullable=True)  # Gratuit, Remunere
    annual_remuneration = Column(Float, nullable=True)

    # Powers
    powers_description = Column(Text, nullable=True)
    signature_power = Column(String(50), nullable=True)  # Seul, conjoint

    # Publications
    nomination_published = Column(Boolean, default=False)
    nomination_publication_date = Column(Date, nullable=True)
    nomination_publication_ref = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CorporateOfficer {self.name} - {self.function}>"


class ShareRegister(Base):
    """Share register / Registre des actions."""
    __tablename__ = "share_register"

    id = Column(Integer, primary_key=True, index=True)

    # Entry info
    entry_number = Column(Integer, nullable=False)
    entry_date = Column(Date, nullable=False)
    transaction_type = Column(String(50), nullable=False)  # Souscription, Cession, etc.

    # Shareholder
    shareholder_name = Column(String(255), nullable=False)
    shareholder_address = Column(Text, nullable=True)
    shareholder_national_id = Column(String(20), nullable=True)
    is_legal_person = Column(Boolean, default=False)
    enterprise_number = Column(String(20), nullable=True)

    # Shares
    share_type = Column(String(50), nullable=False)  # Actions ordinaires, preferentielles
    number_of_shares = Column(Integer, nullable=False)
    nominal_value = Column(Float, nullable=True)
    share_numbers_from = Column(Integer, nullable=True)
    share_numbers_to = Column(Integer, nullable=True)

    # Transfer info (for cessions)
    previous_owner = Column(String(255), nullable=True)
    transfer_price = Column(Float, nullable=True)
    transfer_date = Column(Date, nullable=True)

    # Documents
    transfer_deed_path = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ShareRegister Entry {self.entry_number}>"


class UBORegister(Base):
    """UBO (Ultimate Beneficial Owners) Register."""
    __tablename__ = "ubo_register"

    id = Column(Integer, primary_key=True, index=True)

    # UBO info
    name = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=True)
    birth_date = Column(Date, nullable=True)
    nationality = Column(String(100), nullable=True)
    national_registry_number = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)

    # Beneficial ownership details
    ownership_type = Column(String(100), nullable=False)  # Direct, Indirect, Controle
    ownership_percentage = Column(Float, nullable=True)
    voting_rights_percentage = Column(Float, nullable=True)
    control_description = Column(Text, nullable=True)

    # Verification
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    verified = Column(Boolean, default=False)
    verification_date = Column(Date, nullable=True)
    verification_documents = Column(JSON, nullable=True)

    # SPF declaration
    declared_to_spf = Column(Boolean, default=False)
    spf_declaration_date = Column(Date, nullable=True)
    spf_reference = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UBORegister {self.name}>"


# Belgian legal document templates
LEGAL_DOCUMENT_TEMPLATES = {
    "PV_AG_ORDINAIRE": {
        "title": "Proces-verbal de l'Assemblee Generale Ordinaire",
        "sections": [
            "Composition du bureau",
            "Constatation de la validite",
            "Lecture du rapport de gestion",
            "Lecture du rapport du commissaire",
            "Approbation des comptes annuels",
            "Affectation du resultat",
            "Decharge aux administrateurs",
            "Decharge au commissaire",
            "Divers",
        ]
    },
    "PV_AG_EXTRAORDINAIRE": {
        "title": "Proces-verbal de l'Assemblee Generale Extraordinaire",
        "sections": [
            "Composition du bureau",
            "Constatation de la validite",
            "Lecture du rapport special",
            "Deliberation et vote",
            "Modification des statuts",
            "Cloture",
        ]
    },
    "PV_CA": {
        "title": "Proces-verbal du Conseil d'Administration",
        "sections": [
            "Presences",
            "Verification du quorum",
            "Ordre du jour",
            "Deliberations",
            "Decisions",
            "Cloture",
        ]
    },
    "RAPPORT_GESTION": {
        "title": "Rapport de Gestion",
        "sections": [
            "Commentaire sur les comptes annuels",
            "Expose sur la situation de la societe",
            "Evenements importants survenus apres la cloture",
            "Circonstances susceptibles d'influencer le developpement",
            "Activites en matiere de R&D",
            "Existence de succursales",
            "Utilisation d'instruments financiers",
            "Justification de l'application des regles de continuite",
            "Actions propres",
            "Proposition d'affectation du resultat",
        ]
    },
}

# Standard corporate functions in Belgium
CORPORATE_FUNCTIONS = [
    ("administrateur", "Administrateur"),
    ("administrateur_delegue", "Administrateur delegue"),
    ("president", "President du Conseil d'Administration"),
    ("gerant", "Gerant"),
    ("directeur_general", "Directeur General"),
    ("commissaire", "Commissaire"),
    ("liquidateur", "Liquidateur"),
    ("representant_permanent", "Representant permanent"),
]
