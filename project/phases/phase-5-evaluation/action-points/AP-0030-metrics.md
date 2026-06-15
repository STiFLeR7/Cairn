---
id: AP-0030
title: Metrics implementation (five fidelity axes)
phase: phase-5-evaluation
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0029]
related_docs: [docs/concepts/recovery-fidelity.md, docs/concepts/tool-effect-taxonomy.md]
related_adrs: [ADR-0009]
---

## Objective

Implement the five recovery-fidelity axes as measurement functions against the **uninterrupted reference
run**, and a `RecoveryReport` that carries them. Effect-safety is a **gate**, never averaged into a scalar.

## Scope

**In:** `task_success` (task oracle), `solution_quality` (artifact-digest match ratio vs the reference
run), `no_regression` (pre-failure completed artifacts still present + correct after recovery),
`effect_safety` (count of duplicate/spurious external effects vs ledger ground truth — lower better, 0
ideal), `recovery_tax` (steps/work from failure to completion); a `RecoveryReport` aggregating them with a
`passes_gate` flag.
**Out:** LLM-judge quality grading (v1 uses the deterministic artifact-digest proxy; noted in ADR-0009).

## Deliverables

- `src/cairn/eval/metrics.py` — the five axis functions + `RecoveryReport` (+ `passes_gate`).
- Tests: each axis on hand-built before/after states; effect-safety counts duplicates; gate behavior.

## Acceptance Criteria

- [x] All five axes implemented and computed against the uninterrupted reference run
- [x] Effect-safety is reported as a hard gate (a single duplicate fails the gate regardless of success)
- [x] No-regression penalizes discarding/corrupting pre-failure completed work
- [x] Recovery tax captures recovery cost (post-failure steps) distinct from the reference cost
- [x] Documentation + trackers updated; unit tests pass

## Dependencies

- AP-0029 (recovered runs to score)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 5 entry).
- 2026-06-15 — Accepted → Done. Delivered `eval/metrics.py` (five axes + RecoveryReport gate); tests pass.
