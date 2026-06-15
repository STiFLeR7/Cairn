---
id: AP-0005
title: Stand up master trackers
phase: phase-0-definition
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0001, AP-0003]
related_docs: [ROADMAP.md, CHECKLIST.md, project/tracking/ap-index.md, project/tracking/phase-tracking.md]
related_adrs: [ADR-0001]
---

## Objective

Make repository state always visible: a master checklist, a project roadmap, a phase-tracking board,
and an AP index — all cross-linked so any reader reaches live state in one hop.

## Scope

**In:** `ROADMAP.md`, `CHECKLIST.md`, `phase-tracking.md`, `ap-index.md`; the full 37-AP listing
(Phase 0 committed, later provisional); cross-links.
**Out:** the workflow *rules* behind them (AP-0003).

## Deliverables

- `ROADMAP.md` (7-phase spine + completion criteria)
- `CHECKLIST.md` (master checklist)
- `project/tracking/phase-tracking.md`
- `project/tracking/ap-index.md` (all 37 APs)

## Acceptance Criteria

- [x] Roadmap lists all 7 phases with goals + completion criteria
- [x] Master checklist rolls up phases and Phase-0 APs
- [x] AP index lists all 37 APs with status; Phase 0 committed, rest provisional
- [x] Trackers cross-link to phases/APs and back
- [x] Documentation updated (single source of truth, front-matter current)
- [x] `CHANGELOG.md` updated

## Dependencies

- AP-0001, AP-0003

## Status / Log

- 2026-06-15 — Proposed → In Progress. Roadmap, checklist, phase tracking, and AP index authored.
- 2026-06-15 — In Review → Done. Reviewed & approved; all acceptance criteria met.
