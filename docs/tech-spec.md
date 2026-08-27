# Dante Clippers AI — Technical & Product Spec

**Version:** 0.1 (Draft for build planning)
**Owner:** [you]
**Last updated:** 2026-08-27

---

## 1. Product Summary

Dante Clippers AI turns long-form video into short, captioned, branded clips ready for TikTok, Reels, and Shorts — using AI to find highlight moments, auto-generate captions, and publish directly to connected social accounts.

**Platforms:** iOS + Android (native or cross-platform — see §7)
**Languages at launch:** English, French, German, Italian, Spanish, Dutch, Polish, Portuguese
**Monetization:** Freemium — monthly renewing credits, in-app purchase for extra credits / advanced features

---

## 2. Core User Flow

1. **Input** — User uploads a video file, or connects a social account and selects one of their own videos (see §5 for which platforms support this).
2. **Processing** — Video is uploaded to backend storage, queued for AI processing.
3. **AI Highlight Detection** — Model scores the transcript/audio/video for "highlight-worthy" segments.
4. **Clip Generation** — Top N segments are cut, reframed to 9:16, and captioned.
5. **Styling** — User applies brand template (fonts, colors, caption style) via built-in editor; can hand-edit caption text/timing.
6. **Review** — User previews all generated clips, picks favorites, makes final edits.
7. **Export/Publish** — User saves to camera roll, or publishes directly (or schedules) to connected accounts with custom title/caption per platform.

---

## 3. System Architecture (high level)

```
┌─────────────┐      ┌──────────────────┐      ┌───────────────────┐
│  Mobile App │─────▶│   API Gateway /   │─────▶│  Job Queue         │
│ (iOS/Android)│◀────│   Backend (REST)  │◀─────│ (SQS/Cloud Tasks)  │
└─────────────┘      └──────────────────┘      └────────┬───────────┘
       │                       │                          │
       │                       ▼                          ▼
       │              ┌────────────────┐         ┌──────────────────┐
       │              │  Postgres DB   │         │  Video Processing │
       │              │ (users, jobs,  │         │  Workers (GPU)    │
       │              │  credits, etc) │         │  - transcription  │
       │              └────────────────┘         │  - highlight ML   │
       │                       │                  │  - clip render    │
       │                       ▼                  └────────┬─────────┘
       │              ┌────────────────┐                   │
       └─────────────▶│  Object Storage │◀──────────────────┘
                       │  (S3/GCS)       │
                       └────────────────┘
                               │
                               ▼
                     ┌───────────────────┐
                     │ Social Platform    │
                     │ APIs (publish)     │
                     │ TikTok/IG/YouTube  │
                     └───────────────────┘
```

**Key design principle:** video processing is asynchronous and queue-based — never block the mobile app on a long-running render job. The app polls or receives a push notification when clips are ready.

---

## 4. AI Pipeline

| Stage | What it does | Suggested approach |
|---|---|---|
| **Transcription** | Convert audio to timestamped text | Whisper (self-hosted or API) or a managed ASR service |
| **Highlight scoring** | Score transcript segments for "clippability" (emotional peaks, punchlines, strong claims, laughter, audience reaction) | LLM-based scoring pass over transcript chunks (e.g., Claude/GPT with a scoring rubric prompt), optionally combined with audio-energy/laughter detection signals |
| **Segment selection** | Pick top N non-overlapping segments, each 15–90s | Rule-based ranking + de-dup, informed by highlight scores |
| **Reframe to vertical** | Convert 16:9 or other source to 9:16 | Active-speaker detection / face-tracking crop (e.g., via a face-detection model) or center-crop fallback |
| **Caption generation** | Word-level timed captions | Derived directly from transcription timestamps |
| **Caption styling render** | Burn in captions with chosen font/color/animation | FFmpeg-based render pipeline, or a caption-overlay renderer (e.g., Remotion for programmatic video) |

**Cost note:** transcription + LLM highlight scoring + rendering is the main variable cost per video. Credit pricing should be modeled against actual compute cost per minute of source video, not per clip, since a 2-hour podcast costs much more to process than a 5-minute video regardless of how many clips come out.

---

## 5. Platform Integration Matrix

This determines what "connect your account" can and can't do — see prior conversation for full rationale.

