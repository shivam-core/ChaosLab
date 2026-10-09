# Render Deployment Configuration

This project can be deployed to Render using a Web Service, a Background Worker, and a Key Value service.

## Prerequisites
- A GitHub account with this repository pushed.
- A Render account.

## Steps

1. **Database:**
   Create a "Key Value" service in your desired region. Note the *Internal Connection URL* starting with `rediss://` or `redis://`.

2. **Web Service:**
   - Connect your GitHub repository.
   - Type: Web Service
   - Environment: Python 3
   - Build Command: `pip install -r requirements.lock`
   - Start Command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Health Check Path: `/health/ready`
   - Environment Variables:
     - `REDIS_URL` = (Your Internal Connection URL)
     - `APP_ENV` = production
     - `MAX_LABS` = 20

3. **Background Worker:**
   - Connect the same GitHub repository.
   - Type: Background Worker
   - Environment: Python 3
   - Build Command: `pip install -r requirements.lock`
   - Start Command: `python -m app.worker`
   - Environment Variables:
     - `REDIS_URL` = (Your Internal Connection URL)
     - `APP_ENV` = production

## Limitations
Render's free tier spins down inactive web services and background workers, which will halt pipeline execution. A paid worker/web instance and paid Key Value persistence plan are required for durable processing.
