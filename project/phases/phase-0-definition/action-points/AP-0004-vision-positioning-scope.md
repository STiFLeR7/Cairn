---
id: AP-0004
title: Author vision, positioning & scope docs
phase: phase-0-definition
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0001]
related_docs: [docs/vision/vision.md, docs/vision/positioning.md, docs/vision/scope.md]
related_adrs: [ADR-0001]
---

## Objective

Establish the project's identity in prose: why it exists (vision), where it sits in the ecosystem
(positioning), and what it will and will not do (scope).

## Scope

**In:** vision statement + problem framing + thesis; positioning statement, audience, prior-art stance;
v1 scope, long-term scope, permanent non-goals.
**Out:** the detailed related-work matrix (Phase 1, AP-0009); the conceptual framework (Phase 1, AP-0010).

## Deliverables

- `docs/vision/vision.md`
- `docs/vision/positioning.md`
- `docs/vision/scope.md`

## Acceptance Criteria

- [x] Vision states the problem, the thesis ("Checkpoints Are Compactions"), and what Cairn makes true
- [x] Positioning states what Cairn is/is not, audience tiers, and prior-art stance
- [x] Scope states the three v1 pillars, the long-term arc, and permanent non-goals
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)
- [x] Maintainer approves vision/positioning/scope

## Dependencies

- AP-0001

## Status / Log

- 2026-06-15 — Proposed → In Progress. Vision, positioning, and scope authored; awaiting maintainer approval.
- 2026-06-15 — In Review → Done. Maintainer reviewed & approved vision/positioning/scope.
