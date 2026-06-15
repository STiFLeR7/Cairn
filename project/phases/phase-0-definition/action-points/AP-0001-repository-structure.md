---
id: AP-0001
title: Establish repository structure & skeleton
phase: phase-0-definition
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: []
related_docs: [README.md, docs/README.md]
related_adrs: [ADR-0001]
---

## Objective

Create the repository skeleton that makes the operating model physically real: the knowledge/state
separation (`docs/` vs `project/`), the root-level always-visible trackers, and placeholder homes for
code that arrives in later phases.

## Scope

**In:** directory layout; root `README`; `docs/` and `project/` trees; placeholder `src/`, `tests/`,
`benchmarks/`; `.gitignore`; git init + remote.
**Out:** governance *content* (AP-0002/0003), vision *content* (AP-0004), tracker *content* (AP-0005),
licensing files (AP-0006).

## Deliverables

- `docs/` (governance, vision, concepts, research, design, adr) and `project/` (phases, tracking,
  templates) trees.
- Root `README.md`, `.gitignore`.
- Placeholder READMEs in `src/`, `tests/`, `benchmarks/`, `docs/concepts/`, `docs/research/`, `docs/design/`.
- Git repository initialized with `origin` → `https://github.com/STiFLeR7/Cairn.git`.

## Acceptance Criteria

- [x] `docs/` vs `project/` separation exists and is documented in `docs/README.md`
- [x] Root `README.md` present with positioning and repo map
- [x] Git initialized; `origin` remote set
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- none

## Status / Log

- 2026-06-15 — Proposed → In Progress. Skeleton created; git initialized; remote `origin` added.
- 2026-06-15 — In Review → Done. Reviewed & approved; all acceptance criteria met.
