"""Pydantic schemas for API validation."""
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin, Token
from app.schemas.company import CompanySettingsCreate, CompanySettingsUpdate, CompanySettingsResponse
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleResponse
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    InvoiceLineCreate, InvoiceLineUpdate, InvoiceLineResponse
)
from app.schemas.expense import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse,
    ExpenseTypeCreate, ExpenseTypeUpdate, ExpenseTypeResponse
)
from app.schemas.collaborator import (
    CollaboratorCreate, CollaboratorUpdate, CollaboratorResponse,
    PayrollPeriodCreate, PayrollPeriodResponse,
    PayslipCreate, PayslipResponse
)

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin", "Token",
    "CompanySettingsCreate", "CompanySettingsUpdate", "CompanySettingsResponse",
    "ClientCreate", "ClientUpdate", "ClientResponse",
    "SupplierCreate", "SupplierUpdate", "SupplierResponse",
    "ArticleCreate", "ArticleUpdate", "ArticleResponse",
    "InvoiceCreate", "InvoiceUpdate", "InvoiceResponse",
    "InvoiceLineCreate", "InvoiceLineUpdate", "InvoiceLineResponse",
    "ExpenseCreate", "ExpenseUpdate", "ExpenseResponse",
    "ExpenseTypeCreate", "ExpenseTypeUpdate", "ExpenseTypeResponse",
    "CollaboratorCreate", "CollaboratorUpdate", "CollaboratorResponse",
    "PayrollPeriodCreate", "PayrollPeriodResponse",
    "PayslipCreate", "PayslipResponse",
]
