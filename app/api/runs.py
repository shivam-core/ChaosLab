from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_workspace_id
from app.models.domain import Run, Scenario, Job
from app.models.schemas import RunResponse

router = APIRouter()

class RunCreate(BaseModel):
    scenario_id: str

@router.post("/", response_model=RunResponse)
def start_run(
    req: RunCreate,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db)
):
    scenario = db.query(Scenario).filter(
        Scenario.id == req.scenario_id,
        Scenario.workspace_id == workspace_id
    ).first()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    run = Run(
        workspace_id=workspace_id,
        scenario_id=req.scenario_id,
        status="queued"
    )
    
    db.add(run)
    db.commit()
    db.refresh(run)
    
    job = Job(
        kind="run",
        workspace_id=workspace_id,
        resource_id=run.id,
        status="queued"
    )
    
    db.add(job)
    db.commit()
    
    return RunResponse(
        id=run.id,
        scenario_id=run.scenario_id,
        status=run.status,
        summary=run.summary,
        completed_at=run.completed_at
    )

@router.get("/{run_id}", response_model=RunResponse)
def get_run(
    run_id: str,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db)
):
    run = db.query(Run).filter(
        Run.id == run_id,
        Run.workspace_id == workspace_id
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    return RunResponse(
        id=run.id,
        scenario_id=run.scenario_id,
        status=run.status,
        summary=run.summary,
        completed_at=run.completed_at
    )
