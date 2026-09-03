# Dante Clippers AI — Mobile App

React Native app (via Expo) implementing the mobile side of the architecture in [`../docs/tech-spec.md`](../docs/tech-spec.md).

## Status

Core loop works end-to-end: pick a video → upload → watch it process → view generated clips. Auth, branding/caption editing, and social publishing are not built yet — see "What's NOT done yet" below.

## Why Expo (not bare React Native)

Expo lets you run this app on your actual phone by scanning a QR code — no Android Studio, no Xcode, no native build setup. Given everything involved in getting the backend running locally, this avoids repeating that kind of setup pain on the mobile side.

## Screens

```
src/
  api/
    client.ts       Base fetch wrapper, reads API_BASE_URL from env
    index.ts         Typed functions for each backend endpoint used
  types/index.ts      TypeScript interfaces matching backend schemas
  navigation/
    RootNavigator.tsx  Stack: Home -> Upload -> JobStatus -> Clips
  screens/
    HomeScreen.tsx      Credit balance + entry point
    UploadScreen.tsx     Pick a video, upload it, kick off a job
    JobStatusScreen.tsx   Polls job status every 3s until done/failed
    ClipsScreen.tsx        Shows generated clips with video playback
  components/
    PrimaryButton.tsx
```

## Backend changes this app required

Two things were missing from the backend and had to be added to make this app actually work (already included if you're pulling from the repo):

1. **`POST /videos/upload`** — the backend originally only had a way to *register* a video by an existing storage path/URL, with no way to actually receive a file. Mobile apps need to send the file itself, so this endpoint was added (see `backend/app/api/routes/videos.py`).
2. **`/media` static file serving + `playback_url`** — clips were stored as local Windows file paths (`file://C:\Users\...`), which a phone can't reach at all. The backend now serves `local_storage/` over HTTP and returns a real `playback_url` in the API response (see `backend/app/main.py` and `backend/app/services/storage.py`).

## Running it

### 1. Get your computer's LAN IP

Your phone can't reach `localhost` — that means "this same device" to the phone, not your PC. Find your computer's actual network address:

**Windows:** open a terminal and run `ipconfig`, look for "IPv4 Address" (something like `192.168.1.xxx`).

### 2. Point the backend at that IP

In `backend/.env`, add (or confirm) this line, using your real IP:

```
PUBLIC_BASE_URL=http://192.168.1.xxx:8000
```

Restart uvicorn with `--host 0.0.0.0` instead of the default, so it accepts connections from other devices on your network, not just itself:

```
uvicorn app.main:app --reload --host 0.0.0.0
```

**Windows Firewall** may prompt to allow this the first time — allow it (on Private networks at least). If your phone still can't connect, this firewall prompt is the most likely culprit.

### 3. Configure the mobile app

```
cp .env.example .env
```

Edit `.env` and set `EXPO_PUBLIC_API_BASE_URL` to the same `http://192.168.1.xxx:8000` from step 2.

### 4. Install dependencies and run

```
npm install
npx expo start
```

Install the **Expo Go** app on your phone (App Store / Play Store), make sure your phone is on the **same wifi network** as your computer, and scan the QR code that appears in the terminal.

### 5. Make sure the full backend stack is running

For a real end-to-end test, you need all of these running at once (same as local backend testing):
- PostgreSQL
- Redis
- `uvicorn app.main:app --reload --host 0.0.0.0`
- `celery -A app.worker.celery_app worker --loglevel=info --pool=solo`

## What's NOT done yet

- **Auth** — there's no login screen. The backend's `get_current_user` still just grabs the first user in the database (see backend README). Every screen currently acts as that one test user.
- **No job history list** — `HomeScreen` doesn't show past jobs because there's no `GET /jobs` (list) endpoint on the backend yet, only `GET /jobs/{id}` (single). Worth adding.
- **No caption/brand editing** — clips play back as rendered, but there's no in-app editor for captions, fonts, or colors yet.
- **No social connect/publish** — no TikTok/Instagram/YouTube integration in the app yet (see tech-spec §5 and §10 for the phased plan).
- **No local video trimming preview before upload** — the picker just grabs whatever video length you choose; very long videos will cost more credits and take longer to process (see backend README's cost note).
