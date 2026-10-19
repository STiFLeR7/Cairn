---
id: AP-0053
title: Calibration run, capability-matched C1 verdict, live C3 verdict, gate verdict
phase: milestone-5-v1-gate
status: Done
owner: maintainers
created: 2026-10-19
updated: 2026-10-19
depends_on: []
related_docs: [docs/superpowers/specs/2026-10-19-m5-v1-gate-design.md, src/cairn/eval/runner.py, src/cairn/eval/calibration.py, benchmarks/scenarios.py]
related_adrs: [ADR-0009]
---

## Objective

Make the v1.0 verdict judge recovery relative to each model's own capability, and wire C3 (effect safety)
into the live run, so model reliability no longer confounds the C1 verdict.

## Scope

**In:** `run_calibration` (10 uncrashed chain runs per model; eligible iff rate >= 0.80 and >= 9 runs
completed); `verdict_c1_capability` (success >= calibration - 0.10 and >= B0; B3 tax max < B0 tax min;
no regression; B0 >= 1 success); `verdict_c3_live` (B3 0 duplicates in every fired cell, B0 >= 1);
`verdict_v1_gate` (INCONCLUSIVE / GO / NO-GO, loss threshold 10%); `live_chain_effect_scenario` composing
the live chain with an `EffectSpec(key="send-report")` torn at the crash step; `benchmarks/m5_study.py`.
**Out:** changing the strict `verdict_c1` (kept for comparison); C2/C4/C5.

## Acceptance Criteria

- [x] Every verdict branch unit-tested on synthetic summaries
- [x] Calibration eligibility rule implemented and tested
- [x] Live scenario exercises C1 and C3 together at no extra calls
- [x] `m5_study.py` refuses to run on any pre-registration mismatch

## Status / Log

- 2026-10-19 — Done. Implemented and reviewed on branch `milestone-5-v1-gate`.
