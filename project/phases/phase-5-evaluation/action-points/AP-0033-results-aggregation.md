---
id: AP-0033
title: Results aggregation & claims update
phase: phase-5-evaluation
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0030, AP-0031, AP-0032]
related_docs: [docs/research/claims-registry.md, docs/concepts/recovery-fidelity.md]
related_adrs: [ADR-0009]
---

## Objective

Run the full benchmark — the (step × failure-type × baseline) matrix plus the ablation and cross-version
experiments — aggregate the per-axis results into a readable table, and **update the claims registry**
with dated, honestly-scoped evidence for C1–C5.

## Scope

**In:** a matrix runner that sweeps scenarios × failure steps × baselines, collects `RecoveryReport`s, and
aggregates (per-baseline means, gate pass-rates); a `benchmarks/recovery_matrix.py` that prints the table;
status updates in `docs/research/claims-registry.md` (C1/C3 supported; C2/C4/C5 evidenced) with explicit
scope limits.
**Out:** a live-LLM empirical study and statistical significance testing (future work; flagged in ADR-0009).

## Deliverables

- `src/cairn/eval/runner.py` — `run_matrix(...)` + aggregation.
- `benchmarks/recovery_matrix.py` — runnable end-to-end benchmark printing the results table.
- `docs/research/claims-registry.md` — Status log updated for C1–C5 with dated notes + scope.

## Acceptance Criteria

- [x] `run_matrix` produces a results table over (step × type × baseline) with the five axes
- [x] C1 supported (B3 > B0 on tax + no-regression); C3 supported (0 duplicate effects with WAL)
- [x] C2/C5 evidenced by the ablation; C4 evidenced by the cross-version experiment
- [x] Claims registry Status lines updated with dated notes **and** explicit scope (deterministic harness)
- [x] `benchmarks/recovery_matrix.py` runs end-to-end; full `pytest` suite green
- [x] Documentation + CHANGELOG + trackers updated; Phase 5 completion criteria met

## Dependencies

- AP-0030 (metrics), AP-0031 (ablation), AP-0032 (cross-version)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 5 entry).
- 2026-06-15 — Accepted → Done. Delivered `eval/runner.py` + `benchmarks/recovery_matrix.py`; C1/C3 SUPPORTED; claims registry updated with dated, scoped evidence.
