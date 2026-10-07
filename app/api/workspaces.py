import uuid
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.domain import Workspace
from app.models.schemas import WorkspaceResponse

router = APIRouter()

@router.post("/", response_model=WorkspaceResponse)
def create_workspace(db: Session = Depends(get_db)):
    workspace_id = str(uuid.uuid4())
    token = secrets.token_hex(32)
    token_digest = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    workspace = Workspace(
        id=workspace_id,
        token_digest=token_digest,
        expires_at=expires_at
    )
    
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    
    return WorkspaceResponse(
        id=workspace_id,
        token=token,
        expires_at=expires_at
    )
