from app.engine import counts

def make_snapshot(state, now, worker_online=True):
    return {
        "schema_version": state["schema_version"],
        "lab_id": state["lab_id"],
        "revision": state["revision"],
        "server_time": now,
        "expires_at": state["expires_at"],
        "controls": state["controls"],
        "counts": counts(state),
        "limits": {
            "max_orders": 300,
            "max_attempts": 3
        },
        "worker_status": "online" if worker_online else "offline",
        "orders": state["orders"],
        "samples": state["samples"],
        "events": state["events"]
    }
