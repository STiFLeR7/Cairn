---
id: AP-0007
title: Formalize the recovery problem (continuation sufficiency)
phase: phase-1-conceptual-foundation
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: []
related_docs: [docs/concepts/problem-formalization.md]
related_adrs: [ADR-0001]
---

## Objective

State the agent-recovery problem formally and explain why classical checkpoint/restart does not solve
it. Introduce **continuation sufficiency**: the minimal state `S` from which a resumed agent continues
*equivalently* to an uninterrupted one. This is the conceptual spine the whole project hangs on.

## Scope

**In:** the failure model (what fails, when); the three assumption violations that separate agent
recovery from classical recovery (non-serializable working state, non-deterministic execution,
non-transactional effects); the formal notion of a sufficient statistic for continuation; the
checkpoint-granularity / step-boundary question.
**Out:** the fidelity *metric* (AP-0008); the *mechanism* that produces `S` (Phase 2); any code.

## Deliverables

- `docs/concepts/problem-formalization.md` containing:
  - Failure model and definitions (trajectory, step, world state, effects).
  - The three violations, each with a concrete agent example.
  - Definition of **continuation sufficiency** and the framing of checkpointing as compression of `S`.
  - Statement of open questions handed to later phases (granularity, distillation policy).

## Acceptance Criteria

- [x] The recovery problem is stated with explicit definitions (not prose hand-waving)
- [x] Continuation sufficiency is defined as minimality subject to continuation equivalence
- [x] All three assumption violations are argued with at least one agent example each
- [x] Open questions are enumerated and routed to the phases that will answer them
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- none (foundational)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 1 entry).
- 2026-06-15 — Accepted → Done. Delivered `docs/concepts/problem-formalization.md`
  (failure model, three violations with examples, continuation sufficiency, routed open questions).
