"""Email sending service."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import TYPE_CHECKING, Optional
import os

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.company import CompanySettings


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    attachments: Optional[list] = None,
    company: Optional["CompanySettings"] = None
) -> bool:
    """Send an email.

    Args:
        to_email: Recipient email
        subject: Email subject
        html_body: HTML content
        text_body: Plain text content (optional)
        attachments: List of file paths to attach
        company: Company settings (for SMTP config)

    Returns:
        True if sent successfully
    """
    # Get SMTP settings
    smtp_host = company.smtp_host if company else settings.SMTP_HOST
    smtp_port = company.smtp_port if company else settings.SMTP_PORT
    smtp_user = company.smtp_user if company else settings.SMTP_USER
    smtp_password = company.smtp_password if company else settings.SMTP_PASSWORD
    from_email = company.smtp_from_email if company else settings.SMTP_FROM_EMAIL
    use_tls = company.smtp_tls if company else settings.SMTP_TLS

    if not all([smtp_host, smtp_user, smtp_password, from_email]):
        raise ValueError("SMTP settings not configured")

    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    # Add text body
    if text_body:
        msg.attach(MIMEText(text_body, "plain"))

    # Add HTML body
    msg.attach(MIMEText(html_body, "html"))

    # Add attachments
    if attachments:
        for filepath in attachments:
            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    part = MIMEApplication(f.read())
                    filename = os.path.basename(filepath)
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=filename
                    )
                    msg.attach(part)

    # Send email
    try:
        if use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)

        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise


def send_invoice_email(invoice: "Invoice", company: "CompanySettings") -> bool:
    """Send invoice email to client.

    Args:
        invoice: Invoice model with client loaded
        company: Company settings

    Returns:
        True if sent successfully
    """
    if not invoice.client.email:
        raise ValueError("Client has no email address")

    # Prepare subject
    subject = f"Facture {invoice.invoice_number} - {company.company_name}"

    # Prepare body
    html_body = f"""
    <html>
    <body>
        <p>Bonjour,</p>

        <p>Veuillez trouver ci-joint la facture <strong>{invoice.invoice_number}</strong>
        d'un montant de <strong>{invoice.total_tvac:.2f} EUR</strong>.</p>

        <p><strong>Date d'échéance :</strong> {invoice.due_date.strftime('%d/%m/%Y')}</p>

        {"<p><strong>Lien de paiement PayPal :</strong> <a href='" + invoice.paypal_payment_link + "'>Payer maintenant</a></p>" if invoice.paypal_payment_link else ""}

        <p>Merci pour votre confiance.</p>

        <p>Cordialement,<br>
        {company.company_name}</p>
    </body>
    </html>
    """

    text_body = f"""
Bonjour,

Veuillez trouver ci-joint la facture {invoice.invoice_number}
d'un montant de {invoice.total_tvac:.2f} EUR.

Date d'échéance : {invoice.due_date.strftime('%d/%m/%Y')}

{"Lien de paiement PayPal : " + invoice.paypal_payment_link if invoice.paypal_payment_link else ""}

Merci pour votre confiance.

Cordialement,
{company.company_name}
    """

    # Attachments
    attachments = []
    if invoice.pdf_path and os.path.exists(invoice.pdf_path):
        attachments.append(invoice.pdf_path)

    return send_email(
        to_email=invoice.client.email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        attachments=attachments,
        company=company
    )
