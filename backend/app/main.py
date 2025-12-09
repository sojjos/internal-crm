"""Main FastAPI application."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.database import Base, engine
from app.api.routes import (
    auth, users, company, clients, suppliers,
    articles, invoices, expenses, collaborators, reports, peppol, emails, purchases,
    documents, treasury, stock, interventions, quotes, crm
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Create upload directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "logos"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "invoices"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "receipts"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "payslips"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "purchases"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "documents"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "interventions"), exist_ok=True)

    yield

    # Shutdown
    pass


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Application de gestion pour PME - Facturation, Notes de frais, RH",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# API routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(company.router, prefix="/api/company", tags=["Company Settings"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["Suppliers"])
app.include_router(articles.router, prefix="/api/articles", tags=["Articles/Services"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["Invoices"])
app.include_router(expenses.router, prefix="/api/expenses", tags=["Expenses"])
app.include_router(collaborators.router, prefix="/api/collaborators", tags=["Collaborators & Payroll"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports & Exports"])
app.include_router(peppol.router, prefix="/api/peppol", tags=["Peppol Directory"])
app.include_router(emails.router, prefix="/api/emails", tags=["Email Client"])
app.include_router(purchases.router, prefix="/api/purchases", tags=["Purchases & Investments"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents GED"])
app.include_router(treasury.router, prefix="/api/treasury", tags=["Treasury & Cashflow"])
app.include_router(stock.router, prefix="/api/stock", tags=["Stock Management"])
app.include_router(interventions.router, prefix="/api/interventions", tags=["Interventions & Planning"])
app.include_router(quotes.router, prefix="/api/quotes", tags=["Quotes"])
app.include_router(crm.router, prefix="/api/crm", tags=["CRM & Pipeline"])


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "SME Management API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }
