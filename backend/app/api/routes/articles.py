"""Article/Service catalog routes."""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.article import Article, ArticleType, BillingMode
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleResponse

router = APIRouter()


@router.get("/", response_model=List[ArticleResponse])
def get_articles(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    article_type: Optional[ArticleType] = None,
    billing_mode: Optional[BillingMode] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all articles with optional filtering."""
    query = db.query(Article)

    if search:
        query = query.filter(
            Article.code.ilike(f"%{search}%") |
            Article.name.ilike(f"%{search}%")
        )

    if article_type:
        query = query.filter(Article.article_type == article_type)

    if billing_mode:
        query = query.filter(Article.billing_mode == billing_mode)

    if is_active is not None:
        query = query.filter(Article.is_active == is_active)

    articles = query.order_by(Article.code).offset(skip).limit(limit).all()
    return articles


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article(
    article_in: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new article."""
    # Check if code already exists
    existing = db.query(Article).filter(Article.code == article_in.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article code already exists"
        )

    article = Article(**article_in.model_dump())
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a specific article."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    return article


@router.get("/code/{code}", response_model=ArticleResponse)
def get_article_by_code(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get article by code."""
    article = db.query(Article).filter(Article.code == code).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    return article


@router.put("/{article_id}", response_model=ArticleResponse)
def update_article(
    article_id: int,
    article_in: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update an article."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    update_data = article_in.model_dump(exclude_unset=True)

    # Check code uniqueness if updating
    if "code" in update_data:
        existing = db.query(Article).filter(
            Article.code == update_data["code"],
            Article.id != article_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Article code already exists"
            )

    for field, value in update_data.items():
        setattr(article, field, value)

    db.commit()
    db.refresh(article)
    return article


@router.delete("/{article_id}")
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete an article (deactivate)."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    article.is_active = False
    db.commit()

    return {"message": "Article deactivated"}
