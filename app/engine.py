import random
from collections import Counter

STATES = (
    "queued", "processing", "retry_wait",
    "succeeded", "rejected", "dead_letter",
)
CATEGORIES = ("books", "stationery", "electronics", "essentials")
MAX_ORDERS = 300
MAX_ATTEMPTS = 3

def new_state(lab_id, token_hash, now, seed=41):
    return {
        "schema_version": 1,
        "lab_id": lab_id, "token_hash": token_hash,
        "created_at": now, "expires_at": now + 7200,
        "revision": 0, "seed": seed, "sequence": 0,
        "event_sequence": 0,
        "controls": {
            "generating": False, "paused": False,
            "temporary_errors": False,
        },
        "generation_until": None, "next_generation_at": now,
        "next_sample_at": now,
        "orders": [], "events": [], "samples": [],
        "commands": {},
    }

def emit(s, now, kind, message, order=None):
    s["event_sequence"] += 1
    s["events"].append({
        "id": s["event_sequence"], "time": now,
        "type": kind, "message": message,
        "order_id": order["id"] if order else None,
        "attempt": order["attempts"] if order else None,
    })
    s["events"] = s["events"][-600:]

def counts(s):
    c = Counter(o["state"] for o in s["orders"])
    return {state: c[state] for state in STATES}

def append_order(s, now, malformed=False):
    if len(s["orders"]) >= MAX_ORDERS:
        raise ValueError("Order limit reached")
    s["sequence"] += 1
    n = s["sequence"]
    rng = random.Random(s["seed"] + n)
    order = {
        "id": f"ORD-{n:04d}", "sequence": n,
        "payload": {
            "category": rng.choice(CATEGORIES),
            "quantity": -1 if malformed else rng.randint(1, 5),
            "unit_price_paise": rng.randint(5000, 200000),
        },
        "state": "queued", "attempts": 0,
        "created_at": now, "ready_at": now,
        "started_at": None, "complete_at": None,
        "finished_at": None, "will_fail": False,
        "reason": None, "total_paise": None,
    }
    s["orders"].append(order)
    emit(s, now, "accepted", "Order entered the queue", order)
    return order

def validation_error(payload):
    if payload.get("category") not in CATEGORIES:
        return "Unknown product category"
    q = payload.get("quantity")
    p = payload.get("unit_price_paise")
    if type(q) is not int or not 1 <= q <= 5:
        return "Quantity must be an integer between 1 and 5"
    if type(p) is not int or not 5000 <= p <= 200000:
        return "Unit price is outside the allowed range"
    return None

def tick(s, now):
    if now >= s["expires_at"]:
        return
    active = next(
        (o for o in s["orders"] if o["state"] == "processing"),
        None,
    )
    if active and active["complete_at"] <= now:
        if active["will_fail"]:
            active["reason"] = "Injected temporary processing error"
            if active["attempts"] >= MAX_ATTEMPTS:
                active["state"] = "dead_letter"
                active["finished_at"] = now
                emit(s, now, "exhausted", "Attempts exhausted", active)
            else:
                active["state"] = "retry_wait"
                delay = 2 ** (active["attempts"] - 1)
                active["ready_at"] = now + delay
                emit(s, now, "retry", f"Retry in {delay}s", active)
        else:
            active["state"] = "succeeded"
            active["finished_at"] = now
            active["reason"] = None
            p = active["payload"]
            active["total_paise"] = (
                p["quantity"] * p["unit_price_paise"]
            )
            emit(s, now, "success", "Order processed", active)

    c = s["controls"]
    if c["generating"]:
        full = len(s["orders"]) >= MAX_ORDERS
        timed_out = now >= s["generation_until"]
        if full or timed_out:
            c["generating"] = False
            emit(s, now, "generation_stopped", "Generation limit reached")
        elif now >= s["next_generation_at"]:
            append_order(s, now)
            s["next_generation_at"] = now + 0.5

    busy = any(o["state"] == "processing" for o in s["orders"])
    if not c["paused"] and not busy:
        eligible = [
            o for o in s["orders"]
            if o["state"] in ("queued", "retry_wait")
            and o["ready_at"] <= now
        ]
        if eligible:
            o = min(eligible, key=lambda x: (x["ready_at"], x["sequence"]))
            error = validation_error(o["payload"])
            if error:
                o["state"] = "rejected"
                o["reason"] = error
                o["finished_at"] = now
                emit(s, now, "rejected", error, o)
            else:
                o["state"] = "processing"
                o["attempts"] += 1
                o["started_at"] = now
                o["complete_at"] = now + 0.25
                o["will_fail"] = bool(
                    c["temporary_errors"]
                    and o["sequence"] % 3 == 0
                    and o["attempts"] < 3
                )
                emit(s, now, "attempt_started", "Processing started", o)

    if now >= s["next_sample_at"]:
        s["samples"].append({"time": now, **counts(s)})
        s["samples"] = s["samples"][-180:]
        s["next_sample_at"] = now + 1

def check_invariants(s):
    c = counts(s)
    assert sum(c.values()) == len(s["orders"])
    assert c["processing"] <= 1
    assert len(s["orders"]) <= MAX_ORDERS
    assert all(0 <= o["attempts"] <= 3 for o in s["orders"])
    assert all(o["state"] in STATES for o in s["orders"])
