# Job Application Tracker — Design Doc (Phase 0)

## What this is

A single-user tool that tracks job applications by combining manual entry
with automated status detection from Gmail. It's also a learning vehicle:
each phase is picked to teach a specific engineering skill relevant to
Platform/SDE-in-Test work (schema design, contract testing, dependency
injection for testability, mocked-vs-live test boundaries, CI/CD gates).

## Components

1. **Postgres (Supabase or Neon free tier)** — single source of truth.
   Two tables: `applications` (static facts: company, role, applied-via,
   job posting URL) and `status_events` (append-only log of status
   changes, `application_id` **nullable** — see "unmatched events"
   below). No ORM-managed "current status" column — see tradeoff #1. A
   view, `application_current_status`, derives the current status via
   `DISTINCT ON (application_id) ... ORDER BY application_id,
   created_at DESC`, so reads stay a plain `SELECT` instead of a
   hand-rolled subquery in every route.

2. **Backend API (FastAPI, Python)** — owns all writes to Postgres.
   Exposes:
   - `GET /health` — liveness check
   - `POST /applications`, `GET /applications` — manual CRUD (Phase 2)
   - `POST /ingest` — pulls new Gmail threads, runs them through the
     entity matcher and classifier, writes `status_events` (Phase 4)
   - Everything sits behind a pre-shared API key
     (`Authorization: Bearer <secret>`, via FastAPI's `APIKeyHeader`)
     instead of HTTP Basic Auth — see "Auth mechanism" below (Phase 7)

3. **Ingestion pipeline module** — two pure functions, no I/O, tested
   independently:
   - `match_application(subject, sender, body, applications) ->
     Application | None` — resolves *which* application an email
     belongs to (company name / domain / a tracking token you control
     in outbound applications).
   - `classify(subject, body, sender) -> Status | None` — resolves
     *what happened* (rules-based keyword/sender matching).

   Splitting these was a gap in the first draft: `classify()` alone
   had no way to produce the `application_id` that `status_events`
   requires. Keeping them separate also gives two distinct,
   independently-testable units instead of one function doing fuzzy
   matching and semantic classification at once — entity resolution
   and status classification fail in different ways and deserve
   separate test tables (Phase 3).

4. **Gmail ingestion** — OAuth read-only, single Google account. The
   OAuth consent screen is set to **Production, unverified** (not
   "Testing") — Testing-mode refresh tokens hard-expire after 7 days,
   which would silently kill the cron job every week. Production mode
   without completing Google's verification review is fine here: it's
   allowed for apps under 100 users requesting non-restricted sensitive
   scopes, which `gmail.readonly` is. The only visible cost is clicking
   through Google's "unverified app" warning once, as the sole user,
   during the initial OAuth grant.

   Ingestion is idempotent and incremental: `status_events` has a
   unique constraint on `raw_email_id`, and writes use
   `INSERT ... ON CONFLICT (raw_email_id) DO NOTHING`, so re-polling
   the same thread on the next cron run is a no-op. The Gmail query
   itself is scoped by a rolling time window (or Gmail's `historyId`,
   whichever proves simpler in Phase 4) instead of re-scanning the
   whole inbox on every run. Called by `POST /ingest`, not by Gmail
   pushing to us.

5. **Scheduler (GitHub Actions cron)** — hits `POST /ingest` every few
   hours. No queue, no retries-with-backoff infra, no separate worker
   process (Phase 5).

6. **Frontend (React + Tailwind, on Vercel)** — funnel view, per-company
   table, timeline view (this is why append-only events matter — you get
   a timeline for free), manual-entry form, plus an "unmatched emails"
   badge/list surfacing any `status_events` row where the entity matcher
   came back empty, so you can link it to an application by hand. Talks
   to the backend API using the API key (Phase 6).

## Data flow

```
                     cron, every N hours
 ┌────────────────┐  (HTTP POST, API key)      ┌─────────────────────────┐
 │ GitHub Actions   │ ─────────────────────────▶│  POST /ingest            │
 │ (scheduler)      │                            │  FastAPI backend         │
 └────────────────┘                            └────────────┬─────────────┘
                                                              │
                                        Gmail API              │ match_application()
                                        (OAuth, read-only,     │ + classify()
                                         incremental window/    │ pure fns,
                                         historyId)             │ no I/O
                                                                 ▼
                                                  ┌───────────────────────────┐
                                                  │ status_events              │
 ┌────────────────┐  GET/POST /applications      │ (append-only, unique on   │
 │ React frontend   │◀───────────────────────────│  raw_email_id, nullable   │
 │ (Vercel)         │   API key                    │  application_id)          │
 └────────┬────────┘                            │ applications              │
          │                                       │ (static facts)            │
          ▼                                       │ Postgres: Supabase/Neon  │
      you, browser                                └───────────────────────────┘
      (funnel / table / timeline / manual entry /
       unmatched-events review)
```

Two independent write paths into `status_events` — manual entry (you,
via the form) and ingestion (Gmail, via the matcher+classifier pair) —
both just append rows. Nothing downstream needs to know which path a
row came from except the `source` column, which is there for exactly
that: to let you audit "did this get set by me or by the classifier."

## Stack choice: FastAPI over Express

Going with **FastAPI (Python)**, not Express. Reasoning, not just
preference:

- **Pydantic models double as the API contract.** Every request/response
  is a typed schema, validated automatically. That schema *is* something
  you can test against directly (schema conformance tests, and later,
  tools like Schemathesis that generate tests from the OpenAPI spec FastAPI
  produces for free). This is a real contract-testing pattern, not
  incidental — worth having on your resume story.
- **Dependency injection for testability.** FastAPI's `Depends()` system
  lets you override the DB session with a test database (or a fake) at
  the route level, cleanly, without monkeypatching. This is the same
  shape of problem you'll hit in Platform/SDE-in-Test work: how do you
  swap real infra for test doubles without the app code knowing? Worth
  learning this pattern here, on a small app, before you meet it at
  scale.
- **pytest is your existing home turf.** You already think in pytest
  fixtures from SDET work; that transfers directly to backend test code
  instead of being a second thing to learn.
- Express would need TypeScript bolted on to get comparable type safety,
  and Jest+Supertest is a fine equivalent testing story, but it doesn't
  hand you the contract-testing and DI patterns for free the way FastAPI
  does. For a project whose explicit goal is teaching system design and
  testing strategy, FastAPI's opinions do more of that work for you.

## Top tradeoffs

**1. Append-only `status_events` vs. a mutable `status` column on
`applications`.**
Append-only means "current status" is *derived* — `latest status_event
per application_id`, not stored — which costs a slightly more involved
query (window function or `DISTINCT ON`/`MAX(timestamp)` grouped by
`application_id`) on every read. What you get for that cost: full
history for free (the timeline view is just `SELECT * WHERE
application_id = ? ORDER BY timestamp`), no update anomalies, and an
audit trail of *why* a status changed (`source` + `raw_email_id`) that a
mutable column would silently destroy on every overwrite. For a tracker
whose whole value proposition includes "show me the timeline," a
column you keep clobbering is the wrong data model even before you
factor in the classifier occasionally being wrong and needing a
correction trail.

**2. Polling (GitHub Actions cron) vs. push (Gmail Pub/Sub webhooks).**
Already locked, but worth stating why it's not overengineering to skip
push: Pub/Sub webhooks need a publicly reachable HTTPS endpoint, a Google
Cloud Pub/Sub topic/subscription, watch renewal (Gmail watches expire
every 7 days and must be re-armed), and signature verification on
incoming pushes. That's real infrastructure for a workflow where "I
found out about my interview invite 2 hours late instead of instantly"
has zero cost. Polling every few hours is the honest match for the
actual latency requirement.

**3. Rules-based classifier vs. ML/LLM classifier.**
Rules-based is deterministic — same input always produces the same
output — which is what makes it a pure, independently unit-testable
function with a fixed table of input→expected-output cases and no
flakiness. An LLM classifier would need either live API calls in tests
(slow, costs money, non-deterministic — the same failure mode you fight
against in flaky E2E suites at work) or a mocking layer that mostly
tests the mock. Rules-based also fails in a legible way: when it
misclassifies something, you can see *which keyword rule* fired or
didn't, and fix that rule — an LLM's misclassification doesn't give you
that kind of actionable diff. The real cost is maintenance: rules will
need tuning against your actual inbox (that's explicitly Phase 3's plan
— you correct the starter rules against real patterns).

## Auth mechanism: API key, not HTTP Basic Auth (revised from Phase 0 draft)

The original locked decision said HTTP Basic Auth for v1. On review,
switching to a single pre-shared API key
(`Authorization: Bearer <secret>`, checked via FastAPI's
`Security(APIKeyHeader(...))`) instead — you confirmed this override.
Reasoning: Basic Auth means a browser-native credential popup in the
React frontend (ugly, and credentials end up needing to live in
`localStorage` or be re-typed) and means the GitHub Actions cron job
has to construct a base64 `user:pass` header. An API key is the same
complexity — one secret, no sessions, no JWT signing, no login UI — but
is the idiomatic shape for how a cron worker and a frontend actually
talk to an API. Everything else about the tradeoff stands: no password
reset flow, no token refresh logic, revisit only if this needs to look
polished for other viewers.

## What I'm flagging as possibly overengineered — reviewed, kept minimal

Called out here rather than building first and flagging after:
- No message queue for ingestion — a straight synchronous `POST
  /ingest` call is fine for polling a handful of emails every few hours.
- No multi-tenancy anywhere in the schema (no `user_id` columns) — would
  be pure unused columns for a single-user app.
- No refresh-token rotation UI, no admin panel for OAuth — the OAuth app
  is unverified in Google's console either way; only the publishing
  status (Testing vs. Production) changes, which is a console toggle,
  not new code.
- API key instead of session/JWT auth — no login UI, no password reset
  flow, no token refresh logic. Revisit only if this needs to look
  polished for other viewers.
- No Schemathesis/property-based contract testing wired into CI for v1
  — FastAPI gives you `openapi.json` for free either way, so adding
  generated contract tests later is additive, not a rework. Worth
  doing once the API shape stabilizes past Phase 2, not before.

## Revision log

- **v1 (initial):** Testing-mode OAuth, single `classify()` function,
  no dedup/idempotency story, HTTP Basic Auth.
- **v2 (this version):** Production-mode-unverified OAuth (fixes the
  7-day token expiry), split `match_application()` / `classify()`
  pipeline (fixes the missing `application_id` link), unique constraint
  on `raw_email_id` + incremental fetch (fixes duplicate events on
  re-poll), `application_current_status` view, nullable
  `application_id` + unmatched-events UI, API key auth in place of
  Basic Auth.

## Sign-off

This is Phase 0. Next step on a "go" is Phase 1: Postgres schema +
backend skeleton, with the test strategy for that layer written before
the tests, and the tests written before we move on.
