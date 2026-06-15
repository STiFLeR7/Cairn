---
id: AP-0028
title: Failure-injection harness (step × failure-type matrix)
phase: phase-5-evaluation
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: []
related_docs: [docs/concepts/recovery-fidelity.md]
related_adrs: [ADR-0007, ADR-0009]
---

## Objective

Build the harness that injects a failure at a chosen step `k` of a chosen *type* and captures both the
**uninterrupted reference run** (no failure, the fidelity yardstick) and the **failed run** (state left on
disk after the crash). Generic over task/model/failure-type so any scenario can be swept across the
(step × type) matrix.

## Scope

**In:** `FailureType` taxonomy (crash, context-overflow, tool-timeout, model-error) layered on the
existing `step_hook` seam; `Scenario` (task + model factory + optional effect spec); a function to run the
uninterrupted reference and to run-until-failure at `(k, type)`.
**Out:** the recovery strategies themselves (AP-0029) and metrics (AP-0030). v1 realizes `crash`
faithfully; other types are modeled as a stop-at-`k` with a typed label (honest: noted in ADR-0009).

## Deliverables

- `src/cairn/eval/failure.py` — `FailureType`, injection built on `harness.failure`.
- `src/cairn/eval/scenario.py` — `Scenario` + `run_reference(...)` and `run_until_failure(...)`.
- Tests: reference run completes; failed run stops at `k` leaving durable checkpoints + effect ledger.

## Acceptance Criteria

- [x] Failure injected at step `k` for each declared `FailureType` via a generic seam (no hardcoding)
- [x] The uninterrupted reference run is reproducible and used as the fidelity yardstick
- [x] The failed run leaves the expected durable state (checkpoints, snapshots, effect ledger) for recovery
- [x] Honest labeling of which failure types are faithfully realized vs modeled (ADR-0009)
- [x] Documentation + trackers updated; unit tests pass

## Dependencies

- none (builds on `cairn.harness`)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 5 entry).
- 2026-06-15 — Accepted → Done. Delivered `eval/failure.py` + `eval/scenario.py` (reference + run-until-failure); tests pass.
