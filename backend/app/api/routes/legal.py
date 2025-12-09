"""Legal module API routes for Belgian corporate documents (PV, reports, publications)."""
from datetime import date, datetime
from typing import Any, List, Optional
import io

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.legal import (
    BoardMeeting, MeetingResolution, LegalDocument, ManagementReport,
    MoniteurPublication, CorporateOfficer, ShareRegister, UBORegister,
    MeetingType, DocumentLegalStatus, PublicationType,
    LEGAL_DOCUMENT_TEMPLATES, CORPORATE_FUNCTIONS
)
from app.models.annual_accounts import FiscalYear

router = APIRouter()


# Pydantic schemas
class BoardMeetingCreate(BaseModel):
    meeting_type: MeetingType
    title: str
    meeting_date: date
    meeting_time: Optional[str] = None
    location: Optional[str] = None
    is_virtual: bool = False
    convocation_date: Optional[date] = None
    agenda: Optional[str] = None


class BoardMeetingUpdate(BaseModel):
    title: Optional[str] = None
    meeting_date: Optional[date] = None
    meeting_time: Optional[str] = None
    location: Optional[str] = None
    agenda: Optional[str] = None
    minutes_content: Optional[str] = None
    decisions: Optional[list] = None
    attendees: Optional[list] = None
    quorum_reached: Optional[bool] = None


class BoardMeetingResponse(BaseModel):
    id: int
    reference: str
    meeting_type: MeetingType
    title: str
    status: DocumentLegalStatus
    meeting_date: date
    meeting_time: Optional[str]
    location: Optional[str]
    is_virtual: bool
    quorum_reached: bool
    president_name: Optional[str]
    secretary_name: Optional[str]
    filed_at_greffe: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ResolutionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    requires_publication: bool = False
    execution_deadline: Optional[date] = None


class ResolutionResponse(BaseModel):
    id: int
    meeting_id: int
    resolution_number: int
    title: str
    description: Optional[str]
    votes_for: int
    votes_against: int
    votes_abstain: int
    is_adopted: bool
    requires_publication: bool
    executed: bool

    class Config:
        from_attributes = True


class ManagementReportCreate(BaseModel):
    fiscal_year_id: int
    title: str


class ManagementReportResponse(BaseModel):
    id: int
    fiscal_year_id: int
    reference: str
    title: str
    status: DocumentLegalStatus
    board_approval_date: Optional[date]
    ag_approval_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


class CorporateOfficerCreate(BaseModel):
    name: str
    first_name: Optional[str] = None
    is_legal_person: bool = False
    enterprise_number: Optional[str] = None
    represented_by: Optional[str] = None
    function: str
    function_title: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    remuneration_type: Optional[str] = None
    annual_remuneration: Optional[float] = None
    powers_description: Optional[str] = None
    signature_power: Optional[str] = None


class CorporateOfficerResponse(BaseModel):
    id: int
    name: str
    first_name: Optional[str]
    is_legal_person: bool
    enterprise_number: Optional[str]
    function: str
    function_title: Optional[str]
    start_date: date
    end_date: Optional[date]
    is_active: bool
    nomination_published: bool

    class Config:
        from_attributes = True


class MoniteurPublicationCreate(BaseModel):
    publication_type: PublicationType
    title: str
    meeting_id: Optional[int] = None
    enterprise_number: str
    company_name: str
    legal_form: Optional[str] = None
    content_fr: Optional[str] = None
    content_nl: Optional[str] = None


class MoniteurPublicationResponse(BaseModel):
    id: int
    reference: str
    publication_type: PublicationType
    title: str
    status: DocumentLegalStatus
    enterprise_number: str
    company_name: str
    filed_date: Optional[date]
    published_date: Optional[date]
    publication_number: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UBORegisterCreate(BaseModel):
    name: str
    first_name: Optional[str] = None
    birth_date: Optional[date] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    ownership_type: str
    ownership_percentage: Optional[float] = None
    voting_rights_percentage: Optional[float] = None
    start_date: date


class UBORegisterResponse(BaseModel):
    id: int
    name: str
    first_name: Optional[str]
    ownership_type: str
    ownership_percentage: Optional[float]
    voting_rights_percentage: Optional[float]
    is_active: bool
    declared_to_spf: bool
    spf_declaration_date: Optional[date]

    class Config:
        from_attributes = True


