"""Company settings model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON

from app.db.database import Base


class CompanySettings(Base):
    """Company settings and configuration."""

    __tablename__ = "company_settings"

    id = Column(Integer, primary_key=True, index=True)

    # Company information
    company_name = Column(String(255), nullable=False)
    address_street = Column(String(255), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_postal_code = Column(String(20), nullable=True)
    address_country = Column(String(100), default="Belgique")
    vat_number = Column(String(50), nullable=True)  # TVA number
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    logo_path = Column(String(500), nullable=True)  # Path to logo file

    # VAT settings
    vat_rates = Column(JSON, default=[21.0, 6.0, 12.0, 0.0])  # Available VAT rates
    default_vat_rate = Column(Float, default=21.0)

    # Invoice settings
    invoice_number_format = Column(String(50), default="YYYY-0001")  # e.g., 2025-0001
    invoice_next_number = Column(Integer, default=1)
    default_payment_terms = Column(Integer, default=30)  # Days

    # Peppol / e-invoicing settings
    peppol_enabled = Column(Boolean, default=False)
    peppol_participant_id = Column(String(100), nullable=True)

    # PayPal settings
    paypal_enabled = Column(Boolean, default=False)
    paypal_mode = Column(String(20), default="sandbox")  # sandbox or live
    paypal_client_id = Column(String(255), nullable=True)
    paypal_client_secret = Column(String(255), nullable=True)

    # Other settings
    default_currency = Column(String(10), default="EUR")
    legal_mentions = Column(Text, nullable=True)  # For invoices
    general_terms = Column(Text, nullable=True)  # Terms and conditions

    # SMTP / Email settings
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String(255), nullable=True)
    smtp_password = Column(String(255), nullable=True)
    smtp_from_email = Column(String(255), nullable=True)
    smtp_tls = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CompanySettings {self.company_name}>"

    def get_next_invoice_number(self) -> str:
        """Generate next invoice number based on format."""
        year = datetime.utcnow().year
        number = self.invoice_next_number
        # Format: YYYY-0001
        return f"{year}-{number:04d}"
