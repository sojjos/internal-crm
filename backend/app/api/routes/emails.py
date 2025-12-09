"""Email routes."""
import json
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.email import EmailAccount, Email, EmailTemplate, EmailAccountType
from app.schemas.email import (
    EmailAccountCreate, EmailAccountUpdate, EmailAccountResponse, EmailAccountTest,
    EmailCompose, EmailResponse, EmailDetail, EmailListResponse,
    EmailTemplateCreate, EmailTemplateUpdate, EmailTemplateResponse,
    EmailFolderCount, EmailSyncRequest, EmailSyncStatus,
)
from app.services.email_client import EmailClient, EmailClientError, test_email_account, sync_emails

router = APIRouter()


# ============ Email Accounts ============

@router.get("/accounts", response_model=List[EmailAccountResponse])
def list_email_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all email accounts for current user."""
    accounts = db.query(EmailAccount).filter(
        (EmailAccount.user_id == current_user.id) |
        (EmailAccount.account_type == EmailAccountType.COMPANY)
    ).all()
    return accounts


@router.post("/accounts", response_model=EmailAccountResponse)
def create_email_account(
    account_in: EmailAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new email account."""
    # Check if email already exists
    existing = db.query(EmailAccount).filter(
        EmailAccount.email_address == account_in.email_address
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email account already exists"
        )

    account = EmailAccount(
        user_id=current_user.id if account_in.account_type == EmailAccountType.PERSONAL else None,
        **account_in.model_dump()
    )

    # If this is the first account or marked as default, set it as default
    if account_in.is_default:
        # Unset other defaults for this user
        db.query(EmailAccount).filter(
            EmailAccount.user_id == current_user.id,
            EmailAccount.is_default == True
        ).update({"is_default": False})

    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/accounts/{account_id}", response_model=EmailAccountResponse)
def get_email_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get email account by ID."""
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id,
        (EmailAccount.user_id == current_user.id) |
        (EmailAccount.account_type == EmailAccountType.COMPANY)
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found"
        )
    return account


@router.put("/accounts/{account_id}", response_model=EmailAccountResponse)
def update_email_account(
    account_id: int,
    account_in: EmailAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update email account."""
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id,
        (EmailAccount.user_id == current_user.id) |
        (EmailAccount.account_type == EmailAccountType.COMPANY)
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found"
        )

    update_data = account_in.model_dump(exclude_unset=True)

    # Handle default flag
    if update_data.get("is_default"):
        db.query(EmailAccount).filter(
            EmailAccount.user_id == current_user.id,
            EmailAccount.id != account_id,
            EmailAccount.is_default == True
        ).update({"is_default": False})

    for field, value in update_data.items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)
    return account


@router.delete("/accounts/{account_id}")
def delete_email_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete email account."""
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id,
        EmailAccount.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found"
        )

    db.delete(account)
    db.commit()
    return {"message": "Account deleted"}


@router.post("/accounts/test")
def test_account_connection(
    test_data: EmailAccountTest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Test email account connection."""
    result = test_email_account(
        imap_host=test_data.imap_host,
        imap_port=test_data.imap_port,
        imap_ssl=test_data.imap_ssl,
        imap_username=test_data.imap_username,
        imap_password=test_data.imap_password,
        smtp_host=test_data.smtp_host,
        smtp_port=test_data.smtp_port,
        smtp_ssl=test_data.smtp_ssl,
        smtp_tls=test_data.smtp_tls,
        smtp_username=test_data.smtp_username,
        smtp_password=test_data.smtp_password,
    )
    return result


# ============ Emails ============

