# ChaosLab

ChaosLab is an interactive open-source lab for understanding failures and resilience in data pipelines. It generates synthetic shopping orders, processes them through an independent worker, and lets you deliberately introduce problems to observe queueing and recovery in real-time.

## Overview
This application uses three main components:
- **Web Service:** A FastAPI backend and modern JavaScript frontend serving the dashboard.
- **Worker Service:** A separate Python process handling validation, processing, retries, and metrics generation.
- **Store:** A Valkey datastore serving as a shared persistence layer to keep state synchronized between the web and worker processes.

## Setup and Usage

**Prerequisites:**
- Git
- Docker and Docker Compose

**Running locally:**
```bash
git clone https://github.com/shivamkore/chaoslab.git
cd chaoslab
docker compose config
docker compose up --build
```

**Verifying operation:**
1. Open `http://localhost:8000`.
2. Click **Create lab**.
3. Confirm the worker is "Live".
4. Click **Start generating** and watch orders enter the queue and succeed.
5. Click **Pause worker** to see orders queue up, then **Restore normal operation** to watch the backlog clear.
6. Try injecting malformed orders or enabling temporary errors to see rejection and retry behavior.

## Architecture
- **Browser:** Renders dashboard via HTML/JS using short-polling for real-time updates.
- **Web container:** FastAPI app. Read/Write to store with optimistic concurrency control (WATCH).
- **Worker container:** A tick-based state machine evaluating processing steps, enforcing limits, and updating the datastore transactionally.
- **Store container:** Valkey with AOF enabled for persistence.

## Configuration
All services are configured using environment variables, mostly handled by Docker Compose.
- `REDIS_URL`: URL to the Valkey/Redis instance.
- `MAX_LABS`: Maximum concurrent active labs (default: 20).

## Tests
To run the core engine tests without Docker:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.lock
pytest tests/
```

## Limitations
- State is bounded: maximum of 300 orders and an expiration of 2 hours per lab.
- No public rate limiting or accounts out-of-the-box.
- Storage uses AOF everysec; highly concurrent edge cases during hardware failures might lose recent ticks.

## License
MIT License. See `LICENSE` and `THIRD_PARTY_NOTICES.md`.
