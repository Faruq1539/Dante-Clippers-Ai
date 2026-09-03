import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import users, videos, jobs, clips, credits, connected_accounts
from app.services.storage import LOCAL_STORAGE_DIR

app = FastAPI(
    title="Dante Clippers AI API",
    version="0.1.0",
    description="Backend API for the Dante Clippers AI video clipping app.",
)

# Allow the mobile app (running on a phone, a different origin/device) to
# call this API during local development. Tighten this before shipping.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves locally-stored uploads/clips over HTTP so a phone on the same
# network can actually play them back. Only relevant when running without
# S3 configured -- see docs/tech-spec.md and services/storage.py.
os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=LOCAL_STORAGE_DIR), name="media")

app.include_router(users.router)
app.include_router(videos.router)
app.include_router(jobs.router)
app.include_router(clips.router)
app.include_router(credits.router)
app.include_router(connected_accounts.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
