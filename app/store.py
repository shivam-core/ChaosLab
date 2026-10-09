import json
import time
import os
import secrets
import hashlib
from redis.exceptions import WatchError
import redis

class MissingLab(Exception):
    pass

class BusyLab(Exception):
    pass

class CapacityError(Exception):
    pass

def get_redis():
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    return redis.Redis.from_url(url, decode_responses=True, socket_timeout=2.0)

def mutate(client, key, apply):
    for attempt in range(8):
        with client.pipeline() as pipe:
            try:
                pipe.watch(key)
                raw = pipe.get(key)
                if raw is None:
                    raise MissingLab()
                state = json.loads(raw)
                if state["expires_at"] <= time.time():
                    raise MissingLab()
                result = apply(state)
                state["revision"] += 1
                encoded = json.dumps(state, separators=(",", ":"))
                pipe.multi()
                pipe.set(key, encoded, keepttl=True)
                pipe.execute()
                return result, state
            except WatchError:
                continue
    raise BusyLab()

def create_lab(client, new_state_func, max_labs):
    now = time.time()
    for attempt in range(8):
        with client.pipeline() as pipe:
            try:
                pipe.watch("chaoslab:active")
                # Clean up expired members
                pipe.zremrangebyscore("chaoslab:active", "-inf", now)
                active_labs = pipe.zcard("chaoslab:active")
                if active_labs >= max_labs:
                    raise CapacityError("Maximum lab capacity reached")
                
                lab_id = secrets.token_urlsafe(12)
                token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                
                state = new_state_func(lab_id, token_hash, now)
                key = f"chaoslab:lab:{lab_id}"
                
                encoded = json.dumps(state, separators=(",", ":"))
                pipe.multi()
                pipe.set(key, encoded, ex=int(state["expires_at"] - now))
                pipe.zadd("chaoslab:active", {lab_id: state["expires_at"]})
                pipe.execute()
                
                return lab_id, token, state["expires_at"]
            except WatchError:
                continue
    raise BusyLab()
