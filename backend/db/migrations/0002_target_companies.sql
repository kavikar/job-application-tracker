-- A watchlist, not an event log: unlike status_events, this table is
-- plain CRUD (add a target, remove it once you've applied or decided
-- against it). There's no "history of a target" worth preserving --
-- what happened once you actually apply is already captured in
-- applications/status_events, which is why "already applied" below
-- is computed by cross-referencing those tables, not stored here.
CREATE TABLE target_companies (
    id BIGSERIAL PRIMARY KEY,
    company TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('A', 'B', 'C', 'D')),
    -- Preserves the playbook's sub-groupings (e.g. "Testing / DevEx
    -- tools", "Atlanta cluster") within a tier. Nullable: not every
    -- tier has sub-categories.
    category TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_target_companies_tier ON target_companies (tier, id);
