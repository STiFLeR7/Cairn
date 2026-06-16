---
id: AP-0040
title: Live failure-injection study (Phase 5 matrix, real model)
phase: milestone-1-live-llm-validation
status: Done
owner: maintainers
created: 2026-06-16
updated: 2026-06-16
depends_on: [AP-0039]
related_docs: [benchmarks/live_study.py, benchmarks/scenarios.py, benchmarks/transcripts/openrouter_owl-alpha-recovery-study.jsonl, docs/research/claims-registry.md]
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
- [x] The recovery matrix runs end-to-end against a **real model** — `openrouter/owl-alpha` via OpenRouter,
      authorized by the user (free model); enabled by `CAIRN_LIVE_MODEL` in `benchmarks/live_study.py`
- [x] Run with repetition enough to **observe non-determinism** — two runs flipped per-baseline
      `task_success`/`recovery_tax` (informal N=2; a structured per-cell N is future work)
- [x] Transcripts persisted and offline-replayable (`benchmarks/transcripts/openrouter_owl-alpha-recovery-study.jsonl`)
- [x] **Honest framing preserved (ADR-0009)** — reported as-is: the run did **not** validate C1 (the model
      batched all files into one action and finished before the k=2 crash, so recovery was never exercised;
      a spurious "SUPPORTED" verdict that ignored `task_success` was fixed). Analysis → AP-0041.
- [x] Docs + trackers updated (`REPRODUCE.md`, `Makefile` `bench-live`, claims registry)

## Dependencies

- `AP-0039` (determinism/cost/repro controls), transitively `AP-0038`

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M1 entry).
- 2026-06-16 — Accepted → In Progress. **Runner delivered and offline-validated.** Live-pipeline wiring in
  `benchmarks/scenarios.py` + runnable `benchmarks/live_study.py` (+ `make bench-live`); the fake transport
  reproduces C1/C3 through the live code path. `tests/test_live_study.py` → 69 passed.
- 2026-06-16 — In Progress → **Done. Live study executed against a real model** (user-authorized). Added the
  stdlib `openrouter_transport` (OpenAI-compatible, no new dependency) and ran `openrouter/owl-alpha` via
  OpenRouter through the full live pipeline. **Outcome (honest, negative for the claims):** the model batches
  the whole multi-file task into a single action and finishes before the injected crash, so the Phase-5
  recovery scenario/metrics — built around the mock's one-action-per-step cadence — do not validate C1.
  Fixed two issues the run exposed: a non-fence-tolerant parser (`owl-alpha` emits XML tool-call / bare-code)
  and a C1 verdict that ignored `task_success`. Transcript captured + replayable.
- 2026-06-16 — **Follow-up (systematic-debugging pass): benchmark-integrity bug found + fixed.** The
  "unstable metrics" were a symptom of a real defect — `run_until_failure` never checked that the injected
  crash *fired*, so a batchable task that the model one-shots produced a **vacuous** cell that `run_matrix`
  scored as a perfect recovery (`task_success=True, tax=0` — a false positive). Root-caused with a
  deterministic probe; fixed test-first (`tests/test_eval_injection.py`): `run_until_failure` →
  `Injection(fired, completed)`; `run_matrix` **skips + reports** non-fired cells. The live study now
  correctly prints *"k=2 cells skipped — model finished before the crash; recovery not exercised."* No
  hardcoded harness: the model id lives only in `.env`/env, never in core (ADR-0007).
