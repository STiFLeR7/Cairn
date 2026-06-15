---
id: AP-0012
title: State taxonomy + tool effect taxonomy (conceptual)
phase: phase-1-conceptual-foundation
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0007, AP-0010]
related_docs: [docs/concepts/state-taxonomy.md, docs/concepts/tool-effect-taxonomy.md]
related_adrs: [ADR-0001]
---

## Objective

Author the two taxonomies that feed Phase 2 design: the **state taxonomy** (what kinds of agent state
exist, how recoverable each is, and which layer owns it) and the **tool effect taxonomy** (classifying
tools by reversibility/idempotency and the recovery policy each class implies).

## Scope

**In:** the five-layer state taxonomy (durable external / irreversible effects / working memory / plan /
runtime handles) with recoverability + owner mapping; the three-class tool taxonomy (`safe-to-retry`,
`check-before-retry`, `never-retry`) with the recovery policy per class.
**Out:** the Continuation State *schema* (Phase 2, AP-0013); the effect-safety *protocol* (Phase 2,
AP-0017) — these consume the taxonomies but are designed later.

## Deliverables

- `docs/concepts/state-taxonomy.md` — the five layers, recoverability, and owning layer.
- `docs/concepts/tool-effect-taxonomy.md` — the three classes and their recovery policies.

## Acceptance Criteria

- [x] State taxonomy enumerates the layers with recoverability and owner (Code Harness / Runtime)
- [x] The working-memory layer is identified as the crux (non-serializable) and the durable/effect
      layers as Runtime-owned
- [x] Tool taxonomy defines three classes, each with an explicit recovery policy and an example
- [x] Both docs state how they feed specific Phase 2 APs (AP-0013, AP-0017)
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- AP-0007 (problem), AP-0010 (the two-layer ownership model)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 1 entry).
- 2026-06-15 — Accepted → Done. Delivered `docs/concepts/state-taxonomy.md` (5 layers, owners) and
  `docs/concepts/tool-effect-taxonomy.md` (3 classes, WAL discipline, scope limit).
