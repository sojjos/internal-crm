"""Purchase routes for the Purchases & Investments module."""
from datetime import date
from typing import Any, List, Optional
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.supplier import Supplier
from app.models.purchase import (
    Purchase, PurchaseCategory, PurchaseContract, FixedAsset, DepreciationEntry,
    PurchaseStatus
)
from app.schemas.purchase import (
    # Categories
    PurchaseCategoryCreate, PurchaseCategoryUpdate, PurchaseCategoryResponse,
    # Contracts
    PurchaseContractCreate, PurchaseContractUpdate, PurchaseContractResponse,
    PurchaseContractWithSupplier,
    # Purchases
    PurchaseCreate, PurchaseUpdate, PurchaseResponse, PurchaseWithDetails,
    PurchaseCalculation,
    # Fixed Assets
    FixedAssetCreate, FixedAssetUpdate, FixedAssetResponse, FixedAssetWithDepreciation,
    DepreciationEntryResponse,
    # Reports
    PurchaseSummary, VATReport, PCMNReport, InvestmentReport,
)
from app.services.purchase_service import (
    calculate_vat_amounts, should_be_investment, get_category_defaults,
    create_depreciation_schedule, save_depreciation_schedule,
    get_next_billing_dates, generate_purchases_from_contracts,
    get_purchases_summary, get_vat_report, get_pcmn_report, get_investment_report
)

router = APIRouter()


# ============ Purchase Categories ============

