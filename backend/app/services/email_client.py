"""Email client service for IMAP/SMTP operations."""
import imaplib
import smtplib
import email
import json
import os
import uuid
from datetime import datetime
from email import encoders
from email.header import decode_header, make_header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr, parsedate_to_datetime
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.email import EmailAccount, Email, EmailAccountType


class EmailClientError(Exception):
    """Custom exception for email client errors."""
    pass


class EmailClient:
    """Email client for IMAP and SMTP operations."""

    def __init__(self, account: EmailAccount):
        self.account = account
        self._imap = None
        self._smtp = None

    # Connection methods
    def connect_imap(self) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server."""
        try:
            if self.account.imap_ssl:
                self._imap = imaplib.IMAP4_SSL(
                    self.account.imap_host,
                    self.account.imap_port
                )
            else:
                self._imap = imaplib.IMAP4(
                    self.account.imap_host,
                    self.account.imap_port
                )

            self._imap.login(
                self.account.imap_username,
                self.account.imap_password
            )
            return self._imap
        except Exception as e:
            raise EmailClientError(f"Failed to connect to IMAP: {str(e)}")

    def disconnect_imap(self):
        """Disconnect from IMAP server."""
        if self._imap:
            try:
                self._imap.logout()
            except:
                pass
            self._imap = None

    def connect_smtp(self) -> smtplib.SMTP:
        """Connect to SMTP server."""
        try:
            if self.account.smtp_ssl:
                self._smtp = smtplib.SMTP_SSL(
                    self.account.smtp_host,
                    self.account.smtp_port
                )
            else:
                self._smtp = smtplib.SMTP(
                    self.account.smtp_host,
                    self.account.smtp_port
                )
                if self.account.smtp_tls:
                    self._smtp.starttls()

            self._smtp.login(
                self.account.smtp_username,
                self.account.smtp_password
            )
            return self._smtp
        except Exception as e:
            raise EmailClientError(f"Failed to connect to SMTP: {str(e)}")

    def disconnect_smtp(self):
        """Disconnect from SMTP server."""
        if self._smtp:
            try:
                self._smtp.quit()
            except:
                pass
            self._smtp = None

    # IMAP operations
    def list_folders(self) -> List[str]:
        """List available email folders."""
        if not self._imap:
            self.connect_imap()

        status, folders = self._imap.list()
        if status != 'OK':
            raise EmailClientError("Failed to list folders")

        folder_names = []
        for folder in folders:
            # Parse folder name from response
            if isinstance(folder, bytes):
                folder = folder.decode('utf-8')
            # Extract folder name (last part after the delimiter)
            parts = folder.split('"')
            if len(parts) >= 2:
                folder_names.append(parts[-2])

        return folder_names

    def get_folder_status(self, folder: str = "INBOX") -> Dict[str, int]:
        """Get folder status (total and unread count)."""
        if not self._imap:
            self.connect_imap()

        status, data = self._imap.select(folder, readonly=True)
        if status != 'OK':
            raise EmailClientError(f"Failed to select folder: {folder}")

        total = int(data[0])

        # Get unread count
        status, data = self._imap.search(None, 'UNSEEN')
        unread = len(data[0].split()) if data[0] else 0

        return {"total": total, "unread": unread}

    def fetch_emails(
        self,
        folder: str = "INBOX",
        limit: int = 50,
        offset: int = 0,
        since_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Fetch emails from a folder."""
        if not self._imap:
            self.connect_imap()

        status, data = self._imap.select(folder, readonly=True)
        if status != 'OK':
            raise EmailClientError(f"Failed to select folder: {folder}")

        # Build search criteria
        criteria = 'ALL'
        if since_date:
            date_str = since_date.strftime("%d-%b-%Y")
            criteria = f'(SINCE {date_str})'

        status, data = self._imap.search(None, criteria)
        if status != 'OK':
            raise EmailClientError("Failed to search emails")

        email_ids = data[0].split()
        email_ids.reverse()  # Most recent first

        # Apply pagination
        email_ids = email_ids[offset:offset + limit]

        emails = []
        for email_id in email_ids:
            try:
                email_data = self._fetch_email_data(email_id)
                if email_data:
                    emails.append(email_data)
            except Exception as e:
                print(f"Error fetching email {email_id}: {e}")
                continue

        return emails

    def _fetch_email_data(self, email_id: bytes) -> Optional[Dict[str, Any]]:
        """Fetch and parse a single email."""
        status, data = self._imap.fetch(email_id, '(RFC822 FLAGS)')
        if status != 'OK':
            return None

        raw_email = data[0][1]
        flags = data[0][0].decode() if data[0][0] else ""

        msg = email.message_from_bytes(raw_email)

        # Parse headers
        subject = self._decode_header(msg.get('Subject', ''))
        from_addr = msg.get('From', '')
        from_name, from_email = parseaddr(from_addr)
        from_name = self._decode_header(from_name) if from_name else None

        to_addresses = self._parse_addresses(msg.get('To', ''))
        cc_addresses = self._parse_addresses(msg.get('Cc', ''))

        # Parse date
        date_str = msg.get('Date', '')
        try:
            date_sent = parsedate_to_datetime(date_str) if date_str else None
        except:
            date_sent = None

        # Get message ID
        message_id = msg.get('Message-ID', str(uuid.uuid4()))

        # Parse body
        body_text, body_html, attachments = self._parse_body(msg)

        # Check if read
        is_read = '\\Seen' in flags

        return {
            'message_id': message_id,
            'subject': subject,
            'from_address': from_email,
            'from_name': from_name,
            'to_addresses': to_addresses,
            'cc_addresses': cc_addresses,
            'body_text': body_text,
            'body_html': body_html,
            'date_sent': date_sent,
            'is_read': is_read,
            'has_attachments': len(attachments) > 0,
            'attachments': attachments,
            'reply_to': msg.get('Reply-To'),
            'read_receipt_requested': 'Disposition-Notification-To' in msg,
        }

    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        if not header:
            return ''
        try:
            decoded = str(make_header(decode_header(header)))
            return decoded
        except:
            return header

    def _parse_addresses(self, addresses: str) -> List[str]:
        """Parse comma-separated email addresses."""
        if not addresses:
            return []

        result = []
        # Handle multiple addresses
        for addr in addresses.split(','):
            name, email_addr = parseaddr(addr.strip())
            if email_addr:
                result.append(email_addr)
        return result

    def _parse_body(self, msg) -> Tuple[str, str, List[Dict]]:
        """Parse email body and attachments."""
        body_text = ""
        body_html = ""
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    # Handle attachment
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header(filename)
                        attachments.append({
                            'name': filename,
                            'content_type': content_type,
                            'size': len(part.get_payload(decode=True) or b''),
                        })
                elif content_type == "text/plain":
                    try:
                        body_text = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    except:
                        body_text = part.get_payload()
                elif content_type == "text/html":
                    try:
                        body_html = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    except:
                        body_html = part.get_payload()
        else:
            content_type = msg.get_content_type()
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    text = payload.decode('utf-8', errors='replace')
                    if content_type == "text/html":
                        body_html = text
                    else:
                        body_text = text
            except:
                pass

        return body_text, body_html, attachments

    def mark_as_read(self, email_id: bytes):
        """Mark an email as read."""
        if not self._imap:
            self.connect_imap()
        self._imap.store(email_id, '+FLAGS', '\\Seen')

    def mark_as_unread(self, email_id: bytes):
        """Mark an email as unread."""
        if not self._imap:
            self.connect_imap()
        self._imap.store(email_id, '-FLAGS', '\\Seen')

    def delete_email(self, email_id: bytes):
        """Delete an email (move to trash)."""
        if not self._imap:
            self.connect_imap()
        self._imap.store(email_id, '+FLAGS', '\\Deleted')
        self._imap.expunge()

    # SMTP operations
    def send_email(
        self,
        to: List[str],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Tuple[str, bytes, str]]] = None,
        request_read_receipt: bool = False,
    ) -> str:
        """
        Send an email.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body
            cc: List of CC addresses
            bcc: List of BCC addresses
            reply_to: Reply-to address
            attachments: List of (filename, content, content_type) tuples
            request_read_receipt: Whether to request read receipt

        Returns:
            Message ID of sent email
        """
        if not self._smtp:
            self.connect_smtp()

        # Create message
        if body_html and body_text:
            msg = MIMEMultipart('alternative')
            msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
            msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        elif body_html:
            msg = MIMEMultipart('alternative')
            msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        else:
            msg = MIMEMultipart()
            msg.attach(MIMEText(body_text or '', 'plain', 'utf-8'))

        # Set headers
        msg['From'] = formataddr((self.account.name, self.account.email_address))
        msg['To'] = ', '.join(to)
        msg['Subject'] = subject
        msg['Date'] = email.utils.formatdate(localtime=True)
        msg['Message-ID'] = email.utils.make_msgid()

        if cc:
            msg['Cc'] = ', '.join(cc)
        if reply_to:
            msg['Reply-To'] = reply_to
        if request_read_receipt:
            msg['Disposition-Notification-To'] = self.account.email_address

        # Add signature if configured
        if self.account.signature_html and body_html:
            # Append signature to HTML body
            pass  # Already handled in compose

        # Add attachments
        if attachments:
            for filename, content, content_type in attachments:
                part = MIMEBase(*content_type.split('/'))
                part.set_payload(content)
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{filename}"'
                )
                msg.attach(part)

        # Collect all recipients
        recipients = to.copy()
        if cc:
            recipients.extend(cc)
        if bcc:
            recipients.extend(bcc)

        # Send
        try:
            self._smtp.sendmail(
                self.account.email_address,
                recipients,
                msg.as_string()
            )
            return msg['Message-ID']
        except Exception as e:
            raise EmailClientError(f"Failed to send email: {str(e)}")


