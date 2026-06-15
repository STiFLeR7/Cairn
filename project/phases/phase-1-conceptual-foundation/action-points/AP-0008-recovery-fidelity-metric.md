---
id: AP-0008
title: Define recovery-fidelity metric & eval dimensions (conceptual)
phase: phase-1-conceptual-foundation
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0007]
related_docs: [docs/concepts/recovery-fidelity.md]
related_adrs: [ADR-0001]
---

## Objective

Define **recovery fidelity** as *outcome equivalence* (since faithful trajectory replay is impossible
under non-determinism), and specify its measurable axes. Conceptual only — the implementation and
experiments are Phase 5.

## Scope

**In:** the argument for outcome- (not trajectory-) equivalence; the axes — task success, solution
quality, no-regression, effect-safety, recovery tax (extra tokens/time/$); how each axis is observed in
principle; the baseline-comparison framing (vs cold restart / log-replay / snapshot-only).
**Out:** metric *code*, datasets, and the failure-injection harness (Phase 5); statistical methodology
detail (revisited in Phase 5).

## Deliverables

- `docs/concepts/recovery-fidelity.md` defining each axis, its intuition, and what an "ideal" recovery
  scores; a table mapping axes → future Phase 5 measurements.

## Acceptance Criteria

- [x] Fidelity is defined as outcome equivalence, with the rationale (non-determinism) stated
- [x] At least five axes are defined, each with a precise meaning and direction (higher/lower = better)
- [x] The baseline set is named and the comparison framing is explicit
- [x] Each axis is linked forward to how Phase 5 will measure it
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- AP-0007 (continuation equivalence is the basis for fidelity)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 1 entry).
- 2026-06-15 — Accepted → Done. Delivered `docs/concepts/recovery-fidelity.md` (outcome equivalence,
  five axes, four baselines, sufficiency ablation, Phase 5 forward map).
