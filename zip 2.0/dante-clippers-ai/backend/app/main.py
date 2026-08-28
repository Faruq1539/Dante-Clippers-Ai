from fastapi import FastAPI

from app.api.routes import users, videos, jobs, clips, credits, connected_accounts

app = FastAPI(
    title="Dante Clippers AI API",
    version="0.1.0",
    description="Backend API for the Dante Clippers AI video clipping app.",
)

app.include_router(users.router)
app.include_router(videos.router)
app.include_router(jobs.router)
app.include_router(clips.router)
app.include_router(credits.router)
app.include_router(connected_accounts.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
