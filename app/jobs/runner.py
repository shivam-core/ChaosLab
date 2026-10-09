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
        
    dataset = session.query(Dataset).filter(Dataset.id == scenario.dataset_id).first()
    if not dataset:
        raise Exception("Dataset not found")
        
    transactions = session.query(Transaction).filter(Transaction.dataset_id == scenario.dataset_id).order_by(Transaction.transaction_date).all()
    
    demand = []
    products = set()
    for t in transactions:
        arrival_day = (t.transaction_date.date() - dataset.coverage_start).days + 1
        demand.append(DemandLine(
            id=t.id,
            product_id=t.product_id,
            arrival_day=arrival_day,
            requested_qty=t.quantity,
            unit_price_minor=t.unit_price_minor or 0,
            remaining_qty=t.quantity
        ))
        products.add(t.product_id)
        
    config = EngineConfig(**scenario.config_json)
    
    config_products = set(config.starting_stock.keys()) | set(config.reorder_point.keys())
    all_products = list(products | config_products)
    
    result = run_simulation(config, demand, all_products)
    
    run.summary = {
        "demanded_units": result.metrics.get("demanded_units", 0),
        "fulfilled_units": result.metrics.get("fulfilled_units", 0),
        "fill_rate": result.metrics.get("fill_rate", 0),
        "total_revenue": result.metrics.get("total_revenue", 0),
        "total_cost": result.metrics.get("total_cost", 0),
        "net_profit": result.metrics.get("net_profit", 0),
        "peak_inventory": result.metrics.get("peak_inventory", 0),
        "stockout_days": result.metrics.get("stockout_days", 0)
    }
    
    run.status = "succeeded"
    run.completed_at = datetime.now(timezone.utc)
    session.commit()

