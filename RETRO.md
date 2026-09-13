# Retro

Prep material for talking about this project, not a project status
report. Written after all 9 phases (design doc through CI+deploy docs).

## What broke (and how it was caught)

**1. `now()` returns the same value for every statement in one
transaction (Phase 1).** The `application_current_status` view used
`DISTINCT ON (application_id) ORDER BY created_at DESC` to derive
current status. A test that inserted three events for one application
in a single transaction failed: all three got an identical
`created_at`, so the tiebreak was arbitrary and picked the wrong
"latest" status. Fix was adding `id` (monotonic, always unique) as a
second sort key. This shipped correct because the test wrote a
multi-event scenario before trusting the query, not because anyone
spotted the Postgres behavior by inspection.

**2. The test isolation strategy broke the moment real code called
`commit()` (Phase 2).** Phase 1's test fixture wrapped each test in a
plain transaction and rolled it back after. That's correct only if
application code never calls `session.commit()` — but a real
`POST /applications` handler legitimately needs to commit its work.
Fixed with SQLAlchemy's `join_transaction_mode="create_savepoint"`, so
app-level commits release a savepoint instead of the outer test
transaction. Caught by explicitly checking row counts in the shared
test database after a run that exercised `commit()` — not by a test
failing, since the leak wouldn't have failed *that* test, only
poisoned later ones.

**3. A real Gmail rejection email's plaintext body was empty (Phase
3→4).** Checking the classifier against a real inbox (with
permission) turned up a LinkedIn rejection notification whose subject
line and plaintext MIME part gave zero indication it was a rejection
— the actual "unfortunately, we will not be moving forward" sentence
only existed in the HTML part. Gmail's own plaintext conversion isn't
reliable enough to trust blindly. Fixed by extracting text ourselves
from the raw MIME message, preferring `text/plain` but falling back to
stripping `text/html` when the plain part looks too short to be real
content. This bug is invisible to any test built from synthetic
examples — it only shows up against real data.

**4. No CORS middleware (Phase 6).** Every unit and component test
passed. The frontend still couldn't talk to the backend at all: with
no `CORSMiddleware` configured, the browser's preflight request got a
bare 405 and silently blocked every `fetch`. Caught only by actually
running both servers and driving the app in a real browser
(Playwright) — no mocked-fetch component test or backend integration
test could have caught this, because the bug lives exactly at the
boundary neither side's tests cross.

**5. Almost shipped a real vulnerability (Phase 6→7).** The first
draft of the frontend API client read the API key from
`import.meta.env.VITE_API_KEY`. Vite inlines `VITE_`-prefixed env vars
into the shipped JS bundle at build time — so that "secret" would have
been readable by anyone visiting the deployed site, straight out of
devtools. Caught during Phase 7's design pass, before it was ever
wired to a real backend gate, by asking "who can actually read this
value once it's deployed." Fixed by moving the key to a
runtime-entered, localStorage-only value that never touches the
build.

## What I'd design differently now

- **The append-only schema has exactly one deliberate exception, and
  it's worth flagging every time this project comes up:**
  `PATCH /events/{id}/link` updates `application_id` on an existing
  `status_events` row. It's scoped tightly (only rows where
  `application_id IS NULL`) and justified (correcting the entity
  matcher's guess, not rewriting what happened), but it's the one
  place the "never mutate a row" story has an asterisk. A stricter
  version of this design would model the correction as its own event
  type instead of an UPDATE — that's more architecturally pure and
  measurably more complex for a single-user tool, which is why I
  didn't do it, but it's the honest tradeoff, not an oversight.
- **Component tests gave false confidence about integration.** All 22
  frontend tests passed while the app was completely non-functional
  (the CORS bug). Mocking `fetch` in every component test means
  nothing in the suite ever proves the two halves of the app can
  actually talk to each other. If this project grows, the next testing
  investment isn't more component tests — it's one thin smoke-level
  end-to-end check (even a single Playwright script hitting the real
  built frontend against the real backend) wired into CI, specifically
  because that's the class of bug component tests structurally cannot
  see.
- **The classifier's real-world validation was thin by necessity.**
  Only `application_received` and `rejected` got checked against real
  emails — there simply weren't any real `interview_invite` or `offer`
  examples in the checked window. The rules for those two categories
  are still purely synthetic. Worth another validation pass once more
  inbox data exists, rather than assuming they're as solid as the
  other two.
- **I'd reach for a Gmail `historyId`-based incremental fetch sooner.**
  The current design scopes ingestion by a rolling time window
  (`newer_than:2d`), which is simple and correct but re-fetches
  messages the run before already saw (harmless, since the DB
  dedupes, but wasteful). `historyId` is the more correct primitive
  and I skipped it for v1 simplicity — a reasonable call, but the
  first thing to revisit if Gmail API quota ever became a concern.

## What this demonstrates (resume / interview material)

- **Schema design with a real, nameable failure mode.** Not just
  "I used an append-only events table" but "here's the exact query bug
  a mutable status column would have hidden, and here's the Postgres
  behavior (`now()` per-transaction) that even the append-only version
  had to account for."
- **Dependency injection as a testability tool, used twice, on
  purpose.** `get_db` and `get_gmail_client` are the same pattern
  applied to two different I/O boundaries (database, third-party API),
  each swapped for a test double without touching the route code. This
  is directly the "swap real infra for a test double without the
  system knowing" problem that shows up constantly in platform/test
  infra work.
- **Judgment about which layer to mock, and why.** The DB is real in
  every backend test (because Postgres-specific behavior — `UNIQUE`
  with NULLs, `DISTINCT ON`, `CHECK` constraints — is what's actually
  under test). Gmail and `fetch` are faked (because they're pure I/O
  with no interesting logic of their own to verify). Knowing which is
  which, and being able to justify it, is the actual skill "mock
  everything" or "mock nothing" both miss.
- **A concrete example of validating against real data, not just
  synthetic test cases** — and a bug (the LinkedIn plaintext-body gap)
  that only exists in that gap between the two.
- **A concrete example of catching a real security issue via threat
  modeling** ("who can read this value once it's deployed") before it
  ever reached a live system, not after an incident.
- **Explicit, written tradeoff reasoning throughout** (polling vs.
  push, a CRON job vs. a real job queue, rules-based vs. ML
  classification, `CHECK` vs. `ENUM`) — the interview answer isn't "I
  built X," it's "I chose X over Y because Z, and here's what I gave up
  by not building Y."
