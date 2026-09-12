# Job Application Tracker

A single-user tool that tracks job applications by combining manual
entry with automated status detection from Gmail. See
[`DESIGN.md`](./DESIGN.md) for the full design, data flow, and the
tradeoffs behind it.

- [`backend/README.md`](./backend/README.md) — FastAPI + Postgres
  setup, tests, Gmail OAuth, ingestion design notes, the scheduler,
  and auth.
- [`frontend/README.md`](./frontend/README.md) — React + Tailwind
  dashboard setup and tests.

## CI

`.github/workflows/ci.yml` runs on every push and pull request:
backend lint (`ruff`) + tests (`pytest`, against a real Postgres
service container — same principle as local dev, see
`backend/README.md`) and frontend lint (`oxlint`) + tests (`vitest`)
+ build. Nothing merges green without both passing.

`.github/workflows/ingest.yml` is the Phase 5 scheduler, not a CI
gate — see `backend/README.md`'s "Scheduler" section.

## Deploy

One-time setup, in this order (each step needs the previous one's
output):

### 1. Postgres (Supabase or Neon, free tier)

Create a project on either. You need the resulting
`DATABASE_URL` (Supabase: Project Settings → Database → Connection
string, "URI" format, using the `psycopg`-compatible
`postgresql://` scheme — prefix it `postgresql+psycopg://` for this
project's SQLAlchemy driver; Neon gives you a connection string in the
same shape from its dashboard).

Run migrations against it once, from your machine:
```bash
cd backend
DATABASE_URL=<your connection string> .venv/bin/python -m db.migrate
```

### 2. Backend on Render

1. New → Web Service → connect this GitHub repo.
2. **Root Directory:** `backend`
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Environment variables (Render dashboard → Environment):
   - `DATABASE_URL` — from step 1
   - `API_KEY` — a long random string you generate yourself (e.g.
     `openssl rand -hex 32`); this is what both the scheduler and you
     (via the frontend's unlock screen) will authenticate with
   - `CORS_ALLOWED_ORIGINS` — your Vercel URL once you have it from
     step 3 (comma-separated if you need more than one, e.g. a preview
     URL too)
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`
     — from `backend/README.md`'s Gmail OAuth setup walkthrough
6. Deploy. Note the resulting `https://<name>.onrender.com` URL.

### 3. Frontend on Vercel

1. Import this Git repo as a new Vercel project.
2. **Root Directory:** `frontend` (Vercel auto-detects the Vite
   framework preset — no `vercel.json` needed).
3. Environment variable: `VITE_API_BASE_URL` = the Render URL from
   step 2.
4. Deploy. Note the resulting `https://<name>.vercel.app` URL, and go
   back to Render to set `CORS_ALLOWED_ORIGINS` to it if you hadn't
   yet (the backend will reject the frontend's requests via CORS until
   this matches).
5. Open the deployed URL and enter the same `API_KEY` value you set on
   Render into the unlock screen — it's stored only in your browser's
   `localStorage`, never in the deployed build (see
   `frontend/src/auth.ts`).

### 4. Scheduler (GitHub Actions)

Repo → Settings → Secrets and variables → Actions, add:
- `BACKEND_URL` — the Render URL from step 2 (no trailing slash)
- `API_KEY` — the same value set on Render in step 2

`.github/workflows/ingest.yml` will then start firing on its cron
schedule; use its "Run workflow" button (workflow_dispatch) to trigger
one manually and confirm it works before waiting for the schedule.
