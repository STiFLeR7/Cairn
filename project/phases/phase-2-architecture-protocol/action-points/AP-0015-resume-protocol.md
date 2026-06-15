---
id: AP-0015
title: Re-grounding resume protocol spec
phase: phase-2-architecture-protocol
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0013, AP-0014, AP-0017]
related_docs: [docs/design/resume-protocol.md]
related_adrs: [ADR-0004]
---

## Objective

Specify the **Re-grounding Recovery (RGR)** resume protocol step by step: the sequence the agent follows
after failure — load → re-observe → reconcile (torn-step detection) → re-plan → continue — and exactly
what happens at each step, including how the "torn step" between last checkpoint and failure is handled.

## Scope

**In:** the five-step protocol; torn-step reconciliation (using the effect ledger to detect
INTENT-without-COMPLETE); the "re-observe before re-act" rule; why re-planning may take a different valid
path (non-determinism is a feature here); the resume bootstrap (re-establishing runtime handles). An ADR
(ADR-0004) for re-grounding-not-replay as the resume strategy.
**Out:** the effect-safety *protocol details* (AP-0017); the distillation that wrote `S` (AP-0016);
implementation.

## Deliverables

- `docs/design/resume-protocol.md` — the step-by-step protocol with a sequence diagram and the torn-step
  decision logic.
- `docs/adr/ADR-0004-regrounding-not-replay.md` — decision: resume by re-grounding, not trajectory replay.

## Acceptance Criteria

- [x] All five steps are specified with inputs/outputs and the boundary-contract calls they make
- [x] Torn-step reconciliation is defined (detect + resolve the last-checkpoint→failure window)
- [x] "Re-observe before re-act" is explicit; effect-safety hand-off to AP-0017 is referenced
- [x] Consistent with the boundary contract (AP-0014) and the schema (AP-0013)
- [x] ADR-0004 records the re-grounding-not-replay decision
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- AP-0013 (schema), AP-0014 (contract), AP-0017 (effect-safety used during reconcile)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 2 entry).
- 2026-06-15 — Accepted → Done. Delivered `docs/design/resume-protocol.md` + ADR-0004.
