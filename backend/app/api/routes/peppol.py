"""Peppol Directory API routes."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.peppol_service import peppol_directory


router = APIRouter()


class PeppolSearchResult(BaseModel):
    """Peppol participant search result."""
    total_count: int
    page_index: int
    page_count: int
    matches: list


class PeppolValidationResult(BaseModel):
    """Peppol participant validation result."""
    valid: bool
    registered: bool
    message: str
    participant_id: str
    name: Optional[str] = None
    country: Optional[str] = None
    can_receive_invoice: bool
    document_types: Optional[list] = None
    registration_date: Optional[str] = None


@router.get("/search", response_model=PeppolSearchResult)
async def search_peppol_participants(
    participant_id: Optional[str] = Query(None, description="Exact Peppol participant ID"),
    name: Optional[str] = Query(None, min_length=3, description="Company name (min 3 chars)"),
    country: Optional[str] = Query(None, min_length=2, max_length=2, description="Country code (e.g., BE, FR)"),
    page: int = Query(0, ge=0, description="Page index (0-based)"),
    limit: int = Query(20, ge=1, le=100, description="Results per page")
):
    """Search for participants in the Peppol Directory.

    The Peppol Directory allows searching for registered e-invoicing participants.
    Rate limited to 2 requests per second.

    Args:
        participant_id: Exact Peppol participant ID (e.g., "0208:0123456789" for Belgian enterprises)
        name: Partial business name (minimum 3 characters)
        country: ISO country code (e.g., "BE" for Belgium)
        page: Page index for pagination
        limit: Number of results per page (max 100)

    Returns:
        Search results with participant information
    """
    if not participant_id and not name and not country:
        raise HTTPException(
            status_code=400,
            detail="At least one search parameter is required (participant_id, name, or country)"
        )

    try:
        result = await peppol_directory.search_participant(
            participant_id=participant_id,
            name=name,
            country=country,
            page_index=page,
            page_count=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate/{participant_id}", response_model=PeppolValidationResult)
async def validate_peppol_participant(participant_id: str):
    """Validate a Peppol participant ID.

    Checks if the participant is registered in the Peppol Directory
    and can receive invoices.

    Args:
        participant_id: The Peppol participant ID to validate
                       (e.g., "0208:0123456789" for Belgian enterprise number)

    Returns:
        Validation result with participant details if found
    """
    try:
        result = await peppol_directory.validate_participant(participant_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lookup/belgian/{enterprise_number}")
async def lookup_belgian_company(enterprise_number: str):
    """Lookup a Belgian company by enterprise number (KBO/BCE).

    Args:
        enterprise_number: Belgian enterprise number (e.g., "0123456789" or "BE0123456789")

    Returns:
        Company Peppol registration details if found
    """
    # Clean enterprise number
    clean_num = enterprise_number.replace(".", "").replace(" ", "").replace("BE", "")

    try:
        # Search with Belgian scheme ID (0208)
        result = await peppol_directory.validate_participant(f"0208:{clean_num}")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/belgian")
async def search_belgian_companies(
    name: Optional[str] = Query(None, min_length=3, description="Company name (min 3 chars)"),
    page: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Search for Belgian companies in the Peppol Directory.

    Args:
        name: Company name to search (minimum 3 characters)
        page: Page index
        limit: Results per page

    Returns:
        List of matching Belgian Peppol participants
    """
    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name parameter is required (minimum 3 characters)"
        )

    try:
        result = await peppol_directory.search_participant(
            name=name,
            country="BE",
            page_index=page,
            page_count=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
