from sqlalchemy.orm import Session
from app.models.domain import Report

def process_pdf_job(session: Session, report_id: str):
    report = session.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise Exception("Report not found")
        
    # We will generate real PDF later. For now, mark ready
    report.status = "ready"
    session.commit()
