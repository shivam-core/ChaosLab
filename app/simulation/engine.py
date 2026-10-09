import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any

@dataclass
class DemandLine:
    id: str
    product_id: str
    arrival_day: int
    requested_qty: int
    unit_price_minor: int
    remaining_qty: int

@dataclass
class Purchase:
    id: str
    product_id: str
    placed_day: int
    arrival_day: int
    qty: int

@dataclass
class EngineConfig:
    horizon: int
    capacity: int
    starting_stock: Dict[str, int]
    reorder_point: Dict[str, int]
    reorder_qty: Dict[str, int]
    lead_time: Dict[str, int]
    opening_deliveries: List[Purchase] = field(default_factory=list)
    capacity_reductions: Dict[int, int] = field(default_factory=dict) # day -> reduction %
    supplier_delays: Dict[str, Dict[int, int]] = field(default_factory=dict) # product -> day -> extra delay

@dataclass
class Shipment:
    day: int
    line_id: str
    product_id: str
    shipped_qty: int
    unit_price_minor: int

@dataclass
class EngineResult:
    snapshots: List[Dict[str, Any]]
    shipments: List[Shipment]
    metrics: Dict[str, Any]
    purchases: List[Purchase]
    remaining_backlog: List[DemandLine]
    engine_version: str = "2.0.0"

def run_simulation(config: EngineConfig, frozen_demand: List[DemandLine], products: List[str]) -> EngineResult:
    stock = {p: config.starting_stock.get(p, 0) for p in products}
    backlog: List[DemandLine] = []
    shipments: List[Shipment] = []
    purchases: List[Purchase] = list(config.opening_deliveries)
    snapshots = []
    
    # Sort frozen demand by day, then product_id for deterministic appending
    frozen_demand_sorted = sorted(frozen_demand, key=lambda d: (d.arrival_day, d.product_id, d.id))
    demand_by_day = {}
    for d in frozen_demand_sorted:
        demand_by_day.setdefault(d.arrival_day, []).append(d)
        
    purchase_counter = 1

    for day in range(1, config.horizon + 1):
        # 1. Receive due purchases
        for p in purchases:
            if p.arrival_day == day:
                stock[p.product_id] += p.qty
                
        # 2. Add today's demand
        today_demand = demand_by_day.get(day, [])
        for line in today_demand:
            # Copy line so we don't mutate the frozen input
            backlog.append(DemandLine(
                id=line.id, product_id=line.product_id, arrival_day=line.arrival_day,
                requested_qty=line.requested_qty, unit_price_minor=line.unit_price_minor,
                remaining_qty=line.requested_qty
            ))
            
        # 3. Calculate capacity
        reduction_pct = config.capacity_reductions.get(day, 0)
        cap = math.floor(config.capacity * (1 - reduction_pct / 100.0))
        
        # 4. Allocate units to backlog (FIFO)
        for line in backlog:
            if line.remaining_qty > 0 and stock[line.product_id] > 0 and cap > 0:
                shipped = min(line.remaining_qty, stock[line.product_id], cap)
                stock[line.product_id] -= shipped
                line.remaining_qty -= shipped
                cap -= shipped
                shipments.append(Shipment(
                    day=day, line_id=line.id, product_id=line.product_id,
                    shipped_qty=shipped, unit_price_minor=line.unit_price_minor
                ))

        # 5. Attribute residual backlog causes
        # Virtual stock traversal to not double-count
        virtual_stock = stock.copy()
        virtual_cap = cap
        stock_blocked_p_days = set()
        
        for line in backlog:
            if line.remaining_qty > 0:
                # If we have virtual stock but no virtual capacity, it is capacity-blocked
                if virtual_stock[line.product_id] > 0:
                    virtual_stock[line.product_id] -= min(line.remaining_qty, virtual_stock[line.product_id])
                    # No capacity means it's capacity blocked. We don't deduct virtual cap since it's already 0 if blocked
                else:
                    stock_blocked_p_days.add(line.product_id)

        # 6. Reorder decisions
        for product in sorted(products):
            r_qty = config.reorder_qty.get(product, 0)
            if r_qty <= 0:
                continue # disabled
                
            on_order = sum(p.qty for p in purchases if p.product_id == product and p.arrival_day > day)
            current_backlog = sum(l.remaining_qty for l in backlog if l.product_id == product)
            position = stock[product] + on_order - current_backlog
            
            if position <= config.reorder_point.get(product, 0):
                delay = config.supplier_delays.get(product, {}).get(day, 0)
                arr_day = day + config.lead_time.get(product, 0) + delay
                purchases.append(Purchase(
                    id=f"PO-{day}-{product}-{purchase_counter}",
                    product_id=product, placed_day=day, arrival_day=arr_day, qty=r_qty
                ))
                purchase_counter += 1

        # 7. Record end of day snapshot
        snapshots.append({
            "day": day,
            "inventory": stock.copy(),
            "stock_blocked_products": list(stock_blocked_p_days),
            "effective_capacity": math.floor(config.capacity * (1 - reduction_pct / 100.0)),
            "remaining_capacity": cap,
            "backlog_units": sum(l.remaining_qty for l in backlog),
            "shipped_units_today": sum(s.shipped_qty for s in shipments if s.day == day)
        })

    # Filter out fully shipped backlog
    remaining_backlog = [l for l in backlog if l.remaining_qty > 0]
    
    # Calculate global metrics
    demanded_units = sum(l.requested_qty for l in frozen_demand)
    fulfilled_units = sum(s.shipped_qty for s in shipments)
    fill_rate = (fulfilled_units / demanded_units * 100) if demanded_units else None
    
    total_revenue = sum(s.shipped_qty * s.unit_price_minor for s in shipments) / 100.0
    total_cost = 0 # Not modelled in basic retail config but needed by UI
    net_profit = total_revenue - total_cost
    
    peak_inventory = 0
    stockout_days = 0
    for snap in snapshots:
        total_inv = sum(snap['inventory'].values())
        if total_inv > peak_inventory:
            peak_inventory = total_inv
        
        # Calculate backlogs for this day
        if len(snap['stock_blocked_products']) > 0:
            stockout_days += 1

    
    metrics = {
        "demanded_units": demanded_units,
        "fulfilled_units": fulfilled_units,
        "ending_backlog": demanded_units - fulfilled_units,
        "fill_rate": fill_rate,
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "net_profit": net_profit,
        "peak_inventory": peak_inventory,
        "stockout_days": stockout_days
    }

    return EngineResult(
        snapshots=snapshots,
        shipments=shipments,
        metrics=metrics,
        purchases=purchases,
        remaining_backlog=remaining_backlog
    )
