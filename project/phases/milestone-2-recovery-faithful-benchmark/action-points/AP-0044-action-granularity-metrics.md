---
id: AP-0044
title: Action-granularity-robust recovery metrics
phase: milestone-2-recovery-faithful-benchmark
status: Done
owner: maintainers
created: 2026-06-16
updated: 2026-06-23
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

- [x] `no_regression` / `recovery_tax` defined in progress/work-units, not action counts
- [x] Metrics give stable, interpretable values whether the model takes one action or many per work-unit
- [x] `recovery-fidelity.md` updated; the change is traceable to the M1 finding
- [x] Deterministic eval suite green (old behavior preserved or updated with rationale)

## Dependencies

- `AP-0043` (the work-unit notion comes from the sequential task)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M2 entry).
- 2026-06-23 — Done. Redefined `no_regression` and `recovery_tax` in **work units** instead of
  model actions. Added a `Task.progress(workspace) -> Optional[int]` work-unit oracle (default
  `None`; `ChainTask` → chain `pos`, `MultiFileTask` → file count). Plumbed the measurements:
  `RunOutcome.work_units` (the reference's `W`, and each baseline's final units) and
  `Injection.work_at_crash` (measured progress when the crash fired). `no_regression(recovery_units,
  work_at_crash, total_units)` now scores from genuinely-remaining vs. redone **units**:
  `redone = max(0, recovery_units - (W - work_at_crash))`, `1 - redone/work_at_crash`; `recovery_tax`
  is the work-unit count. The non-batchable chain pins one unit per action, so the deterministic
  numbers are unchanged while the definition no longer *assumes* that cadence; a unitless task
  (`progress() → None`) falls back to the original action/`k` form (`score` defaults `work_at_crash`
  to `k`, `total_units` to `n_steps`). The old `no_regression(executed, n_steps, k)` unit test was
  rewritten to the work-unit signature **with rationale** (`tests/test_eval_metrics.py`), plus a
  granularity-robustness test and an exact end-to-end assertion on the chain
  (`recovery_tax == W - work_at_crash`; `tests/test_eval_chain.py`). `recovery-fidelity.md` §2a
  documents the definitions and traces them to the M1 finding. Suite **88 → 90 passed**; the C1
  matrix and C5 ablation tests pass unchanged.
