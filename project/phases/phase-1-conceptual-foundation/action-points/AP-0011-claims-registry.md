---
id: AP-0011
title: Establish research claims registry
phase: phase-1-conceptual-foundation
status: Accepted
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0007, AP-0008]
related_docs: [docs/research/claims-registry.md]
related_adrs: [ADR-0001]
---

## Objective

Stand up the **research claims registry**: the append-only list of falsifiable claims the project
commits to defending. Registering claims early keeps the work honest — every later phase either
supports, refines, or refutes a registered claim.

## Scope

**In:** the claim schema (ID, statement, rationale, how-it-will-be-evaluated, status); the freeze policy
(claims are immutable once registered — refinement happens via a new superseding claim); an initial set
of falsifiable claims.
**Out:** actually evaluating the claims (Phase 5); the metric definitions themselves (AP-0008).

## Deliverables

- `docs/research/claims-registry.md` with the schema, the freeze policy, and at least four initial
  falsifiable claims, e.g.:
  - **C1** — Re-grounding recovery achieves higher recovery fidelity than cold restart after failure.
  - **C2** — Unified distillation (compaction≡checkpoint) does not degrade checkpoint fidelity relative
    to a checkpoint-only baseline (core/tail hypothesis).
  - **C3** — The effect-safety WAL eliminates duplicate irreversible effects on resume for
    `check-before-retry` tools.
  - **C4** — Re-grounding resume is robust to cross-version resume where log-replay is not.

## Acceptance Criteria

- [ ] Claim schema defined and the freeze policy stated
- [ ] At least four claims registered, each falsifiable and each naming how it will be evaluated
- [ ] Each claim references the fidelity axis (AP-0008) it will be judged on, where applicable
- [ ] Documentation updated (single source of truth, front-matter current)
- [ ] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- AP-0007 (problem), AP-0008 (fidelity axes the claims reference)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 1 entry).
