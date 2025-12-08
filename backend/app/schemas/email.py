"""Email schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.models.email import EmailAccountType, EmailFolder


# Email Account Schemas
class EmailAccountBase(BaseModel):
    """Base email account schema."""
    name: str
    email_address: EmailStr
    account_type: EmailAccountType = EmailAccountType.PERSONAL
    is_default: bool = False

    # IMAP settings
    imap_host: str
    imap_port: int = 993
    imap_ssl: bool = True
    imap_username: str

    # SMTP settings
    smtp_host: str
    smtp_port: int = 587
    smtp_ssl: bool = False
    smtp_tls: bool = True
    smtp_username: str

    # Invoice settings (for company accounts)
    default_cc: Optional[str] = None
    default_bcc: Optional[str] = None
    request_read_receipt: bool = False

    # Signature
    signature_html: Optional[str] = None
    signature_text: Optional[str] = None


class EmailAccountCreate(EmailAccountBase):
    """Schema for creating an email account."""
    imap_password: str
    smtp_password: str


class EmailAccountUpdate(BaseModel):
    """Schema for updating an email account."""
    name: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

    # IMAP settings
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_ssl: Optional[bool] = None
    imap_username: Optional[str] = None
    imap_password: Optional[str] = None

    # SMTP settings
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_ssl: Optional[bool] = None
    smtp_tls: Optional[bool] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

    # Invoice settings
    default_cc: Optional[str] = None
    default_bcc: Optional[str] = None
    request_read_receipt: Optional[bool] = None

    # Signature
    signature_html: Optional[str] = None
    signature_text: Optional[str] = None


class EmailAccountResponse(BaseModel):
    """Schema for email account response."""
    id: int
    user_id: Optional[int]
    name: str
    email_address: str
    account_type: EmailAccountType
    is_default: bool
    is_active: bool

    # Settings (without passwords)
    imap_host: str
    imap_port: int
    imap_ssl: bool
    imap_username: str

    smtp_host: str
    smtp_port: int
    smtp_ssl: bool
    smtp_tls: bool
    smtp_username: str

    default_cc: Optional[str]
    default_bcc: Optional[str]
    request_read_receipt: bool

    signature_html: Optional[str]
    signature_text: Optional[str]

    last_sync_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class EmailAccountTest(BaseModel):
    """Schema for testing email account connection."""
    imap_host: str
    imap_port: int = 993
    imap_ssl: bool = True
    imap_username: str
    imap_password: str
    smtp_host: str
    smtp_port: int = 587
    smtp_ssl: bool = False
    smtp_tls: bool = True
    smtp_username: str
    smtp_password: str


# Email Schemas
class EmailAttachment(BaseModel):
    """Email attachment info."""
    name: str
    size: int
    content_type: str
    path: Optional[str] = None


class EmailBase(BaseModel):
    """Base email schema."""
    subject: Optional[str] = None
    to_addresses: List[str]
    cc_addresses: Optional[List[str]] = None
    bcc_addresses: Optional[List[str]] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None


class EmailCompose(EmailBase):
    """Schema for composing a new email."""
    account_id: int
    reply_to_id: Optional[int] = None  # If replying to an email
    request_read_receipt: bool = False
    # Attachments will be handled separately via multipart


class EmailResponse(BaseModel):
    """Schema for email response."""
    id: int
    account_id: int
    message_id: Optional[str]
    folder: str
    is_read: bool
    is_starred: bool
    is_draft: bool

    subject: Optional[str]
    from_address: str
    from_name: Optional[str]
    to_addresses: List[str]
    cc_addresses: Optional[List[str]]
    snippet: Optional[str]

    date_sent: Optional[datetime]
    date_received: Optional[datetime]

    has_attachments: bool
    attachments: Optional[List[EmailAttachment]] = None

    read_receipt_requested: bool
    invoice_id: Optional[int]
    client_id: Optional[int]

    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_addresses(cls, email):
        """Convert ORM object to response with parsed addresses."""
        import json
        data = {
            "id": email.id,
            "account_id": email.account_id,
            "message_id": email.message_id,
            "folder": email.folder,
            "is_read": email.is_read,
            "is_starred": email.is_starred,
            "is_draft": email.is_draft,
            "subject": email.subject,
            "from_address": email.from_address,
            "from_name": email.from_name,
            "to_addresses": json.loads(email.to_addresses) if email.to_addresses else [],
            "cc_addresses": json.loads(email.cc_addresses) if email.cc_addresses else None,
            "snippet": email.snippet,
            "date_sent": email.date_sent,
            "date_received": email.date_received,
            "has_attachments": email.has_attachments,
            "attachments": email.attachments_json,
            "read_receipt_requested": email.read_receipt_requested,
            "invoice_id": email.invoice_id,
            "client_id": email.client_id,
            "created_at": email.created_at,
        }
        return cls(**data)


class EmailDetail(EmailResponse):
    """Schema for email detail with full body."""
    body_text: Optional[str]
    body_html: Optional[str]
    reply_to: Optional[str]
    bcc_addresses: Optional[List[str]]


class EmailListResponse(BaseModel):
    """Schema for email list with pagination."""
    emails: List[EmailResponse]
    total: int
    page: int
    per_page: int
    has_more: bool


class EmailFolderCount(BaseModel):
    """Schema for folder email counts."""
    folder: str
    total: int
    unread: int


# Email Template Schemas
class EmailTemplateBase(BaseModel):
    """Base email template schema."""
    name: str
    subject: str
    body_html: str
    body_text: Optional[str] = None
    template_type: Optional[str] = None
    is_default: bool = False


class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating an email template."""
    pass


class EmailTemplateUpdate(BaseModel):
    """Schema for updating an email template."""
    name: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    template_type: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(EmailTemplateBase):
    """Schema for email template response."""
    id: int
    is_active: bool
    available_variables: Optional[List[dict]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Sync schemas
class EmailSyncRequest(BaseModel):
    """Schema for requesting email sync."""
    account_id: int
    folder: str = "INBOX"
    force_full_sync: bool = False


class EmailSyncStatus(BaseModel):
    """Schema for sync status response."""
    account_id: int
    is_syncing: bool
    last_sync_at: Optional[datetime]
    emails_synced: int
    errors: Optional[List[str]] = None
