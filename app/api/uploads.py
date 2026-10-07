import hashlib
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_workspace_id
from app.models.domain import Upload, Job
from app.models.schemas import UploadResponse

router = APIRouter()

@router.post("/", response_model=UploadResponse)
def upload_file(
    file: UploadFile = File(...),
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db)
):
    if file.content_type not in ["text/csv", "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        pass # Allow anyway for testing, but typically we'd restrict
        
    content = file.file.read()
    byte_count = len(content)
    
    # 50MB limit
    if byte_count > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")
        
    sha256_hash = hashlib.sha256(content).hexdigest()
    
    upload = Upload(
        workspace_id=workspace_id,
        original_name=file.filename or "unknown",
        mime_type=file.content_type or "application/octet-stream",
        byte_count=byte_count,
        sha256_hash=sha256_hash,
        raw_bytes=content,
        status="uploaded"
    )
    
    db.add(upload)
    db.commit()
    db.refresh(upload)
    
    # Create Parse Job
    job = Job(
        kind="parse",
        workspace_id=workspace_id,
        resource_id=upload.id,
        status="queued"
    )
    db.add(job)
    db.commit()
    
    return UploadResponse(
        id=upload.id,
        workspace_id=workspace_id,
        original_name=upload.original_name,
        mime_type=upload.mime_type,
        byte_count=upload.byte_count,
        status=upload.status
    )
