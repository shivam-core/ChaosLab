from app.engine import new_state, append_order, tick, check_invariants

def test_temporary_errors_retry_then_succeed():
    s = new_state("test", "hash", 1000)
    for _ in range(3):
        append_order(s, 1000)
    s["controls"]["temporary_errors"] = True
    for step in range(200):
        tick(s, 1000 + step * 0.1)
        check_invariants(s)
    third = s["orders"][2]
    assert third["state"] == "succeeded"
    assert third["attempts"] == 3
    assert all(o["state"] == "succeeded" for o in s["orders"])