| Platform | Import (pull user's own video in) | Publish (post out) | Notes |
|---|---|---|---|
| YouTube | ❌ No official download path | ✅ YouTube Data API (upload) | Import = manual upload only |
| TikTok | ✅ Login Kit `video.list` | ✅ Content Posting API | Full official support |
| Instagram | ✅ Graph API (Business/Creator accounts) | ✅ Graph API publishing | Requires IG Business/Creator account |
| Twitch | ✅ Get Videos/Clips (own channel) | ❌ No publish API (Twitch isn't a "post a clip" platform) | Import-only, for VOD/clip repurposing |
| X/Twitter | ✅ API v2 (own tweets, paid tier) | ✅ API v2 (paid tier) | Budget for API costs |
| Kick | ❌ No reliable official path | ❌ N/A | Not supported at launch |

**Auth pattern:** each platform integration is a standard OAuth 2.0 flow, tokens stored encrypted server-side, refreshed automatically, with a visible "connected accounts" screen where users can disconnect/revoke at any time (required by both app stores).

---

## 6. Data Model (core entities)

- **User** — id, email, locale, plan tier, credit balance, credit renewal date
- **ConnectedAccount** — user_id, platform, oauth tokens (encrypted), platform_user_id, scopes
- **SourceVideo** — user_id, origin (upload/tiktok/instagram/twitch/x), storage_url, duration, status
- **ProcessingJob** — source_video_id, status (queued/transcribing/scoring/rendering/done/failed), created_at
- **Clip** — job_id, start_ts, end_ts, storage_url, caption_style_id, highlight_score, status
- **BrandTemplate** — user_id, fonts, colors, logo_url, caption_style_config
- **PublishJob** — clip_id, platform, scheduled_at, status, platform_post_id
- **CreditTransaction** — user_id, amount, reason (monthly_grant/purchase/spend), created_at

---

## 7. Tech Stack Recommendation

| Layer | Options | Notes |
|---|---|---|
| Mobile app | React Native / Flutter (cross-platform) or native Swift + Kotlin | Cross-platform is faster to ship 8-language support and one codebase; native gives smoother video editing UI — depends on your team's skills and how much you want camera-roll-level editing performance |
| Backend API | Node.js (NestJS/Express) or Python (FastAPI) | Python is a natural fit if your ML pipeline is Python-native |
| Job queue | AWS SQS / Google Cloud Tasks / Redis + BullMQ | Any managed queue works; avoid rolling your own |
| Video processing workers | GPU-backed containers (AWS/GCP), FFmpeg + your ML pipeline | Autoscale workers based on queue depth |
| Database | PostgreSQL | Solid default for relational data + transactions (credits) |
| Storage | S3 / GCS | Store raw uploads, transcripts, rendered clips |
| Transcription | Whisper (self-hosted) or managed ASR API | Self-hosting saves cost at scale but adds ops burden |
| Highlight scoring | LLM API call (Claude, etc.) per transcript chunk | Keep prompts versioned — this is your core IP |
| Payments/IAP | Apple StoreKit + Google Play Billing (required — see prior compliance notes) | Third-party payment processors are not allowed for digital goods on iOS/Android |
| Push notifications | Firebase Cloud Messaging (cross-platform) | For "your clips are ready" alerts |
| Localization | i18n framework (e.g., react-i18next / Flutter intl) + professional translation pass | Don't machine-translate UI strings only — get native review, especially for CTAs |

---

## 8. Credit System Logic

- Each user gets **N credits/month**, resetting on a fixed monthly date (not rolling 30-day, to keep billing simple and honest).
- Credits are consumed based on **source video duration processed**, not number of clips generated (since that's your real cost driver).
- Unused credits: decide up front whether they roll over or expire — expiring credits are simpler and industry-standard for freemium apps, but must be disclosed clearly at purchase (App Store requirement).
- In-app purchase unlocks: additional credit packs, higher resolution export, more brand template slots, removal of a watermark (if you plan to add one to free-tier clips).

---

## 9. Compliance Checklist (carried over, for the dev team)

- [ ] All video import flows use official platform APIs only — no scraping
- [ ] Rights-confirmation checkbox at upload
- [ ] In-app account disconnect + data deletion flow
- [ ] All purchases go through Apple/Google IAP
- [ ] AI-generated content disclosure in UI
- [ ] No unverifiable superlative claims in-app or in store listing
- [ ] Trademark clearance on final app name before submission

---

## 10. Suggested MVP Phasing

**Phase 1 — Core loop (upload-only)**
Upload video → transcribe → AI highlight → auto-clip + caption → basic styling → save to camera roll.
No social integrations yet. Prove the AI pipeline works and clips are genuinely good before adding OAuth complexity.

**Phase 2 — Branding + editor**
Caption editor, brand templates (fonts/colors/logo), multiple export formats.

**Phase 3 — Social connect (import)**
TikTok, Instagram, Twitch import via official APIs.

**Phase 4 — Social publish**
One-tap publish + scheduling to TikTok, Instagram, YouTube.

**Phase 5 — Localization rollout**
Expand from English to the other 7 languages, with native-speaker QA per market.

**Phase 6 — X integration, credit system tuning, scale**
Add X import/publish (paid API tier budgeted), refine credit economics based on real usage data.

---

## 11. Open Questions to Resolve Before Build

- Cross-platform (React Native/Flutter) vs. native — depends on team and how central video-editing UX quality is to your differentiation.
- Self-hosted Whisper vs. managed ASR — cost vs. ops tradeoff at your expected volume.
- Watermark on free-tier clips? (Common lever for upgrade conversion.)
- Do you want real-time processing status in-app (websocket/polling) or just a push notification when done?
- Data retention policy — how long do you keep source videos/clips after processing, and is that disclosed in your privacy policy?
