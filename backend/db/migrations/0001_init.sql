-- applications: static facts about something you applied to.
-- Nothing here mutates once created except via a new row elsewhere
-- (status_events) -- this table is not where "state" lives.
CREATE TABLE applications (
    id BIGSERIAL PRIMARY KEY,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    applied_via TEXT,
    job_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- status_events: append-only. A row is never updated or deleted.
-- "Current status" is derived (see application_current_status view),
-- never stored as a column that gets overwritten -- overwriting would
-- destroy the history a timeline view and an audit trail both need.
--
-- application_id is nullable: an email the entity matcher couldn't
-- resolve to an application still gets logged (so nothing is silently
-- dropped), just unlinked, for manual review/linking later.
--
-- status uses a CHECK constraint, not a Postgres ENUM type: enums are
-- awkward to extend later (ADD VALUE has transaction restrictions);
-- a CHECK is a plain ALTER TABLE ... DROP CONSTRAINT / ADD CONSTRAINT,
-- which matters for a schema that's expected to gain statuses in the
-- classifier's early days.
--
-- raw_email_id has a UNIQUE constraint so re-polling the same Gmail
-- thread on the next cron run is a no-op (INSERT ... ON CONFLICT DO
-- NOTHING in the ingestion code). Postgres treats multiple NULLs in a
-- UNIQUE column as distinct, so manual entries (raw_email_id IS NULL)
-- are never blocked by each other.
CREATE TABLE status_events (
    id BIGSERIAL PRIMARY KEY,
    application_id BIGINT REFERENCES applications(id),
    status TEXT NOT NULL CHECK (
        status IN ('applied', 'application_received', 'interview_invite', 'rejected', 'offer')
    ),
    source TEXT NOT NULL CHECK (source IN ('manual', 'gmail')),
    raw_email_id TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_status_events_app_created
    ON status_events (application_id, created_at DESC);

-- Derives "current status" instead of storing it. DISTINCT ON picks
-- the single most recent row per application_id, using the index above.
--
-- Tiebreak on id, not just created_at: Postgres's now() returns the
-- same value for every statement inside one transaction, so two
-- events inserted together (e.g. a batch ingestion run) can share an
-- identical created_at. id (BIGSERIAL) is monotonic and always
-- unique, so it's the only safe total order here -- this was caught
-- by a test inserting multiple events in a single transaction, not
-- spotted by inspection.
CREATE VIEW application_current_status AS
SELECT DISTINCT ON (application_id)
    application_id,
    status,
    source,
    raw_email_id,
    created_at
FROM status_events
WHERE application_id IS NOT NULL
ORDER BY application_id, created_at DESC, id DESC;
