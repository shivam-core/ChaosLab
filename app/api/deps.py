import os
from typing import Generator, Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import hashlib
from datetime import datetime, timezone

from app.models.domain import Workspace

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chaos:chaos@localhost/chaoslab").replace("postgres://", "postgresql://")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_workspace_id(x_workspace_token: Optional[str] = Header(None), db: Session = Depends(get_db)) -> str:
    if not x_workspace_token:
        raise HTTPException(status_code=401, detail="X-Workspace-Token header missing")
        
    token_digest = hashlib.sha256(x_workspace_token.encode()).hexdigest()
    
    workspace = db.query(Workspace).filter(Workspace.token_digest == token_digest).first()
    if not workspace:
        raise HTTPException(status_code=401, detail="Invalid workspace token")
        
    if workspace.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Workspace token expired")
        
    return workspace.id
