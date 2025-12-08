"""Collaborator and payroll models."""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float,
    Enum, ForeignKey, Date
)
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base


class ContractType(str, enum.Enum):
    """Contract type."""
    CDI = "cdi"  # Permanent contract
    CDD = "cdd"  # Fixed-term contract
    FREELANCE = "freelance"  # Freelancer/independent
    INTERN = "intern"  # Internship
    MANAGER = "manager"  # Contrat gérant


class Collaborator(Base):
    """Collaborator/employee model."""

    __tablename__ = "collaborators"

    id = Column(Integer, primary_key=True, index=True)

    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Address
    address_street = Column(String(255), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_postal_code = Column(String(20), nullable=True)
    address_country = Column(String(100), default="Belgique")

    # Contract information
    contract_type = Column(Enum(ContractType), default=ContractType.CDI)
    manager_type = Column(String(100), nullable=True)  # For manager contracts only
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Salary information (informative only - not for legal calculations)
    gross_salary = Column(Float, nullable=True)  # Monthly gross salary
    hourly_rate = Column(Float, nullable=True)  # Hourly rate if applicable

    # Banking
    iban = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payslips = relationship("Payslip", back_populates="collaborator")

    def __repr__(self):
        return f"<Collaborator {self.first_name} {self.last_name}>"

    @property
    def full_name(self) -> str:
        """Return full name."""
        return f"{self.first_name} {self.last_name}"


class PayrollPeriod(Base):
    """Payroll period for internal tracking."""

    __tablename__ = "payroll_periods"

    id = Column(Integer, primary_key=True, index=True)

    # Period identifier (e.g., "2025-03")
    period = Column(String(7), unique=True, nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    # Status
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime, nullable=True)

    # Export tracking
    exported_at = Column(DateTime, nullable=True)
    export_file_path = Column(String(500), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PayrollPeriod {self.period}>"


class Payslip(Base):
    """Payslip storage - for storing PDF payslips from social secretariat."""

    __tablename__ = "payslips"

    id = Column(Integer, primary_key=True, index=True)

    # Collaborator
    collaborator_id = Column(Integer, ForeignKey("collaborators.id"), nullable=False)
    collaborator = relationship("Collaborator", back_populates="payslips")

    # Period
    period = Column(String(7), nullable=False)  # e.g., "2025-03"

    # File
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Payslip {self.collaborator_id} - {self.period}>"
