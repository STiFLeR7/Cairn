---
id: AP-0045
title: Repetition + statistics harness (injection-fired enforced)
phase: milestone-2-recovery-faithful-benchmark
status: Accepted
owner: maintainers
created: 2026-06-16
updated: 2026-06-16
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

- [ ] Each cell runs `N` times; per-axis mean ± spread reported per baseline
- [ ] Fired-vs-skipped counts surfaced; vacuous cells excluded from the statistics (M1 fix carried forward)
- [ ] A verdict is "supported" only when consistent across repetitions and B-task success holds
- [ ] Deterministic suite green; the runner stays usable offline (fake transport) and live

## Dependencies

- `AP-0044` (granularity-robust metrics to aggregate)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M2 entry).
