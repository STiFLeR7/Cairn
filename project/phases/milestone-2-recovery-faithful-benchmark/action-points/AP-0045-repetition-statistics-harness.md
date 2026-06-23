---
id: AP-0045
title: Repetition + statistics harness (injection-fired enforced)
phase: milestone-2-recovery-faithful-benchmark
status: Done
owner: maintainers
created: 2026-06-16
updated: 2026-06-23
depends_on: [AP-0044]
related_docs: [src/cairn/eval/runner.py, benchmarks/live_study.py]
related_adrs: [ADR-0009]
---

## Objective

Run each (failure-step × baseline) cell **N times** and report results with their spread, so a
non-deterministic real model yields evidence with uncertainty rather than a single noisy number. Build on the
M1 injection-fired integrity fix: vacuous cells (crash never fired) are skipped and reported, never averaged
into the signal.

## Scope

**In:** extend the matrix runner to repeat each cell `N` times (seeded where the model supports it),
aggregating mean ± spread per axis per baseline; surface the count of fired vs skipped cells; a verdict helper
that only reports "supported" when the effect is consistent across repetitions (and B-task actually succeeds).
**Out:** the live run itself (AP-0046); the task (AP-0043) and metric definitions (AP-0044).

## Acceptance Criteria

- [x] Each cell runs `N` times; per-axis mean ± spread reported per baseline
- [x] Fired-vs-skipped counts surfaced; vacuous cells excluded from the statistics (M1 fix carried forward)
- [x] A verdict is "supported" only when consistent across repetitions and B-task success holds
- [x] Deterministic suite green; the runner stays usable offline (fake transport) and live

## Dependencies

- `AP-0044` (granularity-robust metrics to aggregate)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M2 entry).
- 2026-06-23 — Done. Added the repetition + statistics layer to `src/cairn/eval/runner.py`:
  `run_repeated(scenario, steps, baselines, *, repeats, base_factory, on_skip, before_repeat)`
  runs the matrix `N` times (each a full `run_matrix` pass, so the reference is re-run per repeat
  and the M1 injection-fired skip is enforced), returning a `RepeatedRun(reports, fired, skipped,
  repeats, …)`. `aggregate_repeated` yields per-baseline `AxisStat(mean, stdev, min, max, n)` per
  axis (population stdev → 0 for a deterministic model) plus `effect_duplicates_total` and
  `gate_pass_rate`; vacuous cells are excluded (an all-skipped run aggregates to `{}`).
  `verdict_c1` returns "supported" **only** when both B0/B3 fired, B3 completes the task in *every*
  repetition, B3's recovery tax is strictly lower with **no overlap** across repeats
  (`B3.tax.max < B0.tax.min`), and B3 ≥ B0 on mean no-regression — a lower tax on a failed task is
  never support. `before_repeat(i)` is the seam a live runner uses to vary seed/temperature
  between repeats (deterministic scenarios ignore it). `format_repeated_table` renders mean±spread.
  Wired an offline repeated study on the **non-batchable chain** into `benchmarks/live_study.py`
  (`run_offline_repeated_study`) — the exact machinery AP-0046 runs live, transport-swapped.
  **Hygiene fix found while validating:** `world_digest` now excludes Python bytecode caches
  (`__pycache__`, `.pyc`/`.pyo`) — importing the planted `oracle` created a `.pyc` whose
  non-reproducible header dropped `solution_quality` to 0.67 and could trigger spurious torn-write
  detection; with it excluded the recovered chain matches the reference exactly (1.0). Tests:
  `tests/test_eval_repetition.py` (8) + chain solution_quality==1.0 guard. Suite **90 → 98 passed**.
