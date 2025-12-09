"""Document management schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.models.document import DocumentType


class DocumentCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#6B7280"
    icon: Optional[str] = None


class DocumentCategoryCreate(DocumentCategoryBase):
    pass


class DocumentCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class DocumentCategoryResponse(DocumentCategoryBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    document_type: DocumentType = DocumentType.AUTRE
    category_id: Optional[int] = None
    document_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    tags: Optional[str] = None
    client_id: Optional[int] = None
    supplier_id: Optional[int] = None
    purchase_id: Optional[int] = None
    contract_id: Optional[int] = None
    fixed_asset_id: Optional[int] = None
    collaborator_id: Optional[int] = None
    invoice_id: Optional[int] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[DocumentType] = None
    category_id: Optional[int] = None
    document_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    tags: Optional[str] = None
    is_archived: Optional[bool] = None


class DocumentResponse(DocumentBase):
    id: int
    file_path: str
    file_name: str
    file_size: Optional[int]
    mime_type: Optional[str]
    is_archived: bool
    created_at: datetime

    # Related entity names (for display)
    category_name: Optional[str] = None
    client_name: Optional[str] = None
    supplier_name: Optional[str] = None

    class Config:
        from_attributes = True
