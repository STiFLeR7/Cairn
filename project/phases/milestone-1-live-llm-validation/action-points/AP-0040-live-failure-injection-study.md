---
id: AP-0040
title: Live failure-injection study (Phase 5 matrix, real model)
phase: milestone-1-live-llm-validation
status: In Progress
owner: maintainers
created: 2026-06-16
updated: 2026-06-16
depends_on: [AP-0039]
related_docs: [benchmarks/live_study.py, benchmarks/scenarios.py, benchmarks/recovery_matrix.py, docs/concepts/recovery-fidelity.md]
related_adrs: [ADR-0009, ADR-0010]
---

## Objective

Run the Phase 5 failure-injection benchmark **live** against a real model — the step × failure-type ×
baseline matrix (B0 cold-restart / B1 log-replay / B2 snapshot-only / B3 RGR), the ablation study, and the
cross-version resume experiment — capturing raw results and transcripts. The aim is to obtain genuine
non-deterministic evidence, especially for the claims a deterministic mock cannot exercise: C4 (RGR holds
where log-replay B1 *fails* under non-determinism) and whether C5's reference-harness fidelity cliff
survives a real model that actually uses decisions and dead-ends.

## Scope

**In:** running `recovery_matrix.py`, `ablation_study.py`, and `cross_version_resume.py` against an injected
real model via the AP-0038/0039 machinery; multiple seeds/repetitions per cell where cost allows; persisting
raw per-run results + transcripts for analysis; recording the model, version, seeds, and cost of the study.
**Out:** the statistical analysis and claims verdicts (AP-0041); changing the benchmark *design* (it reuses
the Phase 5 matrix — design changes would need their own AP); guaranteeing a particular outcome.

## Deliverables

- Captured live results for the recovery matrix, ablation, and cross-version experiments (raw + transcripts).
- A run manifest: model, version, seeds, repetitions, date, and total cost.

## Acceptance Criteria

- [x] **Runner built and offline-validated** — `benchmarks/live_study.py` runs the Phase 5 matrix through
      the live pipeline (`LiveModelProvider` + `live_controls`); on a deterministic fake transport it
      reproduces C1 (B3 tax 1.50 vs B0 5.00; no-regression 1.0 vs 0.0) and C3 (B3 dup 0 / gate PASS vs B0 1)
- [ ] The Phase 5 matrix, ablation, and cross-version experiments run end-to-end against a **real model** —
      *gated on explicit approval (paid API); swap in `build_live_transport(model=…)`*
- [ ] Results are captured with enough repetition to observe non-determinism (≥ a documented N per cell)
- [ ] Raw results + transcripts + a run manifest (model/version/seed/cost) are persisted and reproducible
      via the AP-0039 replay path
- [ ] Honest framing preserved (ADR-0009): the run is reported as-is, including any failures or noise
- [x] Docs + trackers updated (`REPRODUCE.md`, `Makefile` `bench-live`)

## Dependencies

- `AP-0039` (determinism/cost/repro controls), transitively `AP-0038`

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M1 entry).
- 2026-06-16 — Accepted → In Progress. **Runner delivered and offline-validated.** Added the live-pipeline
  wiring in `benchmarks/scenarios.py` (`fake_multifile_transport`, `live_multi_file_scenario`,
  `live_effectful_scenario`, and the gated `build_live_transport(model, …)`) and the runnable
  `benchmarks/live_study.py` (+ `make bench-live`). The fake transport is functionally equivalent to the
  scripted mock, so the matrix reproduces C1/C3 **through the live code path** end-to-end (prompt render →
  parse → harness → matrix → metrics). `tests/test_live_study.py` (5 offline tests) → **69 passed**.
  **Remaining (gated):** swap the fake for `build_live_transport(model=…)` with `ANTHROPIC_API_KEY` and an
  approved budget to run the actual paid study; capture transcripts + a manifest. The offline run validates
  the *pipeline*, not the claims under a real model — no claims-registry update is made from it (ADR-0009).
