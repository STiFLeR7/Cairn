---
id: AP-0048
title: Success-conditioned recovery tax (fairness fix)
phase: milestone-3-powered-live-study
status: Done
owner: maintainers
created: 2026-06-29
updated: 2026-06-29
depends_on: [AP-0045]
related_docs: [src/cairn/eval/runner.py, tests/test_eval_tax_fairness.py]
related_adrs: [ADR-0009]
---

## Objective

Close the fairness gap the M2 v1.0 go/no-go flagged: `recovery_tax` must be the cost of a **successful
recovery**, so a run that *fails* the task cannot register a misleadingly low ("cheap") tax and thereby
look good — or let a baseline "win" by failing cheaply.

## Scope

**In:** measure `recovery_tax` over successful repetitions only in `aggregate_repeated`; expose `n_success`
and keep `recovery_tax_all` (full distribution) for transparency; harden `verdict_c1` to compare
cost-of-success to cost-of-success and to decline when the competitor (B0) never actually recovers; tests
pinning the property directly via hand-built `RecoveryReport`s.
**Out:** the live run (AP-0050); any new task or provider.

## Acceptance Criteria

- [x] `recovery_tax` aggregated over successful reports only; `n_success` + `recovery_tax_all` exposed
- [x] A failed, low-work run does not pull the reported tax down (tested)
- [x] `verdict_c1` declines when B0 has zero successful recoveries (no cost-of-recovery to compare)
- [x] Cheap competitor *failures* no longer suppress a genuine B3 win (tested)
- [x] Deterministic all-success case unchanged (success-conditioning is a no-op there); full suite green

## Status / Log

- 2026-06-29 — Done. `aggregate_repeated` now computes `recovery_tax` over `task_success` reports only,
  adds `n_success` and `recovery_tax_all`; `format_repeated_table` shows `n_success`. `verdict_c1` requires
  B0 to have ≥1 successful recovery (else "B0 never completed the recovery … not a cheap recovery") and
  compares the success-conditioned taxes. New `tests/test_eval_tax_fairness.py` (4 tests) pins: tax measured
  over successes only; cheap failures don't suppress a real win; a never-recovering competitor isn't a cheap
  win; deterministic all-success unchanged. Suite **103 → 107** (with AP-0049: 110) passed.
