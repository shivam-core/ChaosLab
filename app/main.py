from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import workspaces, uploads, datasets, scenarios, runs

app = FastAPI(title="ChaosLab API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workspaces.router, prefix="/api/workspaces", tags=["workspaces"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["scenarios"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])

import os
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
