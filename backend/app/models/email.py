"""Email models for the integrated email client."""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship

from app.db.database import Base


class EmailAccountType(str, PyEnum):
    """Type of email account."""
    PERSONAL = "personal"  # User's personal email
    COMPANY = "company"    # Company/shared email for invoices


class EmailFolder(str, PyEnum):
    """Standard email folders."""
    INBOX = "INBOX"
    SENT = "Sent"
    DRAFTS = "Drafts"
    TRASH = "Trash"
    SPAM = "Spam"


class EmailAccount(Base):
    """Email account configuration for IMAP/SMTP."""
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for company accounts

    # Account info
    name = Column(String(100), nullable=False)  # Display name
    email_address = Column(String(255), nullable=False)
    account_type = Column(Enum(EmailAccountType), default=EmailAccountType.PERSONAL)
    is_default = Column(Boolean, default=False)  # Default account for sending
    is_active = Column(Boolean, default=True)

    # IMAP settings (for receiving)
    imap_host = Column(String(255), nullable=False)
    imap_port = Column(Integer, default=993)
    imap_ssl = Column(Boolean, default=True)
    imap_username = Column(String(255), nullable=False)
    imap_password = Column(String(255), nullable=False)  # Should be encrypted in production

    # SMTP settings (for sending)
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, default=587)
    smtp_ssl = Column(Boolean, default=False)
    smtp_tls = Column(Boolean, default=True)
    smtp_username = Column(String(255), nullable=False)
    smtp_password = Column(String(255), nullable=False)  # Should be encrypted in production

    # Invoice settings (for company accounts)
    default_cc = Column(Text, nullable=True)  # Comma-separated CC addresses
    default_bcc = Column(Text, nullable=True)  # Comma-separated BCC addresses
    request_read_receipt = Column(Boolean, default=False)

    # Signature
    signature_html = Column(Text, nullable=True)
    signature_text = Column(Text, nullable=True)

    # Sync settings
    last_sync_at = Column(DateTime, nullable=True)
    sync_from_date = Column(DateTime, nullable=True)  # Only sync emails after this date

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="email_accounts")
    emails = relationship("Email", back_populates="account", cascade="all, delete-orphan")


class Email(Base):
    """Cached email message."""
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("email_accounts.id"), nullable=False)

    # Email identifiers
    message_id = Column(String(255), unique=True, index=True)  # Unique message ID from server
    thread_id = Column(String(255), nullable=True, index=True)  # For threading

    # Folder/status
    folder = Column(String(100), default="INBOX")
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=False)

    # Email headers
    subject = Column(String(500), nullable=True)
    from_address = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=True)
    to_addresses = Column(Text, nullable=False)  # JSON array
    cc_addresses = Column(Text, nullable=True)  # JSON array
    bcc_addresses = Column(Text, nullable=True)  # JSON array
    reply_to = Column(String(255), nullable=True)

    # Content
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    snippet = Column(String(500), nullable=True)  # Preview text

    # Dates
    date_sent = Column(DateTime, nullable=True)
    date_received = Column(DateTime, nullable=True)

    # Attachments info
    has_attachments = Column(Boolean, default=False)
    attachments_json = Column(JSON, nullable=True)  # [{name, size, content_type, path}]

    # Read receipt
    read_receipt_requested = Column(Boolean, default=False)
    read_receipt_sent = Column(Boolean, default=False)

    # Related entities
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("EmailAccount", back_populates="emails")
    invoice = relationship("Invoice", backref="related_emails")
    client = relationship("Client", backref="related_emails")


class EmailTemplate(Base):
    """Email templates for common messages."""
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)

    # Template type
    template_type = Column(String(50), nullable=True)  # invoice, reminder, welcome, etc.

    # Variables that can be used
    available_variables = Column(JSON, nullable=True)  # [{name, description}]

    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