@router.get("/categories", response_model=List[PurchaseCategoryResponse])
def get_categories(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all purchase categories."""
    query = db.query(PurchaseCategory)
    if is_active is not None:
        query = query.filter(PurchaseCategory.is_active == is_active)
    return query.order_by(PurchaseCategory.name).all()


@router.post("/categories", response_model=PurchaseCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: PurchaseCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new purchase category."""
    existing = db.query(PurchaseCategory).filter(
        PurchaseCategory.name == category_in.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category already exists"
        )

    category = PurchaseCategory(**category_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/categories/{category_id}", response_model=PurchaseCategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a specific purchase category."""
    category = db.query(PurchaseCategory).filter(
        PurchaseCategory.id == category_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.put("/categories/{category_id}", response_model=PurchaseCategoryResponse)
def update_category(
    category_id: int,
    category_in: PurchaseCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a purchase category."""
    category = db.query(PurchaseCategory).filter(
        PurchaseCategory.id == category_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    update_data = category_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete a purchase category."""
    category = db.query(PurchaseCategory).filter(
        PurchaseCategory.id == category_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Check if category is in use
    purchase_count = db.query(Purchase).filter(
        Purchase.category_id == category_id
    ).count()
    if purchase_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category with {purchase_count} purchases"
        )

    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}


@router.get("/categories/{category_id}/defaults")
def get_category_default_values(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get default values for a category (for form pre-filling)."""
    category = db.query(PurchaseCategory).filter(
        PurchaseCategory.id == category_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return get_category_defaults(category)


# ============ Purchase Contracts ============

@router.get("/contracts", response_model=List[PurchaseContractWithSupplier])
def get_contracts(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    supplier_id: Optional[int] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all purchase contracts."""
    query = db.query(PurchaseContract).options(
        joinedload(PurchaseContract.supplier),
        joinedload(PurchaseContract.category)
    )

    if is_active is not None:
        query = query.filter(PurchaseContract.is_active == is_active)
    if supplier_id:
        query = query.filter(PurchaseContract.supplier_id == supplier_id)
    if category_id:
        query = query.filter(PurchaseContract.category_id == category_id)

    contracts = query.order_by(PurchaseContract.name).offset(skip).limit(limit).all()

    # Add supplier and category names
    result = []
    for c in contracts:
        contract_dict = {
            "id": c.id,
            "supplier_id": c.supplier_id,
            "category_id": c.category_id,
            "contract_type": c.contract_type,
            "name": c.name,
            "description": c.description,
            "reference": c.reference,
            "start_date": c.start_date,
            "end_date": c.end_date,
            "periodicity": c.periodicity,
            "amount_htva": c.amount_htva,
            "vat_rate": c.vat_rate,
            "payment_method": c.payment_method,
            "billing_day": c.billing_day,
            "vehicle_type": c.vehicle_type,
            "vehicle_co2": c.vehicle_co2,
            "vehicle_registration": c.vehicle_registration,
            "is_active": c.is_active,
            "next_billing_date": c.next_billing_date,
            "created_at": c.created_at,
            "amount_ttc": c.amount_ttc,
            "monthly_amount": c.monthly_amount,
            "supplier_name": c.supplier.name if c.supplier else None,
            "category_name": c.category.name if c.category else None,
        }
        result.append(contract_dict)

    return result


@router.post("/contracts", response_model=PurchaseContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract_in: PurchaseContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new purchase contract."""
    # Verify supplier exists
    supplier = db.query(Supplier).filter(Supplier.id == contract_in.supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )

    # Verify category exists
    category = db.query(PurchaseCategory).filter(
        PurchaseCategory.id == contract_in.category_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    contract = PurchaseContract(**contract_in.model_dump())
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


@router.get("/contracts/{contract_id}", response_model=PurchaseContractWithSupplier)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a specific purchase contract."""
    contract = db.query(PurchaseContract).options(
        joinedload(PurchaseContract.supplier),
        joinedload(PurchaseContract.category)
    ).filter(PurchaseContract.id == contract_id).first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    return {
        **contract.__dict__,
        "supplier_name": contract.supplier.name if contract.supplier else None,
        "category_name": contract.category.name if contract.category else None,
    }


@router.put("/contracts/{contract_id}", response_model=PurchaseContractResponse)
def update_contract(
    contract_id: int,
    contract_in: PurchaseContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a purchase contract."""
    contract = db.query(PurchaseContract).filter(
        PurchaseContract.id == contract_id
    ).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    update_data = contract_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)

    db.commit()
    db.refresh(contract)
    return contract


@router.delete("/contracts/{contract_id}")
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete a purchase contract."""
    contract = db.query(PurchaseContract).filter(
        PurchaseContract.id == contract_id
    ).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    # Soft delete by deactivating
    contract.is_active = False
    db.commit()
    return {"message": "Contract deactivated"}


@router.get("/contracts/{contract_id}/billing-dates")
def get_contract_billing_dates(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get next billing dates for a contract."""
    contract = db.query(PurchaseContract).filter(
        PurchaseContract.id == contract_id
    ).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    dates = get_next_billing_dates(contract)
    return {"billing_dates": dates}


@router.post("/contracts/generate-purchases")
def generate_contract_purchases(
    for_date: date = Query(..., description="Date for which to generate purchases"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Generate purchases from active contracts for a specific date."""
    contracts = db.query(PurchaseContract).filter(
        PurchaseContract.is_active == True
    ).all()

    generated = generate_purchases_from_contracts(db, contracts, for_date)
    return {
        "message": f"Generated {len(generated)} purchases",
        "purchase_ids": [p.id for p in generated]
    }


# ============ Purchases ============

@router.get("/", response_model=List[PurchaseWithDetails])
def get_purchases(
    skip: int = 0,
    limit: int = 100,
    supplier_id: Optional[int] = None,
    category_id: Optional[int] = None,
    contract_id: Optional[int] = None,
    status: Optional[PurchaseStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    is_investment: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all purchases with optional filtering."""
    query = db.query(Purchase).options(
        joinedload(Purchase.supplier),
        joinedload(Purchase.category),
        joinedload(Purchase.contract)
    )

    if supplier_id:
        query = query.filter(Purchase.supplier_id == supplier_id)
    if category_id:
        query = query.filter(Purchase.category_id == category_id)
    if contract_id:
        query = query.filter(Purchase.contract_id == contract_id)
    if status:
        query = query.filter(Purchase.status == status)
    if date_from:
        query = query.filter(Purchase.purchase_date >= date_from)
    if date_to:
        query = query.filter(Purchase.purchase_date <= date_to)
    if is_investment is not None:
        query = query.filter(Purchase.is_investment == is_investment)

    purchases = query.order_by(Purchase.purchase_date.desc()).offset(skip).limit(limit).all()

    result = []
    for p in purchases:
        purchase_dict = {
            "id": p.id,
            "supplier_id": p.supplier_id,
            "category_id": p.category_id,
            "contract_id": p.contract_id,
            "purchase_date": p.purchase_date,
            "supplier_invoice_number": p.supplier_invoice_number,
            "description": p.description,
            "amount_htva": p.amount_htva,
            "vat_rate": p.vat_rate,
            "vat_amount": p.vat_amount,
            "vat_deductible_rate": p.vat_deductible_rate,
            "vat_deductible_amount": p.vat_deductible_amount,
            "vat_non_deductible_amount": p.vat_non_deductible_amount,
            "fiscal_deductible_rate": p.fiscal_deductible_rate,
            "amount_ttc": p.amount_ttc,
            "pcmn_account": p.pcmn_account,
            "is_investment": p.is_investment,
            "fixed_asset_id": p.fixed_asset_id,
            "payment_method": p.payment_method,
            "payment_date": p.payment_date,
            "payment_reference": p.payment_reference,
            "status": p.status,
            "document_path": p.document_path,
            "created_at": p.created_at,
            "supplier_name": p.supplier.name if p.supplier else None,
            "category_name": p.category.name if p.category else None,
            "contract_name": p.contract.name if p.contract else None,
        }
        result.append(purchase_dict)

    return result


@router.post("/", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
def create_purchase(
    purchase_in: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new purchase."""
    # Verify supplier exists
    supplier = db.query(Supplier).filter(Supplier.id == purchase_in.supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )

    # Verify category exists
    category = db.query(PurchaseCategory).filter(
        PurchaseCategory.id == purchase_in.category_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Get category defaults if not specified
    vat_deductible_rate = purchase_in.vat_deductible_rate or category.default_vat_deductible_rate
    fiscal_deductible_rate = purchase_in.fiscal_deductible_rate or category.default_fiscal_deductible_rate
    pcmn_account = purchase_in.pcmn_account or category.pcmn_account

    # Calculate VAT amounts
    vat_amount, vat_deductible, vat_non_deductible, amount_ttc = calculate_vat_amounts(
        purchase_in.amount_htva,
        purchase_in.vat_rate,
        vat_deductible_rate
    )

    # Check if should be investment
    is_investment = purchase_in.is_investment or should_be_investment(
        category, purchase_in.amount_htva
    )

    # Create purchase
    purchase_data = purchase_in.model_dump(exclude={
        'create_fixed_asset', 'asset_name', 'asset_type',
        'depreciation_years', 'service_start_date',
        'vat_deductible_rate', 'fiscal_deductible_rate', 'pcmn_account'
    })

    purchase = Purchase(
        **purchase_data,
        vat_amount=vat_amount,
        vat_deductible_rate=vat_deductible_rate,
        vat_deductible_amount=vat_deductible,
        vat_non_deductible_amount=vat_non_deductible,
        fiscal_deductible_rate=fiscal_deductible_rate,
        pcmn_account=pcmn_account,
        is_investment=is_investment,
        status=PurchaseStatus.BROUILLON,
    )
    db.add(purchase)
    db.flush()  # Get purchase ID

    # Create fixed asset if requested
    if purchase_in.create_fixed_asset and is_investment:
        asset = FixedAsset(
            purchase_id=purchase.id,
            name=purchase_in.asset_name or purchase_in.description,
            asset_type=purchase_in.asset_type or category.default_asset_type,
            pcmn_account=category.pcmn_account,
            acquisition_value=purchase_in.amount_htva,
            service_start_date=purchase_in.service_start_date or purchase_in.purchase_date,
            depreciation_years=purchase_in.depreciation_years or category.default_depreciation_years or 5,
            depreciation_method=category.default_depreciation_method,
        )
        db.add(asset)
        db.flush()
        purchase.fixed_asset_id = asset.id

        # Generate depreciation schedule
        save_depreciation_schedule(db, asset)

    db.commit()
    db.refresh(purchase)
    return purchase


@router.get("/{purchase_id}", response_model=PurchaseWithDetails)
def get_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a specific purchase."""
    purchase = db.query(Purchase).options(
        joinedload(Purchase.supplier),
        joinedload(Purchase.category),
        joinedload(Purchase.contract)
    ).filter(Purchase.id == purchase_id).first()

    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )

    return {
        **purchase.__dict__,
        "supplier_name": purchase.supplier.name if purchase.supplier else None,
        "category_name": purchase.category.name if purchase.category else None,
        "contract_name": purchase.contract.name if purchase.contract else None,
    }


@router.put("/{purchase_id}", response_model=PurchaseResponse)
def update_purchase(
    purchase_id: int,
    purchase_in: PurchaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a purchase."""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )

    update_data = purchase_in.model_dump(exclude_unset=True)

    # Recalculate VAT if amounts changed
    if any(k in update_data for k in ['amount_htva', 'vat_rate', 'vat_deductible_rate']):
        amount_htva = update_data.get('amount_htva', purchase.amount_htva)
        vat_rate = update_data.get('vat_rate', purchase.vat_rate)
        vat_deductible_rate = update_data.get('vat_deductible_rate', purchase.vat_deductible_rate)

        vat_amount, vat_deductible, vat_non_deductible, _ = calculate_vat_amounts(
            amount_htva, vat_rate, vat_deductible_rate
        )

        update_data['vat_amount'] = vat_amount
        update_data['vat_deductible_amount'] = vat_deductible
        update_data['vat_non_deductible_amount'] = vat_non_deductible

    for field, value in update_data.items():
        setattr(purchase, field, value)

    db.commit()
    db.refresh(purchase)
    return purchase


@router.delete("/{purchase_id}")
def delete_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete a purchase."""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )

    if purchase.status == PurchaseStatus.VALIDE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a validated purchase"
        )

    # Delete associated fixed asset if exists
    if purchase.fixed_asset_id:
        db.query(DepreciationEntry).filter(
            DepreciationEntry.asset_id == purchase.fixed_asset_id
        ).delete()
        db.query(FixedAsset).filter(FixedAsset.id == purchase.fixed_asset_id).delete()

    db.delete(purchase)
    db.commit()
    return {"message": "Purchase deleted"}


@router.post("/{purchase_id}/validate")
def validate_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Validate a purchase."""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )

    purchase.status = PurchaseStatus.VALIDE
    db.commit()
    return {"message": "Purchase validated"}


@router.post("/{purchase_id}/document")
async def upload_purchase_document(
    purchase_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Upload document (invoice) for a purchase."""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )

    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed: PNG, JPEG, PDF"
        )

    # Create upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, "purchases")
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"purchase_{purchase_id}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_dir, filename)

    # Save file
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Update purchase
    purchase.document_path = filepath
    db.commit()

    return {"document_path": filepath}


@router.post("/calculate", response_model=PurchaseCalculation)
def calculate_purchase_amounts(
    calculation: PurchaseCalculation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Calculate VAT amounts for a purchase (preview before creating)."""
    vat_amount, vat_deductible, vat_non_deductible, amount_ttc = calculate_vat_amounts(
        calculation.amount_htva,
        calculation.vat_rate,
        calculation.vat_deductible_rate
    )

    return {
        "amount_htva": calculation.amount_htva,
        "vat_rate": calculation.vat_rate,
        "vat_deductible_rate": calculation.vat_deductible_rate,
        "fiscal_deductible_rate": calculation.fiscal_deductible_rate,
        "vat_amount": vat_amount,
        "vat_deductible_amount": vat_deductible,
        "vat_non_deductible_amount": vat_non_deductible,
        "amount_ttc": amount_ttc,
    }


# ============ Fixed Assets ============

@router.get("/assets", response_model=List[FixedAssetResponse])
def get_fixed_assets(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all fixed assets."""
    query = db.query(FixedAsset)

    if is_active is not None:
        query = query.filter(FixedAsset.is_active == is_active)

    return query.order_by(FixedAsset.service_start_date.desc()).offset(skip).limit(limit).all()


@router.post("/assets", response_model=FixedAssetResponse, status_code=status.HTTP_201_CREATED)
def create_fixed_asset(
    asset_in: FixedAssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new fixed asset (standalone, without purchase)."""
    asset = FixedAsset(**asset_in.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Generate depreciation schedule
    save_depreciation_schedule(db, asset)

    return asset


@router.get("/assets/{asset_id}", response_model=FixedAssetWithDepreciation)
def get_fixed_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a specific fixed asset with depreciation schedule."""
    asset = db.query(FixedAsset).options(
        joinedload(FixedAsset.depreciation_entries),
        joinedload(FixedAsset.purchase)
    ).filter(FixedAsset.id == asset_id).first()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixed asset not found"
        )

    return asset


@router.put("/assets/{asset_id}", response_model=FixedAssetResponse)
def update_fixed_asset(
    asset_id: int,
    asset_in: FixedAssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a fixed asset."""
    asset = db.query(FixedAsset).filter(FixedAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixed asset not found"
        )

    update_data = asset_in.model_dump(exclude_unset=True)

    # Check if depreciation needs recalculation
    recalc_needed = any(k in update_data for k in [
        'residual_value', 'depreciation_years', 'depreciation_method'
    ])

    for field, value in update_data.items():
        setattr(asset, field, value)

    if recalc_needed:
        save_depreciation_schedule(db, asset)

    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/assets/{asset_id}")
def delete_fixed_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete a fixed asset."""
    asset = db.query(FixedAsset).filter(FixedAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixed asset not found"
        )

    # Delete depreciation entries
    db.query(DepreciationEntry).filter(DepreciationEntry.asset_id == asset_id).delete()
    db.delete(asset)
    db.commit()
    return {"message": "Fixed asset deleted"}


@router.post("/assets/{asset_id}/regenerate-depreciation")
def regenerate_depreciation(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Regenerate depreciation schedule for an asset."""
    asset = db.query(FixedAsset).filter(FixedAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixed asset not found"
        )

    entries = save_depreciation_schedule(db, asset)
    return {
        "message": f"Regenerated {len(entries)} depreciation entries",
        "entries": [DepreciationEntryResponse.model_validate(e) for e in entries]
    }


# ============ Reports ============

@router.get("/reports/summary", response_model=PurchaseSummary)
def get_purchase_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get purchase summary for a period."""
    return get_purchases_summary(db, start_date, end_date)


@router.get("/reports/vat", response_model=VATReport)
def get_vat_report_endpoint(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get VAT report for a period (purchases + sales)."""
    return get_vat_report(db, start_date, end_date)


@router.get("/reports/pcmn", response_model=PCMNReport)
def get_pcmn_report_endpoint(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get PCMN report for a period."""
    return get_pcmn_report(db, start_date, end_date)


@router.get("/reports/investments", response_model=InvestmentReport)
def get_investment_report_endpoint(
    as_of_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get investment/fixed assets report."""
    return get_investment_report(db, as_of_date)
