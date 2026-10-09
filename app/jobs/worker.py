import time
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import sys

# Setup paths so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.models.domain import Job, Run, Report, Upload
from app.simulation.engine import run_simulation, EngineConfig, DemandLine
from app.jobs.parser import process_parse_job
from app.jobs.runner import process_run_job
from app.jobs.pdf import process_pdf_job

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chaos:chaos@localhost/chaoslab").replace("postgres://", "postgresql://")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def claim_job(session) -> Job | None:
    # Find a queued or expired job and lock it
    now = datetime.now(timezone.utc)
    
    # We use raw SQL for the SKIP LOCKED part because SQLAlchemy's support varies, but actually SQLAlchemy supports with_for_update(skip_locked=True)
    # Let's use SQLAlchemy ORM
    
    job = session.query(Job).filter(
        (Job.status == "queued") | 
        ((Job.status == "running") & (Job.lease_expiry < now))
    ).with_for_update(skip_locked=True).first()
    
    if job:
        job.status = "running"
        job.lease_token = str(uuid.uuid4())
        job.lease_expiry = now + timedelta(seconds=60)
        job.attempt_count += 1
        session.commit()
        return job
    
    session.rollback()
    return None

def process_job(job_id: int, job_kind: str, resource_id: str):
    print(f"Processing job {job_id} of kind {job_kind} for resource {resource_id}")
    
    with SessionLocal() as session:
        try:
            if job_kind == "run":
                process_run_job(session, resource_id)
                    
            elif job_kind == "parse":
                process_parse_job(session, resource_id)
                    
            elif job_kind == "pdf":
                process_pdf_job(session, resource_id)
                    
            # Mark job complete
            db_job = session.query(Job).filter(Job.id == job_id).first()
            if db_job:
                db_job.status = "succeeded"
            
            session.commit()
            print(f"Successfully processed job {job_id}")
            
        except Exception as e:
            session.rollback()
            db_job = session.query(Job).filter(Job.id == job_id).first()
            if db_job:
                db_job.status = "failed"
                db_job.safe_error = str(e)
                session.commit()
            print(f"Failed job {job_id}: {e}")

def main():
    print("Starting background worker loop...")
    while True:
        with SessionLocal() as session:
            job = claim_job(session)
            if job:
                job_id = job.id
                job_kind = job.kind
                resource_id = job.resource_id
            else:
                job_id = None
                
        if job_id:
            process_job(job_id, job_kind, resource_id)
        else:
            time.sleep(2)

if __name__ == "__main__":
    main()
