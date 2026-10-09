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
        t_date = t.transaction_date.date() if isinstance(t.transaction_date, datetime) else t.transaction_date
        coverage_start_date = dataset.coverage_start.date() if isinstance(dataset.coverage_start, datetime) else dataset.coverage_start
        arrival_day = (t_date - coverage_start_date).days + 1
        demand.append(DemandLine(
            id=t.id,
            product_id=t.product_id,
            arrival_day=arrival_day,
            requested_qty=t.quantity,
            unit_price_minor=t.unit_price_minor or 0,
            remaining_qty=t.quantity
        ))
        products.add(t.product_id)
        
    ui_config = scenario.config_json or {}
    products_list = list(products)
    
    starting_inv = ui_config.get("starting_inventory", 100)
    lead_time_days = ui_config.get("lead_time_days", 7)
    
    horizon = 30
    if dataset.coverage_end and dataset.coverage_start:
        c_end = dataset.coverage_end.date() if isinstance(dataset.coverage_end, datetime) else dataset.coverage_end
        c_start = dataset.coverage_start.date() if isinstance(dataset.coverage_start, datetime) else dataset.coverage_start
        horizon = (c_end - c_start).days + 1
        
    config = EngineConfig(
        horizon=horizon,
        capacity=10000,
        starting_stock={p: starting_inv for p in products_list},
        reorder_point={p: starting_inv for p in products_list},
        reorder_qty={p: starting_inv for p in products_list},
        lead_time={p: lead_time_days for p in products_list},
        opening_deliveries=[],
        capacity_reductions={},
        supplier_delays={}
    )
    
    all_products = products_list
    
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
    
    run.results = {
        "snapshots": result.snapshots
    }
    
    run.status = "succeeded"
    run.completed_at = datetime.now(timezone.utc)
    session.commit()

