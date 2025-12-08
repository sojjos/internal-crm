"""Client model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
import enum

from app.db.database import Base


class SendMethod(str, enum.Enum):
    """Preferred invoice sending method."""
    EMAIL = "email"
    PEPPOL = "peppol"


class Client(Base):
    """Client model for managing customers."""

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)

    # Basic information
    name = Column(String(255), nullable=False, index=True)  # Company name or individual
    contact_name = Column(String(255), nullable=True)  # Contact person
    address_street = Column(String(255), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_postal_code = Column(String(20), nullable=True)
    address_country = Column(String(100), default="Belgique")

    # Tax information
    vat_number = Column(String(50), nullable=True)  # Required for B2B
    is_business = Column(Boolean, default=True)  # B2B vs B2C

    # Contact information
    email = Column(String(255), nullable=True)  # Billing email
    phone = Column(String(50), nullable=True)

    # Invoicing preferences
    preferred_send_method = Column(
        Enum(SendMethod),
        default=SendMethod.EMAIL
    )
    peppol_id = Column(String(100), nullable=True)  # Peppol participant ID if applicable
    custom_payment_terms = Column(Integer, nullable=True)  # Override default payment terms

    # Internal notes
    notes = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Client {self.name}>"

    @property
    def full_address(self) -> str:
        """Return formatted full address."""
        parts = [
            self.address_street,
            f"{self.address_postal_code} {self.address_city}".strip(),
            self.address_country
        ]
        return "\n".join(p for p in parts if p)
