# UI / UX Component System

The current product UI is a server-rendered component system inside
`src/importer_source_readiness/operator_app.py`. It is intentionally local and
offline-safe for private-beta review, but it follows reusable product patterns
instead of static HTML pages.

## Current Components

- app shell with persistent sidebar and mobile topbar
- workflow stepper for start, documents, confirm, report, and review
- status badges for blocked, ready, and warning states
- icon buttons using a local Lucide-style icon subset
- metric cards for packet, evidence, runtime, and source-monitor state
- responsive grids and split panels
- table views for evidence, extracted fields, blockers, source registry, audit,
  and saved packets
- route-level forms for beginner starter, PDF upload, field confirmation, AI
  policy, review findings, and evidence actions

## UX Rules

- First screen is the workflow, not a marketing page.
- Beginner users can start without documents at `/start`.
- Document users upload PDFs at `/trade-check`, then confirm fields at
  `/public/packets/:id/confirm`.
- The result page gives starter checklist, missing evidence, buyer packet,
  broker packet, ChatGPT-safe summary, and delete-files actions.
- The workspace at `/workspace` shows saved packets and next moves.
- UI copy must keep external claims closed.

## Open Source Direction

When the UI is split into a dedicated frontend app, use:

- React or Preact for component composition
- Radix UI primitives for accessible dialogs, tabs, menus, and form controls
- TanStack Query/Table for API state and dense operator tables
- React Hook Form plus Zod for form validation
- Lucide for icons
- Playwright for visual/interaction proof

Until that split, keep the server-rendered components deterministic, testable,
and dependency-light so the local product can run from the Python repo alone.
