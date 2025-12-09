"""CRM and pipeline routes."""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.crm import (
    ClientTag, ClientTagAssociation, Opportunity, ContactActivity, CRMTask,
    PipelineStage, TaskStatus, TaskPriority
)
from app.models.client import Client
from app.schemas.crm import (
    ClientTagCreate, ClientTagUpdate, ClientTagResponse,
    OpportunityCreate, OpportunityUpdate, OpportunityResponse,
    ContactActivityCreate, ContactActivityResponse,
    CRMTaskCreate, CRMTaskUpdate, CRMTaskResponse,
    PipelineSummary, CRMDashboard
)

router = APIRouter()


# ============ Tags ============

@router.get("/tags", response_model=List[ClientTagResponse])
def get_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return db.query(ClientTag).order_by(ClientTag.name).all()


@router.post("/tags", response_model=ClientTagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_in: ClientTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    tag = ClientTag(**tag_in.model_dump())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.put("/tags/{tag_id}", response_model=ClientTagResponse)
def update_tag(
    tag_id: int,
    tag_in: ClientTagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    tag = db.query(ClientTag).filter(ClientTag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    for field, value in tag_in.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)

    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/tags/{tag_id}")
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    tag = db.query(ClientTag).filter(ClientTag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    db.delete(tag)
    db.commit()
    return {"message": "Tag deleted"}


@router.post("/clients/{client_id}/tags/{tag_id}")
def add_tag_to_client(
    client_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Check if already exists
    existing = db.query(ClientTagAssociation).filter(
        ClientTagAssociation.client_id == client_id,
        ClientTagAssociation.tag_id == tag_id
    ).first()

    if existing:
        return {"message": "Tag already assigned"}

    assoc = ClientTagAssociation(client_id=client_id, tag_id=tag_id)
    db.add(assoc)
    db.commit()
    return {"message": "Tag added"}


@router.delete("/clients/{client_id}/tags/{tag_id}")
def remove_tag_from_client(
    client_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    assoc = db.query(ClientTagAssociation).filter(
        ClientTagAssociation.client_id == client_id,
        ClientTagAssociation.tag_id == tag_id
    ).first()

    if assoc:
        db.delete(assoc)
        db.commit()

    return {"message": "Tag removed"}


# ============ Opportunities ============

@router.get("/opportunities", response_model=List[OpportunityResponse])
def get_opportunities(
    skip: int = 0,
    limit: int = 100,
    stage: Optional[PipelineStage] = None,
    assigned_to_id: Optional[int] = None,
    client_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    query = db.query(Opportunity).options(
        joinedload(Opportunity.client),
        joinedload(Opportunity.assigned_to)
    )

    if stage:
        query = query.filter(Opportunity.stage == stage)
    if assigned_to_id:
        query = query.filter(Opportunity.assigned_to_id == assigned_to_id)
    if client_id:
        query = query.filter(Opportunity.client_id == client_id)

    # Exclude closed (won/lost) by default, unless specific stage requested
    if not stage:
        query = query.filter(Opportunity.stage.notin_([
            PipelineStage.GAGNE, PipelineStage.PERDU
        ]))

    opportunities = query.order_by(Opportunity.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            **o.__dict__,
            "client_name": o.client.name if o.client else o.prospect_company,
            "assigned_to_name": f"{o.assigned_to.first_name} {o.assigned_to.last_name}" if o.assigned_to else None,
            "weighted_value": (o.estimated_value or 0) * o.probability / 100 if o.estimated_value else None,
        }
        for o in opportunities
    ]


@router.post("/opportunities", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    opportunity_in: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    opportunity = Opportunity(**opportunity_in.model_dump())
    opportunity.created_by_id = current_user.id
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    return opportunity


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
def get_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    opportunity = db.query(Opportunity).options(
        joinedload(Opportunity.client),
        joinedload(Opportunity.assigned_to),
        joinedload(Opportunity.activities),
        joinedload(Opportunity.tasks)
    ).filter(Opportunity.id == opportunity_id).first()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    return {
        **opportunity.__dict__,
        "client_name": opportunity.client.name if opportunity.client else opportunity.prospect_company,
        "assigned_to_name": f"{opportunity.assigned_to.first_name} {opportunity.assigned_to.last_name}" if opportunity.assigned_to else None,
        "weighted_value": (opportunity.estimated_value or 0) * opportunity.probability / 100 if opportunity.estimated_value else None,
    }


@router.put("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
def update_opportunity(
    opportunity_id: int,
    opportunity_in: OpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    opportunity = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id
    ).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    update_data = opportunity_in.model_dump(exclude_unset=True)

    # Handle stage transitions
    if "stage" in update_data:
        new_stage = update_data["stage"]
        if new_stage == PipelineStage.GAGNE:
            opportunity.won_at = datetime.utcnow()
        elif new_stage == PipelineStage.PERDU:
            opportunity.lost_at = datetime.utcnow()

    for field, value in update_data.items():
        setattr(opportunity, field, value)

    db.commit()
    db.refresh(opportunity)
    return opportunity


@router.delete("/opportunities/{opportunity_id}")
def delete_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    opportunity = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id
    ).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    db.delete(opportunity)
    db.commit()
    return {"message": "Opportunity deleted"}


@router.post("/opportunities/{opportunity_id}/convert-to-client")
def convert_prospect_to_client(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Convert a prospect opportunity to a client."""
    opportunity = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id
    ).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    if opportunity.client_id:
        raise HTTPException(status_code=400, detail="Already linked to a client")

    if not opportunity.prospect_company:
        raise HTTPException(status_code=400, detail="No prospect company name")

    # Create client
    client = Client(
        name=opportunity.prospect_company,
        contact_name=opportunity.prospect_contact,
        email=opportunity.prospect_email,
        phone=opportunity.prospect_phone,
        is_active=True
    )
    db.add(client)
    db.flush()

    # Link opportunity to new client
    opportunity.client_id = client.id

    db.commit()

    return {"message": "Prospect converted to client", "client_id": client.id}


# ============ Activities ============

@router.get("/activities", response_model=List[ContactActivityResponse])
def get_activities(
    skip: int = 0,
    limit: int = 50,
    client_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    query = db.query(ContactActivity).options(
        joinedload(ContactActivity.client)
    )

    if client_id:
        query = query.filter(ContactActivity.client_id == client_id)
    if opportunity_id:
        query = query.filter(ContactActivity.opportunity_id == opportunity_id)

    activities = query.order_by(
        ContactActivity.activity_date.desc()
    ).offset(skip).limit(limit).all()

    return [
        {
            **a.__dict__,
            "client_name": a.client.name if a.client else None,
        }
        for a in activities
    ]


@router.post("/activities", response_model=ContactActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity_in: ContactActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    activity = ContactActivity(**activity_in.model_dump())
    activity.created_by_id = current_user.id
    if not activity.activity_date:
        activity.activity_date = datetime.utcnow()
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


# ============ Tasks ============

@router.get("/tasks", response_model=List[CRMTaskResponse])
def get_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TaskStatus] = None,
    assigned_to_id: Optional[int] = None,
    client_id: Optional[int] = None,
    overdue_only: bool = False,
    due_today: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    query = db.query(CRMTask).options(
        joinedload(CRMTask.client),
        joinedload(CRMTask.assigned_to),
        joinedload(CRMTask.opportunity)
    )

    if status:
        query = query.filter(CRMTask.status == status)
    else:
        # By default, show non-completed tasks
        query = query.filter(CRMTask.status.in_([TaskStatus.A_FAIRE, TaskStatus.EN_COURS]))

    if assigned_to_id:
        query = query.filter(CRMTask.assigned_to_id == assigned_to_id)
    if client_id:
        query = query.filter(CRMTask.client_id == client_id)

    now = datetime.utcnow()
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())

    if overdue_only:
        query = query.filter(
            CRMTask.due_date < now,
            CRMTask.status.in_([TaskStatus.A_FAIRE, TaskStatus.EN_COURS])
        )
    if due_today:
        query = query.filter(
            CRMTask.due_date >= today_start,
            CRMTask.due_date <= today_end
        )

    tasks = query.order_by(CRMTask.due_date.asc().nullslast()).offset(skip).limit(limit).all()

    return [
        {
            **t.__dict__,
            "client_name": t.client.name if t.client else None,
            "assigned_to_name": f"{t.assigned_to.first_name} {t.assigned_to.last_name}" if t.assigned_to else None,
            "opportunity_name": t.opportunity.name if t.opportunity else None,
        }
        for t in tasks
    ]


@router.post("/tasks", response_model=CRMTaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: CRMTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    task = CRMTask(**task_in.model_dump())
    task.created_by_id = current_user.id
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/tasks/{task_id}", response_model=CRMTaskResponse)
def update_task(
    task_id: int,
    task_in: CRMTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    task = db.query(CRMTask).filter(CRMTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_in.model_dump(exclude_unset=True)

    # Handle completion
    if update_data.get("status") == TaskStatus.TERMINE:
        task.completed_at = datetime.utcnow()
        task.completed_by_id = current_user.id

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    task = db.query(CRMTask).filter(CRMTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = TaskStatus.TERMINE
    task.completed_at = datetime.utcnow()
    task.completed_by_id = current_user.id
    db.commit()

    return {"message": "Task completed"}


@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    task = db.query(CRMTask).filter(CRMTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}


# ============ Pipeline ============

@router.get("/pipeline")
def get_pipeline_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get pipeline stage summary."""
    result = []
    for stage in PipelineStage:
        opps = db.query(Opportunity).filter(Opportunity.stage == stage).all()
        count = len(opps)
        total_value = sum(o.estimated_value or 0 for o in opps)

        result.append({
            "stage": stage.value,
            "count": count,
            "total_value": float(total_value)
        })

    return result


@router.put("/opportunities/{opportunity_id}/stage")
def update_opportunity_stage(
    opportunity_id: int,
    stage: PipelineStage = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update opportunity stage."""
    opportunity = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id
    ).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Handle stage transitions
    if stage == PipelineStage.GAGNE:
        opportunity.won_at = datetime.utcnow()
    elif stage == PipelineStage.PERDU:
        opportunity.lost_at = datetime.utcnow()

    opportunity.stage = stage
    db.commit()

    return {"message": "Stage updated", "stage": stage.value}


# ============ Dashboard ============

@router.get("/dashboard")
def get_crm_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get CRM dashboard data."""
    # Pipeline summary
    pipeline_data = []
    for stage in PipelineStage:
        if stage in [PipelineStage.GAGNE, PipelineStage.PERDU]:
            continue

        opps = db.query(Opportunity).filter(Opportunity.stage == stage).all()
        count = len(opps)
        total_value = sum(o.estimated_value or 0 for o in opps)
        weighted_value = sum(
            (o.estimated_value or 0) * o.probability / 100
            for o in opps
        )

        pipeline_data.append({
            "stage": stage,
            "count": count,
            "total_value": float(total_value),
            "weighted_value": float(weighted_value)
        })

    # Totals
    active_opps = db.query(Opportunity).filter(
        Opportunity.stage.notin_([PipelineStage.GAGNE, PipelineStage.PERDU])
    ).all()

    total_opportunities = len(active_opps)
    total_value = sum(o.estimated_value or 0 for o in active_opps)
    weighted_value = sum(
        (o.estimated_value or 0) * o.probability / 100
        for o in active_opps
    )

    # Tasks
    now = datetime.utcnow()
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())

    tasks_due_today = db.query(func.count(CRMTask.id)).filter(
        CRMTask.due_date >= today_start,
        CRMTask.due_date <= today_end,
        CRMTask.status.in_([TaskStatus.A_FAIRE, TaskStatus.EN_COURS])
    ).scalar() or 0

    tasks_overdue = db.query(func.count(CRMTask.id)).filter(
        CRMTask.due_date < now,
        CRMTask.status.in_([TaskStatus.A_FAIRE, TaskStatus.EN_COURS])
    ).scalar() or 0

    # Recent activities
    recent_activities = db.query(ContactActivity).options(
        joinedload(ContactActivity.client)
    ).order_by(
        ContactActivity.activity_date.desc()
    ).limit(10).all()

    return {
        "pipeline_summary": pipeline_data,
        "total_opportunities": total_opportunities,
        "total_value": float(total_value),
        "weighted_value": float(weighted_value),
        "tasks_due_today": tasks_due_today,
        "tasks_overdue": tasks_overdue,
        "recent_activities": [
            {
                **a.__dict__,
                "client_name": a.client.name if a.client else None,
            }
            for a in recent_activities
        ]
    }