@router.get("/", response_model=EmailListResponse)
def list_emails(
    account_id: Optional[int] = None,
    folder: str = "INBOX",
    is_read: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List emails with pagination."""
    # Build query
    query = db.query(Email).join(EmailAccount)

    # Filter by account or user's accounts
    if account_id:
        query = query.filter(Email.account_id == account_id)
    else:
        query = query.filter(
            (EmailAccount.user_id == current_user.id) |
            (EmailAccount.account_type == EmailAccountType.COMPANY)
        )

    # Filter by folder
    query = query.filter(Email.folder == folder)

    # Filter by read status
    if is_read is not None:
        query = query.filter(Email.is_read == is_read)

    # Search
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Email.subject.ilike(search_pattern)) |
            (Email.from_address.ilike(search_pattern)) |
            (Email.body_text.ilike(search_pattern))
        )

    # Get total count
    total = query.count()

    # Order and paginate
    emails = query.order_by(Email.date_sent.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    # Convert to response format
    email_responses = [EmailResponse.from_orm_with_addresses(e) for e in emails]

    return EmailListResponse(
        emails=email_responses,
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total
    )


@router.get("/folders", response_model=List[EmailFolderCount])
def get_folder_counts(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get email counts per folder."""
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id,
        (EmailAccount.user_id == current_user.id) |
        (EmailAccount.account_type == EmailAccountType.COMPANY)
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found"
        )

    # Get counts from database
    folders = ["INBOX", "Sent", "Drafts", "Trash"]
    result = []

    for folder in folders:
        total = db.query(Email).filter(
            Email.account_id == account_id,
            Email.folder == folder
        ).count()

        unread = db.query(Email).filter(
            Email.account_id == account_id,
            Email.folder == folder,
            Email.is_read == False
        ).count()

        result.append(EmailFolderCount(folder=folder, total=total, unread=unread))

    return result


@router.get("/{email_id}", response_model=EmailDetail)
def get_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get email detail."""
    email = db.query(Email).join(EmailAccount).filter(
        Email.id == email_id,
        (EmailAccount.user_id == current_user.id) |
        (EmailAccount.account_type == EmailAccountType.COMPANY)
    ).first()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )

    # Mark as read
    if not email.is_read:
        email.is_read = True
        db.commit()

    # Build response
    return EmailDetail(
        id=email.id,
        account_id=email.account_id,
        message_id=email.message_id,
        folder=email.folder,
        is_read=email.is_read,
        is_starred=email.is_starred,
        is_draft=email.is_draft,
        subject=email.subject,
        from_address=email.from_address,
        from_name=email.from_name,
        to_addresses=json.loads(email.to_addresses) if email.to_addresses else [],
        cc_addresses=json.loads(email.cc_addresses) if email.cc_addresses else None,
        bcc_addresses=json.loads(email.bcc_addresses) if email.bcc_addresses else None,
        snippet=email.snippet,
        body_text=email.body_text,
        body_html=email.body_html,
        reply_to=email.reply_to,
        date_sent=email.date_sent,
        date_received=email.date_received,
        has_attachments=email.has_attachments,
        attachments=email.attachments_json,
        read_receipt_requested=email.read_receipt_requested,
        invoice_id=email.invoice_id,
        client_id=email.client_id,
        created_at=email.created_at,
    )


@router.post("/send")
async def send_email(
    account_id: int = Form(...),
    to: str = Form(...),  # Comma-separated
    subject: str = Form(...),
    body_text: Optional[str] = Form(None),
    body_html: Optional[str] = Form(None),
    cc: Optional[str] = Form(None),
    bcc: Optional[str] = Form(None),
    request_read_receipt: bool = Form(False),
    attachments: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Send an email."""
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id,
        (EmailAccount.user_id == current_user.id) |
        (EmailAccount.account_type == EmailAccountType.COMPANY)
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found"
        )

    # Parse addresses
    to_list = [addr.strip() for addr in to.split(',') if addr.strip()]
    cc_list = [addr.strip() for addr in cc.split(',') if addr.strip()] if cc else None
    bcc_list = [addr.strip() for addr in bcc.split(',') if addr.strip()] if bcc else None

    # Add default CC/BCC from account settings
    if account.default_cc:
        default_cc = [addr.strip() for addr in account.default_cc.split(',')]
        if cc_list:
            cc_list.extend(default_cc)
        else:
            cc_list = default_cc

    if account.default_bcc:
        default_bcc = [addr.strip() for addr in account.default_bcc.split(',')]
        if bcc_list:
            bcc_list.extend(default_bcc)
        else:
            bcc_list = default_bcc

    # Use account's read receipt setting if not specified
    if account.request_read_receipt and not request_read_receipt:
        request_read_receipt = True

    # Handle attachments
    attachment_data = []
    if attachments:
        for file in attachments:
            if file.filename:
                content = await file.read()
                attachment_data.append((
                    file.filename,
                    content,
                    file.content_type or 'application/octet-stream'
                ))

    # Add signature
    if body_html and account.signature_html:
        body_html = body_html + "<br><br>" + account.signature_html
    if body_text and account.signature_text:
        body_text = body_text + "\n\n" + account.signature_text

    # Send email
    client = EmailClient(account)
    try:
        message_id = client.send_email(
            to=to_list,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            cc=cc_list,
            bcc=bcc_list,
            request_read_receipt=request_read_receipt,
            attachments=attachment_data if attachment_data else None,
        )

        # Save to database
        sent_email = Email(
            account_id=account.id,
            message_id=message_id,
            folder="Sent",
            is_read=True,
            subject=subject,
            from_address=account.email_address,
            from_name=account.name,
            to_addresses=json.dumps(to_list),
            cc_addresses=json.dumps(cc_list) if cc_list else None,
            bcc_addresses=json.dumps(bcc_list) if bcc_list else None,
            body_text=body_text,
            body_html=body_html,
            date_sent=datetime.utcnow(),
            has_attachments=len(attachment_data) > 0,
            read_receipt_requested=request_read_receipt,
        )
        db.add(sent_email)
        db.commit()

        return {"message": "Email sent successfully", "message_id": message_id}

    except EmailClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        client.disconnect_smtp()


