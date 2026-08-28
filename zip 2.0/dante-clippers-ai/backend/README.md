# Dante Clippers AI — Backend

FastAPI backend implementing the architecture in [`../docs/tech-spec.md`](../docs/tech-spec.md).

## Status

Data model, API routes, job queue, and the full AI pipeline (transcription,
highlight scoring, rendering) are implemented. Auth and OAuth flows are
still placeholders — see "What's NOT done yet" below.

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
    pipeline.py             Orchestrates the AI pipeline stages below
    transcription.py         faster-whisper transcription
    highlight_scoring.py      Anthropic API-based highlight scoring
    captions.py                Builds .srt caption files per clip
```

## AI Pipeline

1. **Transcribe** (`transcription.py`) — extracts audio via ffmpeg, runs it
   through a self-hosted `faster-whisper` model, returns timestamped segments.
2. **Score highlights** (`highlight_scoring.py`) — chunks the transcript into
   ~5-minute overlapping windows and asks the Anthropic API to identify
   clip-worthy moments in each, using a rubric prompt (emotional peaks,
   punchlines, bold claims, audience reaction). Requires `ANTHROPIC_API_KEY`.
3. **Select segments** (`pipeline.py`) — ranks candidates by score, picks the
   top N non-overlapping ones.
4. **Render** (`pipeline.py::render_clip`) — cuts the segment with ffmpeg,
   center-crops to 9:16, burns in captions styled from the clip's brand
   template, uploads the result.

**Known limitation:** reframing uses a plain center crop. That's fine for
single-speaker talking-head content but not ideal for multi-person or
off-center footage — swapping in active-speaker/face-tracking is a natural
next upgrade once the basic pipeline is validated end-to-end.

**Cost note:** Whisper model size and the Anthropic model used for scoring
(`WHISPER_MODEL_SIZE` / `ANTHROPIC_MODEL` in `.env`) directly drive your
per-minute processing cost — see `docs/tech-spec.md` §8 for how that should
inform your credit pricing.

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
- **Active-speaker reframing** — rendering currently uses a plain center
  crop instead of face/speaker tracking (see "Known limitation" above).
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
