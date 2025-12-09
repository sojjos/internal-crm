"""PDF generation service for invoices and quotes."""
import os
from datetime import datetime, date
from typing import TYPE_CHECKING, Optional

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.quote import Quote
    from app.models.company import CompanySettings


# Get template directory
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")


def generate_invoice_pdf(
    invoice: "Invoice",
    company: "CompanySettings",
    is_paid: bool = False,
    payment_date: Optional[date] = None
) -> str:
    """Generate PDF for an invoice.

    Args:
        invoice: Invoice model with lines and client loaded
        company: Company settings
        is_paid: Whether to show PAID stamp
        payment_date: Date of payment for the stamp

    Returns:
        Path to generated PDF file
    """
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("invoice.html")

    # Prepare template context
    context = {
        "invoice": invoice,
        "company": company,
        "client": invoice.client,
        "lines": invoice.lines,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "is_paid": is_paid,
        "payment_date": payment_date,
    }

    # Render HTML
    html_content = template.render(**context)

    # Create output directory
    output_dir = os.path.join(settings.UPLOAD_DIR, "invoices")
    os.makedirs(output_dir, exist_ok=True)

    # Generate PDF
    filename = f"invoice_{invoice.invoice_number.replace('/', '-')}.pdf"
    filepath = os.path.join(output_dir, filename)

    HTML(string=html_content).write_pdf(filepath)

    # Return relative path for URL access
    return f"invoices/{filename}"


def generate_invoice_html(invoice: "Invoice", company: "CompanySettings") -> str:
    """Generate HTML content for an invoice (for email body).

    Args:
        invoice: Invoice model with lines and client loaded
        company: Company settings

    Returns:
        HTML content string
    """
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("invoice_email.html")

    context = {
        "invoice": invoice,
        "company": company,
        "client": invoice.client,
        "lines": invoice.lines,
    }

    return template.render(**context)


def generate_quote_pdf(
    quote: "Quote",
    company: "CompanySettings",
    is_accepted: bool = False,
    accepted_date: Optional[date] = None
) -> str:
    """Generate PDF for a quote.

    Args:
        quote: Quote model with lines and client loaded
        company: Company settings
        is_accepted: Whether to show ACCEPTED stamp
        accepted_date: Date of acceptance for the stamp

    Returns:
        Path to generated PDF file
    """
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("quote.html")

    # Prepare template context
    context = {
        "quote": quote,
        "company": company,
        "client": quote.client,
        "lines": quote.lines,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "is_accepted": is_accepted,
        "accepted_date": accepted_date,
    }

    # Render HTML
    html_content = template.render(**context)

    # Create output directory
    output_dir = os.path.join(settings.UPLOAD_DIR, "quotes")
    os.makedirs(output_dir, exist_ok=True)

    # Generate PDF
    filename = f"quote_{quote.quote_number.replace('/', '-')}.pdf"
    filepath = os.path.join(output_dir, filename)

    HTML(string=html_content).write_pdf(filepath)

    # Return relative path for URL access
    return f"quotes/{filename}"
