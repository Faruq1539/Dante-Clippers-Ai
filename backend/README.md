# Dante Clippers AI — Backend

FastAPI backend implementing the architecture in [`../docs/tech-spec.md`](../docs/tech-spec.md).

## Status

Scaffold only — data model, API routes, and job queue wiring are in place;
the AI pipeline stages (transcription, highlight scoring, rendering) are
stubbed with `NotImplementedError` in `app/worker/pipeline.py` and need
real implementations.

## Structure

```
app/
  main.py              FastAPI app + route registration
  config.py            Settings (env vars via pydantic-settings)
  database.py           SQLAlchemy engine/session setup
  models/               SQLAlchemy models (one file per entity)
  schemas/               Pydantic request/response schemas
  api/routes/            FastAPI routers (one file per resource)
  services/
    credit_service.py    Credit accounting — duration-based pricing (see tech-spec §8)
  worker/
    celery_app.py         Celery app config
    tasks.py               Main processing_video task
    pipeline.py             Stubbed AI pipeline stages — fill these in
```

## Running locally

Requires Docker.

```bash
cp .env.example .env    # fill in real secrets/keys as you get them
docker compose up --build
```

This starts:
- `api` — FastAPI app at http://localhost:8000 (interactive docs at `/docs`)
- `worker` — Celery worker that picks up processing jobs
- `db` — Postgres
- `redis` — Celery broker/result backend

## What's NOT done yet

- **Auth** — `app/api/deps.py` has a placeholder that just grabs the first
  user in the DB. Replace with real JWT auth before this touches real users.
- **AI pipeline** — `app/worker/pipeline.py` functions all raise
  `NotImplementedError`. This is the core product differentiator, so it's
  worth prioritizing over OAuth/publishing integrations (see tech-spec §10,
  Phase 1).
- **OAuth flows** — `app/api/routes/connected_accounts.py` has a stub
  `start_oauth` endpoint. Needs real per-platform authorization URLs and
  callback handling for TikTok, Instagram, Twitch (see tech-spec §5 for
  which platforms have official import APIs).
- **Database migrations** — no Alembic setup yet. Run
  `alembic init alembic` and generate an initial migration once the
  models are stable.
- **IAP receipt verification** — `credit_service.grant_purchased_credits`
  must only be called after verifying the purchase server-side with
  Apple/Google, not from a client-reported amount.
