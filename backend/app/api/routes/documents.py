"""Document management (GED) routes."""
from datetime import datetime
from typing import Any, List, Optional
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.document import Document, DocumentCategory, DocumentType
from app.schemas.document import (
    DocumentCategoryCreate, DocumentCategoryUpdate, DocumentCategoryResponse,
    DocumentCreate, DocumentUpdate, DocumentResponse
)

router = APIRouter()


# ============ Categories ============

@router.get("/categories", response_model=List[DocumentCategoryResponse])
def get_categories(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all document categories."""
    query = db.query(DocumentCategory)
    if is_active is not None:
        query = query.filter(DocumentCategory.is_active == is_active)
    return query.order_by(DocumentCategory.name).all()


@router.post("/categories", response_model=DocumentCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: DocumentCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new document category."""
    category = DocumentCategory(**category_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=DocumentCategoryResponse)
def update_category(
    category_id: int,
    category_in: DocumentCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a document category."""
    category = db.query(DocumentCategory).filter(DocumentCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    for field, value in category_in.model_dump(exclude_unset=True).items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


# ============ Documents ============

@router.get("/", response_model=List[DocumentResponse])
def get_documents(
    skip: int = 0,
    limit: int = 100,
    document_type: Optional[DocumentType] = None,
    category_id: Optional[int] = None,
    client_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    is_archived: bool = False,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all documents with optional filtering."""
    query = db.query(Document).options(
        joinedload(Document.category),
        joinedload(Document.client),
        joinedload(Document.supplier)
    )

    query = query.filter(Document.is_archived == is_archived)

    if document_type:
        query = query.filter(Document.document_type == document_type)
    if category_id:
        query = query.filter(Document.category_id == category_id)
    if client_id:
        query = query.filter(Document.client_id == client_id)
    if supplier_id:
        query = query.filter(Document.supplier_id == supplier_id)
    if search:
        query = query.filter(
            (Document.title.ilike(f"%{search}%")) |
            (Document.tags.ilike(f"%{search}%"))
        )

    documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    # Add related names
    result = []
    for doc in documents:
        doc_dict = {
            **doc.__dict__,
            "category_name": doc.category.name if doc.category else None,
            "client_name": doc.client.name if doc.client else None,
            "supplier_name": doc.supplier.name if doc.supplier else None,
        }
        result.append(doc_dict)

    return result


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Query(...),
    document_type: DocumentType = Query(DocumentType.AUTRE),
    category_id: Optional[int] = Query(None),
    description: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    client_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    purchase_id: Optional[int] = Query(None),
    contract_id: Optional[int] = Query(None),
    fixed_asset_id: Optional[int] = Query(None),
    collaborator_id: Optional[int] = Query(None),
    invoice_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Upload a new document."""
    # Create upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, "documents")
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else ""
    filename = f"doc_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_dir, filename)

    # Save file
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Create document record
    document = Document(
        title=title,
        description=description,
        document_type=document_type,
        category_id=category_id,
        file_path=filepath,
        file_name=file.filename,
        file_size=len(content),
        mime_type=file.content_type,
        tags=tags,
        client_id=client_id,
        supplier_id=supplier_id,
        purchase_id=purchase_id,
        contract_id=contract_id,
        fixed_asset_id=fixed_asset_id,
        collaborator_id=collaborator_id,
        invoice_id=invoice_id,
        created_by_id=current_user.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return document


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a specific document."""
    document = db.query(Document).options(
        joinedload(Document.category),
        joinedload(Document.client),
        joinedload(Document.supplier)
    ).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        **document.__dict__,
        "category_name": document.category.name if document.category else None,
        "client_name": document.client.name if document.client else None,
        "supplier_name": document.supplier.name if document.supplier else None,
    }


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    document_in: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a document metadata."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    for field, value in document_in.model_dump(exclude_unset=True).items():
        setattr(document, field, value)

    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete a document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()
    return {"message": "Document deleted"}


@router.get("/expiring/soon")
def get_expiring_documents(
    days: int = Query(30, description="Number of days to look ahead"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get documents expiring within specified days."""
    from datetime import timedelta

    cutoff = datetime.utcnow() + timedelta(days=days)

    documents = db.query(Document).filter(
        Document.expiry_date != None,
        Document.expiry_date <= cutoff,
        Document.is_archived == False
    ).order_by(Document.expiry_date).all()

    return documents
