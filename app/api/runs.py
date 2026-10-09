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
        status="queued",
        engine_version="1.0"
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
        results=run.results,
        completed_at=run.completed_at
    )

from fastapi.responses import Response
import io
from reportlab.pdfgen import canvas

@router.get("/{run_id}/report/download")
def download_run_report(
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
        
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "ChaosLab Retail Simulation Report")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 770, f"Run ID: {run.id}")
    p.drawString(100, 750, f"Status: {run.status}")
    if run.completed_at:
        p.drawString(100, 730, f"Completed At: {run.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
    y = 690
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, y, "Simulation Results Summary:")
    y -= 25
    p.setFont("Helvetica", 12)
    
    if run.summary:
        for k, v in run.summary.items():
            if isinstance(v, float):
                v_str = f"{v:.2f}"
            else:
                v_str = str(v)
            p.drawString(120, y, f"{k.replace('_', ' ').title()}: {v_str}")
            y -= 20
    else:
        p.drawString(120, y, "No results summary available yet.")
        
    p.showPage()
    p.save()
    
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{run_id}.pdf"}
    )