# Board Meeting endpoints
@router.get("/meetings", response_model=List[BoardMeetingResponse])
def list_meetings(
    meeting_type: Optional[MeetingType] = None,
    status: Optional[DocumentLegalStatus] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List board meetings and assemblies."""
    query = db.query(BoardMeeting)

    if meeting_type:
        query = query.filter(BoardMeeting.meeting_type == meeting_type)
    if status:
        query = query.filter(BoardMeeting.status == status)
    if year:
        query = query.filter(
            func.extract('year', BoardMeeting.meeting_date) == year
        )

    return query.order_by(BoardMeeting.meeting_date.desc()).all()


@router.post("/meetings", response_model=BoardMeetingResponse)
def create_meeting(
    meeting_in: BoardMeetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new board meeting."""
    # Generate reference
    year = meeting_in.meeting_date.year
    type_prefix = {
        MeetingType.AG_ORDINAIRE: "AGO",
        MeetingType.AG_EXTRAORDINAIRE: "AGE",
        MeetingType.CA: "CA",
        MeetingType.COMITE_DIRECTION: "CD",
        MeetingType.AG_SPECIALE: "AGS",
    }.get(meeting_in.meeting_type, "PV")

    count = db.query(BoardMeeting).filter(
        func.extract('year', BoardMeeting.meeting_date) == year,
        BoardMeeting.meeting_type == meeting_in.meeting_type
    ).count()
    reference = f"PV-{type_prefix}-{year}-{count + 1:03d}"

    meeting = BoardMeeting(**meeting_in.model_dump(), reference=reference)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("/meetings/{meeting_id}", response_model=BoardMeetingResponse)
def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a meeting by ID."""
    meeting = db.query(BoardMeeting).filter(BoardMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.put("/meetings/{meeting_id}", response_model=BoardMeetingResponse)
def update_meeting(
    meeting_id: int,
    meeting_in: BoardMeetingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a meeting."""
    meeting = db.query(BoardMeeting).filter(BoardMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    update_data = meeting_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meeting, field, value)

    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("/meetings/{meeting_id}/approve")
def approve_meeting(
    meeting_id: int,
    president_name: str,
    secretary_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Approve and sign meeting minutes."""
    meeting = db.query(BoardMeeting).filter(BoardMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    meeting.status = DocumentLegalStatus.APPROVED
    meeting.president_name = president_name
    meeting.secretary_name = secretary_name
    meeting.signed_at = datetime.utcnow()

    db.commit()
    return {"message": "Meeting minutes approved"}


# Meeting Resolution endpoints
@router.get("/meetings/{meeting_id}/resolutions", response_model=List[ResolutionResponse])
def list_resolutions(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List resolutions for a meeting."""
    return db.query(MeetingResolution).filter(
        MeetingResolution.meeting_id == meeting_id
    ).order_by(MeetingResolution.resolution_number).all()


@router.post("/meetings/{meeting_id}/resolutions", response_model=ResolutionResponse)
def create_resolution(
    meeting_id: int,
    resolution_in: ResolutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Add a resolution to a meeting."""
    meeting = db.query(BoardMeeting).filter(BoardMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    count = db.query(MeetingResolution).filter(
        MeetingResolution.meeting_id == meeting_id
    ).count()

    resolution = MeetingResolution(
        meeting_id=meeting_id,
        resolution_number=count + 1,
        **resolution_in.model_dump()
    )
    db.add(resolution)
    db.commit()
    db.refresh(resolution)
    return resolution


@router.put("/meetings/{meeting_id}/resolutions/{res_id}/vote")
def record_vote(
    meeting_id: int,
    res_id: int,
    votes_for: int,
    votes_against: int,
    votes_abstain: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Record votes for a resolution."""
    resolution = db.query(MeetingResolution).filter(
        MeetingResolution.id == res_id,
        MeetingResolution.meeting_id == meeting_id
    ).first()
    if not resolution:
        raise HTTPException(status_code=404, detail="Resolution not found")

    resolution.votes_for = votes_for
    resolution.votes_against = votes_against
    resolution.votes_abstain = votes_abstain
    resolution.is_adopted = votes_for > votes_against

    db.commit()
    return {"message": "Vote recorded", "is_adopted": resolution.is_adopted}


# Management Report endpoints
@router.get("/management-reports", response_model=List[ManagementReportResponse])
def list_management_reports(
    fiscal_year_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List management reports."""
    query = db.query(ManagementReport)
    if fiscal_year_id:
        query = query.filter(ManagementReport.fiscal_year_id == fiscal_year_id)
    return query.order_by(ManagementReport.created_at.desc()).all()


@router.post("/management-reports", response_model=ManagementReportResponse)
def create_management_report(
    report_in: ManagementReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new management report."""
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.id == report_in.fiscal_year_id
    ).first()
    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    count = db.query(ManagementReport).filter(
        ManagementReport.fiscal_year_id == report_in.fiscal_year_id
    ).count()
    reference = f"RG-{fiscal_year.name}-{count + 1:03d}"

    report = ManagementReport(**report_in.model_dump(), reference=reference)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/management-reports/{report_id}")
def get_management_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a management report with all sections."""
    report = db.query(ManagementReport).filter(ManagementReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.put("/management-reports/{report_id}/section")
def update_report_section(
    report_id: int,
    section_name: str,
    content: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a section of the management report."""
    report = db.query(ManagementReport).filter(ManagementReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Map section names to fields
    section_map = {
        "situation_overview": "situation_overview",
        "significant_events": "significant_events",
        "future_outlook": "future_outlook",
        "rd_activities": "rd_activities",
        "branches": "branches",
        "financial_instruments": "financial_instruments",
        "own_shares": "own_shares",
        "profit_distribution": "profit_distribution",
        "corporate_governance": "corporate_governance",
    }

    if section_name not in section_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown section: {section_name}"
        )

    setattr(report, section_map[section_name], content)
    db.commit()
    return {"message": f"Section {section_name} updated"}


# Corporate Officer endpoints
@router.get("/officers", response_model=List[CorporateOfficerResponse])
def list_officers(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List corporate officers."""
    query = db.query(CorporateOfficer)
    if active_only:
        query = query.filter(CorporateOfficer.is_active == True)
    return query.order_by(CorporateOfficer.function, CorporateOfficer.name).all()


@router.post("/officers", response_model=CorporateOfficerResponse)
def create_officer(
    officer_in: CorporateOfficerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Add a corporate officer."""
    officer = CorporateOfficer(**officer_in.model_dump())
    db.add(officer)
    db.commit()
    db.refresh(officer)
    return officer


@router.put("/officers/{officer_id}", response_model=CorporateOfficerResponse)
def update_officer(
    officer_id: int,
    officer_in: CorporateOfficerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a corporate officer."""
    officer = db.query(CorporateOfficer).filter(CorporateOfficer.id == officer_id).first()
    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")

    update_data = officer_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(officer, field, value)

    db.commit()
    db.refresh(officer)
    return officer


@router.post("/officers/{officer_id}/end-mandate")
def end_mandate(
    officer_id: int,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """End an officer's mandate."""
    officer = db.query(CorporateOfficer).filter(CorporateOfficer.id == officer_id).first()
    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")

    officer.end_date = end_date
    officer.is_active = False
    db.commit()
    return {"message": "Mandate ended"}


# Moniteur Publication endpoints
@router.get("/publications", response_model=List[MoniteurPublicationResponse])
def list_publications(
    publication_type: Optional[PublicationType] = None,
    status: Optional[DocumentLegalStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List Moniteur Belge publications."""
    query = db.query(MoniteurPublication)
    if publication_type:
        query = query.filter(MoniteurPublication.publication_type == publication_type)
    if status:
        query = query.filter(MoniteurPublication.status == status)
    return query.order_by(MoniteurPublication.created_at.desc()).all()


@router.post("/publications", response_model=MoniteurPublicationResponse)
def create_publication(
    pub_in: MoniteurPublicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new publication request."""
    count = db.query(MoniteurPublication).count()
    reference = f"MB-{datetime.utcnow().year}-{count + 1:04d}"

    publication = MoniteurPublication(**pub_in.model_dump(), reference=reference)
    db.add(publication)
    db.commit()
    db.refresh(publication)
    return publication


@router.post("/publications/{pub_id}/file")
def file_publication(
    pub_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Mark publication as filed at greffe."""
    pub = db.query(MoniteurPublication).filter(MoniteurPublication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")

    pub.filed_date = date.today()
    pub.status = DocumentLegalStatus.FILED
    db.commit()
    return {"message": "Publication filed"}


# UBO Register endpoints
@router.get("/ubo", response_model=List[UBORegisterResponse])
def list_ubo(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List UBO (Ultimate Beneficial Owners)."""
    query = db.query(UBORegister)
    if active_only:
        query = query.filter(UBORegister.is_active == True)
    return query.all()


@router.post("/ubo", response_model=UBORegisterResponse)
def create_ubo(
    ubo_in: UBORegisterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Add a UBO entry."""
    ubo = UBORegister(**ubo_in.model_dump())
    db.add(ubo)
    db.commit()
    db.refresh(ubo)
    return ubo


@router.post("/ubo/{ubo_id}/declare-spf")
def declare_to_spf(
    ubo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Mark UBO as declared to SPF."""
    ubo = db.query(UBORegister).filter(UBORegister.id == ubo_id).first()
    if not ubo:
        raise HTTPException(status_code=404, detail="UBO not found")

    ubo.declared_to_spf = True
    ubo.spf_declaration_date = date.today()
    ubo.spf_reference = f"UBO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    db.commit()
    return {"message": "Declared to SPF", "reference": ubo.spf_reference}


# Reference data
@router.get("/templates")
def get_templates(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get legal document templates."""
    return LEGAL_DOCUMENT_TEMPLATES


@router.get("/functions")
def get_corporate_functions(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get corporate function types."""
    return CORPORATE_FUNCTIONS


# Generate document
@router.post("/meetings/{meeting_id}/generate-pv")
def generate_pv_document(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Generate PV document for a meeting."""
    meeting = db.query(BoardMeeting).filter(BoardMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Get resolutions
    resolutions = db.query(MeetingResolution).filter(
        MeetingResolution.meeting_id == meeting_id
    ).order_by(MeetingResolution.resolution_number).all()

    # Generate document content
    content = _generate_pv_content(meeting, resolutions)

    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=PV_{meeting.reference}.txt"
        }
    )


def _generate_pv_content(meeting: BoardMeeting, resolutions: List[MeetingResolution]) -> str:
    """Generate PV document content."""
    meeting_type_names = {
        MeetingType.AG_ORDINAIRE: "l'Assemblee Generale Ordinaire",
        MeetingType.AG_EXTRAORDINAIRE: "l'Assemblee Generale Extraordinaire",
        MeetingType.CA: "du Conseil d'Administration",
        MeetingType.COMITE_DIRECTION: "du Comite de Direction",
        MeetingType.AG_SPECIALE: "l'Assemblee Generale Speciale",
    }

    content = f"""
PROCES-VERBAL DE {meeting_type_names.get(meeting.meeting_type, 'la reunion').upper()}

Reference: {meeting.reference}
Date: {meeting.meeting_date.strftime('%d/%m/%Y')}
{"Heure: " + meeting.meeting_time if meeting.meeting_time else ""}
Lieu: {meeting.location or "Siege social"}

---

ORDRE DU JOUR
{meeting.agenda or "(Non specifie)"}

---

DELIBERATIONS ET DECISIONS

"""

    for res in resolutions:
        content += f"""
RESOLUTION N°{res.resolution_number}: {res.title}
{res.description or ""}

Resultat du vote:
- Pour: {res.votes_for}
- Contre: {res.votes_against}
- Abstentions: {res.votes_abstain}

La resolution est {"ADOPTEE" if res.is_adopted else "REJETEE"}.

"""

    content += f"""
---

CLOTURE

L'ordre du jour etant epuise, la seance est levee.

{"President: " + meeting.president_name if meeting.president_name else ""}
{"Secretaire: " + meeting.secretary_name if meeting.secretary_name else ""}

Date de signature: {meeting.signed_at.strftime('%d/%m/%Y') if meeting.signed_at else "(Non signe)"}
"""

    return content
