import time
import os
import signal
import sys
import logging
from app.store import get_redis, mutate, MissingLab, BusyLab
from app.engine import tick, check_invariants

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    client = get_redis()
    running = True

    def handler(signum, frame):
        nonlocal running
        running = False
        logger.info("Worker stopping...")
    
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    logger.info("Worker started")
    
    while running:
        try:
            now = time.time()
            client.set("chaoslab:worker_heartbeat", "online", ex=10)
            
            # Get active labs
            active_labs = client.zrangebyscore("chaoslab:active", now, "+inf")
            for lab_id in active_labs:
                key = f"chaoslab:lab:{lab_id}"
                
                def apply_tick(state):
                    tick(state, now)
                    check_invariants(state)
                    return True
                
                try:
                    mutate(client, key, apply_tick)
                except MissingLab:
                    client.zrem("chaoslab:active", lab_id)
                except BusyLab:
                    pass # Retry next loop
            
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Store connection error: {e}")
            for delay in [0.5, 1, 2, 5]:
                if not running:
                    break
                time.sleep(delay)
                try:
                    client.ping()
                    break
                except Exception:
                    pass

if __name__ == "__main__":
    main()