@router.post("/{email_id}/mark-read")
def mark_email_read(
    email_id: int,
    is_read: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Mark email as read/unread."""
    email = db.query(Email).join(EmailAccount).filter(
        Email.id == email_id,
        (EmailAccount.user_id == current_user.id) |
        (EmailAccount.account_type == EmailAccountType.COMPANY)
    ).first()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )

    email.is_read = is_read
    db.commit()
    return {"message": "Email updated"}


@router.post("/{email_id}/star")
def toggle_star(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Toggle email star."""
    email = db.query(Email).join(EmailAccount).filter(
        Email.id == email_id,
        (EmailAccount.user_id == current_user.id) |
        (EmailAccount.account_type == EmailAccountType.COMPANY)
    ).first()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )

    email.is_starred = not email.is_starred
    db.commit()
    return {"is_starred": email.is_starred}


@router.delete("/{email_id}")
def delete_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete email (move to trash or permanently delete)."""
    email = db.query(Email).join(EmailAccount).filter(
        Email.id == email_id,
        (EmailAccount.user_id == current_user.id) |
        (EmailAccount.account_type == EmailAccountType.COMPANY)
    ).first()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )

    if email.folder == "Trash":
        # Permanently delete
        db.delete(email)
    else:
        # Move to trash
        email.folder = "Trash"

    db.commit()
    return {"message": "Email deleted"}


# ============ Sync ============

@router.post("/sync")
def sync_account_emails(
    sync_request: EmailSyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Sync emails from server."""
    account = db.query(EmailAccount).filter(
        EmailAccount.id == sync_request.account_id,
        (EmailAccount.user_id == current_user.id) |
        (EmailAccount.account_type == EmailAccountType.COMPANY)
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found"
        )

    # Run sync in background
    background_tasks.add_task(
        sync_emails,
        db,
        account,
        sync_request.folder,
        sync_request.force_full_sync
    )

    return {"message": "Sync started"}


# ============ Templates ============

@router.get("/templates", response_model=List[EmailTemplateResponse])
def list_templates(
    template_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List email templates."""
    query = db.query(EmailTemplate).filter(EmailTemplate.is_active == True)

    if template_type:
        query = query.filter(EmailTemplate.template_type == template_type)

    return query.all()


@router.post("/templates", response_model=EmailTemplateResponse)
def create_template(
    template_in: EmailTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create email template."""
    template = EmailTemplate(**template_in.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.put("/templates/{template_id}", response_model=EmailTemplateResponse)
def update_template(
    template_id: int,
    template_in: EmailTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update email template."""
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    for field, value in template_in.model_dump(exclude_unset=True).items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete email template."""
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    db.delete(template)
    db.commit()
    return {"message": "Template deleted"}
