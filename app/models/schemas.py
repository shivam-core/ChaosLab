from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

class WorkspaceResponse(BaseModel):
    id: str
    token: str
    expires_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UploadResponse(BaseModel):
    id: str
    workspace_id: str
    original_name: str
    mime_type: str
    byte_count: int
    status: str
    
    model_config = ConfigDict(from_attributes=True)

class DatasetSummary(BaseModel):
    id: str
    name: str
    currency: Optional[str]
    coverage_start: Optional[datetime]
    coverage_end: Optional[datetime]
    status: str
    
    model_config = ConfigDict(from_attributes=True)

class ScenarioCreate(BaseModel):
    dataset_id: str
    name: str
    config_json: Dict[str, Any]

class ScenarioResponse(BaseModel):
    id: str
    name: str
    dataset_id: str
    config_json: Dict[str, Any]
    revision: int
    
    model_config = ConfigDict(from_attributes=True)

class RunResponse(BaseModel):
    id: str
    scenario_id: str
    status: str
    summary: Optional[Dict[str, Any]]
    completed_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)

class ReportResponse(BaseModel):
    id: str
    status: str
    
    model_config = ConfigDict(from_attributes=True)
