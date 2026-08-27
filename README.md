# Dante Clippers AI

AI-powered video clipping app — turns long-form video into short, captioned, branded clips ready for TikTok, Reels, and Shorts.

## Status
Backend scaffold in progress. Mobile app not started yet. See `/docs` for product and technical planning documents.

## Docs
- [`docs/tech-spec.md`](docs/tech-spec.md) — architecture, AI pipeline, platform integration matrix, MVP phasing

## Backend
- [`backend/`](backend/) — FastAPI backend scaffold (data model, API routes, Celery job queue). See [`backend/README.md`](backend/README.md) for what's implemented vs. still stubbed, and how to run it locally.

## Stack
See tech spec for full details — mobile app (React Native/Flutter or native, not started), FastAPI backend, async video processing workers via Celery/Redis, Postgres, object storage, LLM-based highlight detection.

## License
TBD
