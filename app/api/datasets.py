from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_workspace_id
from app.models.domain import Dataset
from app.models.schemas import DatasetSummary

router = APIRouter()

@router.get("/", response_model=List[DatasetSummary])
def list_datasets(
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db)
):
    datasets = db.query(Dataset).filter(Dataset.workspace_id == workspace_id).all()
    
    return [
        DatasetSummary(
            id=d.id,
            name=d.name,
            currency=d.currency,
            coverage_start=d.coverage_start,
            coverage_end=d.coverage_end,
            status="ready"
        )
        for d in datasets
    ]

@router.get("/{dataset_id}", response_model=DatasetSummary)
def get_dataset(
    dataset_id: str,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.workspace_id == workspace_id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    return DatasetSummary(
        id=dataset.id,
        name=dataset.name,
        currency=dataset.currency,
        coverage_start=dataset.coverage_start,
        coverage_end=dataset.coverage_end,
        status="ready"
    )
