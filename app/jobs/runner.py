from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.domain import Run, Scenario, Dataset, Transaction
from app.simulation.engine import run_simulation, EngineConfig, DemandLine

def process_run_job(session: Session, run_id: str):
    run = session.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise Exception("Run not found")
        
    scenario = session.query(Scenario).filter(Scenario.id == run.scenario_id).first()
    if not scenario:
        raise Exception("Scenario not found")
        
    transactions = session.query(Transaction).filter(Transaction.dataset_id == scenario.dataset_id).order_by(Transaction.transaction_date).all()
    
    demand = []
    for t in transactions:
        demand.append(DemandLine(
            date=t.transaction_date.date(),
            product_id=t.product_id,
            quantity=t.quantity
        ))
        
    config = EngineConfig(**scenario.config_json)
    
    metrics = run_simulation(config, demand)
    
    run.summary = {
        "demanded_units": metrics.demanded_units,
        "fulfilled_units": metrics.fulfilled_units,
        "fill_rate": metrics.fill_rate,
        "total_revenue": metrics.total_revenue,
        "total_cost": metrics.total_cost,
        "net_profit": metrics.net_profit,
        "peak_inventory": metrics.peak_inventory,
        "stockout_days": metrics.stockout_days
    }
    
    run.status = "succeeded"
    run.completed_at = datetime.now(timezone.utc)
    session.commit()
