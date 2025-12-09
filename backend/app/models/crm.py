"""CRM and pipeline models."""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Boolean, Enum, Numeric
from sqlalchemy.orm import relationship

from app.db.database import Base


class LeadSource(str, PyEnum):
    """Source of the lead/prospect."""
    SITE_WEB = "SITE_WEB"
    RECOMMANDATION = "RECOMMANDATION"
    RESEAUX_SOCIAUX = "RESEAUX_SOCIAUX"
    SALON = "SALON"
    DEMARCHAGE = "DEMARCHAGE"
    PUBLICITE = "PUBLICITE"
    ANCIEN_CLIENT = "ANCIEN_CLIENT"
    AUTRE = "AUTRE"


class PipelineStage(str, PyEnum):
    """Pipeline stage for opportunities."""
    PROSPECT = "PROSPECT"           # New lead
    PREMIER_CONTACT = "PREMIER_CONTACT"  # First contact made
    QUALIFICATION = "QUALIFICATION"  # Qualifying the lead
    PROPOSITION = "PROPOSITION"      # Quote/proposal sent
    NEGOCIATION = "NEGOCIATION"     # Negotiating
    GAGNE = "GAGNE"                 # Won
    PERDU = "PERDU"                 # Lost


class ContactType(str, PyEnum):
    """Type of contact activity."""
    APPEL = "APPEL"
    EMAIL = "EMAIL"
    REUNION = "REUNION"
    VISITE = "VISITE"
    MESSAGE = "MESSAGE"
    AUTRE = "AUTRE"


class TaskPriority(str, PyEnum):
    """Task priority."""
    BASSE = "BASSE"
    NORMALE = "NORMALE"
    HAUTE = "HAUTE"
    URGENTE = "URGENTE"


class TaskStatus(str, PyEnum):
    """Task status."""
    A_FAIRE = "A_FAIRE"
    EN_COURS = "EN_COURS"
    TERMINE = "TERMINE"
    ANNULE = "ANNULE"


class ClientTag(Base):
    """Tags for categorizing clients."""
    __tablename__ = "client_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    color = Column(String(7), default="#6B7280")
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    clients = relationship("ClientTagAssociation", back_populates="tag")


class ClientTagAssociation(Base):
    """Association between clients and tags."""
    __tablename__ = "client_tag_associations"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("client_tags.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", backref="tag_associations")
    tag = relationship("ClientTag", back_populates="clients")


class Opportunity(Base):
    """Sales opportunity / deal."""
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Client (can be existing or prospect)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    prospect_company = Column(String(255), nullable=True)  # If not yet a client
    prospect_contact = Column(String(100), nullable=True)
    prospect_email = Column(String(255), nullable=True)
    prospect_phone = Column(String(20), nullable=True)

    # Pipeline
    stage = Column(Enum(PipelineStage), default=PipelineStage.PROSPECT)
    source = Column(Enum(LeadSource), nullable=True)
    probability = Column(Integer, default=10)  # Win probability %

    # Value
    estimated_value = Column(Numeric(12, 2), nullable=True)
    estimated_close_date = Column(Date, nullable=True)

    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Outcome
    won_at = Column(DateTime, nullable=True)
    lost_at = Column(DateTime, nullable=True)
    lost_reason = Column(Text, nullable=True)

    # Links
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)

    # Metadata
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", backref="opportunities")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], backref="assigned_opportunities")
    created_by = relationship("User", foreign_keys=[created_by_id], backref="created_opportunities")
    quote = relationship("Quote", backref="opportunity")
    invoice = relationship("Invoice", backref="opportunity")
    activities = relationship("ContactActivity", back_populates="opportunity")
    tasks = relationship("CRMTask", back_populates="opportunity")


class ContactActivity(Base):
    """Contact activity / interaction log."""
    __tablename__ = "contact_activities"

    id = Column(Integer, primary_key=True, index=True)

    # What
    activity_type = Column(Enum(ContactType), default=ContactType.AUTRE)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # When
    activity_date = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer, nullable=True)

    # Who
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    contact_name = Column(String(100), nullable=True)

    # Linked items
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=True)

    # Metadata
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    client = relationship("Client", backref="activities")
    opportunity = relationship("Opportunity", back_populates="activities")
    created_by = relationship("User", backref="logged_activities")


class CRMTask(Base):
    """Task / reminder for CRM."""
    __tablename__ = "crm_tasks"

    id = Column(Integer, primary_key=True, index=True)

    # Task details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Enum(TaskPriority), default=TaskPriority.NORMALE)
    status = Column(Enum(TaskStatus), default=TaskStatus.A_FAIRE)

    # Due date
    due_date = Column(DateTime, nullable=True)
    reminder_date = Column(DateTime, nullable=True)

    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Links
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)

    # Completion
    completed_at = Column(DateTime, nullable=True)
    completed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Metadata
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", backref="crm_tasks")
    opportunity = relationship("Opportunity", back_populates="tasks")
    quote = relationship("Quote", backref="crm_tasks")
    invoice = relationship("Invoice", backref="crm_tasks")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], backref="assigned_tasks")
    completed_by = relationship("User", foreign_keys=[completed_by_id])
    created_by = relationship("User", foreign_keys=[created_by_id], backref="created_tasks")
