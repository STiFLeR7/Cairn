---
id: AP-0044
title: Action-granularity-robust recovery metrics
phase: milestone-2-recovery-faithful-benchmark
status: Accepted
owner: maintainers
created: 2026-06-16
updated: 2026-06-16
depends_on: [AP-0043]
related_docs: [src/cairn/eval/metrics.py, docs/concepts/recovery-fidelity.md]
related_adrs: [ADR-0009]
---

## Objective

Redefine the recovery metrics so they measure recovery in **progress / work-units** rather than assuming the
mock's one-action-per-step cadence. M1 showed `recovery_tax` and `no_regression` become meaningless when a
real model chunks the work differently than the scripted mock. The five fidelity axes stay; their definitions
become granularity-robust.

## Scope

**In:** redefine `no_regression` and `recovery_tax` in terms of **completed work units** (e.g. how many of the
sequential chain's links the recovery had to redo vs the genuinely-remaining links), independent of how many
model *actions* that took; keep `task_success` (oracle), `effect_duplicates` (gate), and `solution_quality`
(digest proxy). Document the new definitions in `recovery-fidelity.md`. Keep the deterministic suite passing
(the new definitions must reduce to the old numbers on the one-action-per-step mock, or the tests are updated
with rationale).
**Out:** the task itself (AP-0043); repetition/statistics (AP-0045).

## Acceptance Criteria

- [ ] `no_regression` / `recovery_tax` defined in progress/work-units, not action counts
- [ ] Metrics give stable, interpretable values whether the model takes one action or many per work-unit
- [ ] `recovery-fidelity.md` updated; the change is traceable to the M1 finding
- [ ] Deterministic eval suite green (old behavior preserved or updated with rationale)

## Dependencies

- `AP-0043` (the work-unit notion comes from the sequential task)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M2 entry).
