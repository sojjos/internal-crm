"""Document management (GED) models."""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship

from app.db.database import Base


class DocumentType(str, PyEnum):
    """Document type enum."""
    CONTRAT = "CONTRAT"
    ASSURANCE = "ASSURANCE"
    CERTIFICAT = "CERTIFICAT"
    JURIDIQUE = "JURIDIQUE"
    FACTURE_FOURNISSEUR = "FACTURE_FOURNISSEUR"
    BON_COMMANDE = "BON_COMMANDE"
    DEVIS_FOURNISSEUR = "DEVIS_FOURNISSEUR"
    PROCES_VERBAL = "PROCES_VERBAL"
    FACTURE_CLIENT = "FACTURE_CLIENT"  # Generated invoice PDF
    DEVIS_CLIENT = "DEVIS_CLIENT"  # Generated quote PDF
    AUTRE = "AUTRE"


class DocumentCategory(Base):
    """Document category for organization."""
    __tablename__ = "document_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#6B7280")  # Hex color for UI
    icon = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="category")


class Document(Base):
    """Document storage model."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(Enum(DocumentType), default=DocumentType.AUTRE)
    category_id = Column(Integer, ForeignKey("document_categories.id"), nullable=True)

    # File storage
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)  # In bytes
    mime_type = Column(String(100), nullable=True)

    # Dates
    document_date = Column(DateTime, nullable=True)  # Date on document
    expiry_date = Column(DateTime, nullable=True)  # For certificates, insurances

    # Links to other entities (polymorphic)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=True)
    contract_id = Column(Integer, ForeignKey("purchase_contracts.id"), nullable=True)
    fixed_asset_id = Column(Integer, ForeignKey("fixed_assets.id"), nullable=True)
    collaborator_id = Column(Integer, ForeignKey("collaborators.id"), nullable=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True)

    # Tags for search
    tags = Column(String(500), nullable=True)  # Comma-separated tags

    # Metadata
    is_archived = Column(Boolean, default=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("DocumentCategory", back_populates="documents")
    client = relationship("Client", backref="documents")
    supplier = relationship("Supplier", backref="documents")
    purchase = relationship("Purchase", backref="documents")
    contract = relationship("PurchaseContract", backref="documents")
    fixed_asset = relationship("FixedAsset", backref="documents")
    collaborator = relationship("Collaborator", backref="documents")
    invoice = relationship("Invoice", backref="documents")
    quote = relationship("Quote", backref="documents")
    created_by = relationship("User", backref="created_documents")
