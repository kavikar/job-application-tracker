# Frontend

React + TypeScript + Tailwind (v4), built with Vite. See `/DESIGN.md`
at the repo root for the overall design.

## Local setup

```bash
npm install
cp .env.example .env   # points at the local backend by default
npm run dev
```

Needs the backend running (see `../backend/README.md`) -- the backend
must have CORS configured to allow this dev server's origin
(`http://localhost:5173` by default; see `CORS_ALLOWED_ORIGINS` in the
backend's `.env`).

## Tests

```bash
npm run test
```

Component tests (Vitest + React Testing Library) mock `fetch` rather
than hitting a real backend -- the same "mock the I/O boundary, not
the logic" principle as the backend's Gmail-client mocking in Phase 4,
mirrored here. They check what each component does with given data
(funnel math, table rows, form submission payloads), not pixel-level
styling.

**Known gap:** there's no browser-driven end-to-end suite (Playwright,
Cypress) here. The full flow (funnel -> table -> timeline ->
unmatched-linking -> manual entry) was checked manually against the
real running backend before this phase was called done -- that's how
a real CORS misconfiguration was caught, which no component test
would have surfaced since component tests never make a real network
call. Standing up a permanent e2e suite is more infrastructure than a
single-user app needs right now, but it's the natural next addition
if this project ever needs automated regression coverage beyond
components.

## Structure

- `src/api.ts` -- the only place that calls `fetch`. Everything else
  takes data as props/state, which is what makes the components
  testable without a real backend.
- `src/components/` -- one component per dashboard section (funnel,
  company table, timeline, manual-entry form, unmatched-events
  review).
- `src/App.tsx` -- fetches data, wires components together, owns the
  "which application is selected" state that drives the timeline view.