def test_email_account(
    imap_host: str,
    imap_port: int,
    imap_ssl: bool,
    imap_username: str,
    imap_password: str,
    smtp_host: str,
    smtp_port: int,
    smtp_ssl: bool,
    smtp_tls: bool,
    smtp_username: str,
    smtp_password: str,
) -> Dict[str, Any]:
    """Test email account credentials."""
    result = {
        "imap_success": False,
        "smtp_success": False,
        "imap_error": None,
        "smtp_error": None,
    }

    # Test IMAP
    try:
        if imap_ssl:
            imap = imaplib.IMAP4_SSL(imap_host, imap_port)
        else:
            imap = imaplib.IMAP4(imap_host, imap_port)

        imap.login(imap_username, imap_password)
        imap.logout()
        result["imap_success"] = True
    except Exception as e:
        result["imap_error"] = str(e)

    # Test SMTP
    try:
        if smtp_ssl:
            smtp = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            smtp = smtplib.SMTP(smtp_host, smtp_port)
            if smtp_tls:
                smtp.starttls()

        smtp.login(smtp_username, smtp_password)
        smtp.quit()
        result["smtp_success"] = True
    except Exception as e:
        result["smtp_error"] = str(e)

    return result


def sync_emails(
    db: Session,
    account: EmailAccount,
    folder: str = "INBOX",
    force_full_sync: bool = False
) -> int:
    """Sync emails from server to database."""
    client = EmailClient(account)

    try:
        client.connect_imap()

        # Determine since date
        since_date = None
        if not force_full_sync and account.last_sync_at:
            since_date = account.last_sync_at
        elif account.sync_from_date:
            since_date = account.sync_from_date

        # Fetch emails
        emails_data = client.fetch_emails(
            folder=folder,
            limit=500,  # Batch size
            since_date=since_date
        )

        count = 0
        for email_data in emails_data:
            # Check if email already exists
            existing = db.query(Email).filter(
                Email.account_id == account.id,
                Email.message_id == email_data['message_id']
            ).first()

            if existing:
                # Update read status
                existing.is_read = email_data['is_read']
                continue

            # Create new email record
            email_record = Email(
                account_id=account.id,
                message_id=email_data['message_id'],
                folder=folder,
                is_read=email_data['is_read'],
                subject=email_data['subject'],
                from_address=email_data['from_address'],
                from_name=email_data['from_name'],
                to_addresses=json.dumps(email_data['to_addresses']),
                cc_addresses=json.dumps(email_data['cc_addresses']) if email_data['cc_addresses'] else None,
                body_text=email_data['body_text'],
                body_html=email_data['body_html'],
                snippet=email_data['body_text'][:200] if email_data['body_text'] else None,
                date_sent=email_data['date_sent'],
                date_received=datetime.utcnow(),
                has_attachments=email_data['has_attachments'],
                attachments_json=email_data['attachments'] if email_data['attachments'] else None,
                read_receipt_requested=email_data['read_receipt_requested'],
                reply_to=email_data['reply_to'],
            )
            db.add(email_record)
            count += 1

        # Update last sync time
        account.last_sync_at = datetime.utcnow()
        db.commit()

        return count

    finally:
        client.disconnect_imap()
