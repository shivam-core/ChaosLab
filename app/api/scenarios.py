import hashlib
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_workspace_id
from app.models.domain import Scenario, Dataset
from app.models.schemas import ScenarioCreate, ScenarioResponse

router = APIRouter()

@router.post("/", response_model=ScenarioResponse)
def create_scenario(
    req: ScenarioCreate,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(
        Dataset.id == req.dataset_id,
        Dataset.workspace_id == workspace_id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    config_str = json.dumps(req.config_json, sort_keys=True)
    config_hash = hashlib.sha256(config_str.encode()).hexdigest()
    
    scenario = Scenario(
        workspace_id=workspace_id,
        dataset_id=req.dataset_id,
        name=req.name,
        config_json=req.config_json,
        config_hash=config_hash,
        revision=1
    )
    
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    
    return ScenarioResponse(
        id=scenario.id,
        name=scenario.name,
        dataset_id=scenario.dataset_id,
        config_json=scenario.config_json,
        revision=scenario.revision
    )

@router.get("/", response_model=List[ScenarioResponse])
def list_scenarios(
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db)
):
    scenarios = db.query(Scenario).filter(Scenario.workspace_id == workspace_id).all()
    
    return [
        ScenarioResponse(
            id=s.id,
            name=s.name,
            dataset_id=s.dataset_id,
            config_json=s.config_json,
            revision=s.revision
        ) for s in scenarios
    ]
