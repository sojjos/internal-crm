"""Supplier model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text

from app.db.database import Base


class Supplier(Base):
    """Supplier/vendor model."""

    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)

    # Basic information
    name = Column(String(255), nullable=False, index=True)
    contact_name = Column(String(255), nullable=True)
    address_street = Column(String(255), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_postal_code = Column(String(20), nullable=True)
    address_country = Column(String(100), default="Belgique")

    # Tax information
    vat_number = Column(String(50), nullable=True)

    # Contact information
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Supplier type
    supplier_type = Column(String(100), nullable=True)  # materials, services, fuel, etc.

    # Internal notes
    notes = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Supplier {self.name}>"
