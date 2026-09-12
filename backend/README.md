# Backend

FastAPI + Postgres. See `/DESIGN.md` at the repo root for the overall
design and tradeoffs.

## Local setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt

# Postgres running locally, with a role/db matching .env.example
cp .env.example .env

# Apply migrations (must run as a module, from the backend/ dir, so
# the app package resolves the same way pytest's pythonpath=. does)
.venv/bin/python -m db.migrate

.venv/bin/uvicorn app.main:app --reload
```

## Tests

```bash
.venv/bin/python -m pytest -v
```

Tests run against a real local Postgres database (`jobtracker_test`),
not a mock — see `tests/conftest.py` and `DESIGN.md` for why. Each
test runs inside a transaction that's rolled back afterward, so the
schema only needs to be migrated once per test session.

## Schema

Numbered plain-SQL files in `db/migrations/`, applied by
`db/migrate.py`, which tracks what's already run in a
`schema_migrations` table. Not Alembic — see the comment at the top of
`db/migrate.py` for why that's the right call at this size.

## Gmail OAuth setup (needed for `/ingest`, not for anything else)

`POST /ingest` needs its own Google Cloud OAuth client — separate from
any Gmail access a chat session might have; the deployed backend runs
unattended on a schedule, so it needs its own long-lived credentials.
One-time setup, done by you in Google Cloud Console:

1. Create a Google Cloud project (or reuse one) at
   console.cloud.google.com.
2. Enable the **Gmail API** for that project (APIs & Services ->
   Enable APIs and Services -> search "Gmail API").
3. Configure the **OAuth consent screen**: External user type, fill in
   the required app fields (name, your email). Add the scope
   `https://www.googleapis.com/auth/gmail.readonly`.
4. **Publish the app to Production** (not "Testing"). This is the
   important part: Testing-mode refresh tokens hard-expire after 7
   days, which would silently break the cron job every week. Staying
   unverified in Production is fine at this scale — see DESIGN.md's
   Gmail ingestion section for why Google allows this under 100 users
   without a verification review.
5. Create an **OAuth client ID** of type **Desktop app** (Credentials
   -> Create Credentials -> OAuth client ID). Note its Client ID and
   Client Secret.
6. Run the one-time authorization script locally (not in CI, not on a
   server — it needs a real browser):
   ```bash
   GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... .venv/bin/python scripts/authorize_gmail.py
   ```
   This opens a browser for you to sign in and consent — you'll see an
   "unverified app" warning; click through it (Advanced -> "Go to
   <app name> (unsafe)"), since you're the app's own developer and
   only user. The script prints a refresh token.
7. Store all three values (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`,
   `GOOGLE_REFRESH_TOKEN`) as secrets: a GitHub Actions secret for the
   cron job (Phase 5) and a Render environment variable for the
   deployed backend (Phase 8). Never commit them — `.env` is
   gitignored for exactly this.

## Ingestion design notes

`POST /ingest` fetches messages from Gmail scoped only by a rolling
time window (`newer_than:2d in:inbox`, see `app/ingestion.py`), not by
a keyword search — `classify()` is what decides whether a message is
job-related at all, so there's no second, separately-maintained
keyword filter at the Gmail-query layer to keep in sync with the
classifier's rules.

`app/gmail_client.py`'s `extract_text()` prefers a message's
`text/plain` MIME part, but falls back to stripping the `text/html`
part when the plain-text part looks too short to be real content.
This isn't defensive programming for its own sake: checking the
classifier against a real inbox during Phase 3 turned up a real
LinkedIn rejection email whose plain-text part decoded to just
unsubscribe-footer boilerplate, while the actual rejection sentence
("Unfortunately, we will not be moving forward...") existed only in
the HTML part. Without the fallback, that email would have silently
gone through as "no status detected" instead of a rejection.

## Scheduler

`.github/workflows/ingest.yml` hits `POST /ingest` on a cron schedule
(every 4 hours) via `workflow_dispatch`-capable GitHub Actions. This
is deliberately not a real production job queue (Celery/SQS/etc.),
and the gaps that leaves are worth naming rather than glossing over:

- **No retry/backoff on failure.** A production queue retries a failed
  job with exponential backoff and a dead-letter queue for jobs that
  keep failing. Here, a failed run just waits for the next scheduled
  fire (at most ~4 hours later) or a manual `workflow_dispatch`. This
  is fine because ingestion is idempotent (`ON CONFLICT (raw_email_id)
  DO NOTHING`) and stateless between runs -- a missed run doesn't lose
  data, Gmail still has the message next time the time window covers
  it.
- **No monitoring/alerting infrastructure.** A production system would
  page someone on repeated failures. Here, GitHub's own default
  behavior -- emailing the repo owner when a scheduled workflow run
  fails -- is the entire alerting story. That's a real, free mechanism
  and it's enough for a single person watching their own job search;
  it would not be enough for anything with an on-call rotation.
- **No timing guarantees.** GitHub Actions documents that scheduled
  workflows can be delayed during periods of high platform load --
  "every 4 hours" can mean "every 4-5 hours" some days. Fine for "did
  I get an email today," not fine if a use case needed precise timing.
- **No concurrency control / worker pool.** There's only ever one
  ingestion run in flight, triggered serially by cron. A real queue
  would need to handle many concurrent workers competing for jobs;
  there's nothing here to compete over.

All of these are acceptable specifically because ingestion is cheap,
infrequent, and idempotent. The moment any of that stops being true
(near-real-time requirements, expensive per-run cost, non-idempotent
side effects), this is the first piece of the design to replace.

## Auth

Every route except `/health` requires `Authorization: Bearer
<API_KEY>` (see `app/auth.py`), checked with a constant-time
comparison against the `API_KEY` setting. **The default
(`dev-only-change-me`) must be overridden via env var in any real
deployment** -- set `API_KEY` in Render's environment and as a GitHub
Actions secret (the same value the `ingest.yml` workflow and the
frontend's manually-entered key both need to match).

The frontend does **not** get this key baked into its build -- see
`frontend/src/auth.ts` for why that would leak it to anyone visiting
the deployed site. It's entered once by hand into the app's unlock
screen and kept only in the browser's own `localStorage`.
