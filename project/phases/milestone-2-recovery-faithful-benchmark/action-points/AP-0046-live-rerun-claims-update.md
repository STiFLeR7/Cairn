---
id: AP-0046
title: Live re-run + claims update (C1–C5, with statistics)
phase: milestone-2-recovery-faithful-benchmark
status: In Progress
owner: maintainers
created: 2026-06-16
updated: 2026-06-23
depends_on: [AP-0045]
related_docs: [docs/research/claims-registry.md, PAPER.md, benchmarks/live_study.py]
related_adrs: [ADR-0009]
---

## Objective

Run the new non-batchable benchmark **live** against a real model (e.g. `openrouter/owl-alpha` or a more
instruction-reliable model), with repetitions, and record dated **live** evidence for C1–C5 — supporting or
refuting — with the statistics. This is the run M1 could not produce because the old task was batchable.

## Scope

**In:** a budgeted, transcript-recorded live run of the AP-0045 harness on the AP-0043 task; a per-claim live
verdict with mean ± spread, scoped "live-LLM study (M2)"; updates to the claims registry and `PAPER.md`.
Gated on the same cost discipline as M1 (budget ceiling; transcripts replay offline).
**Out:** the v1.0 decision (AP-0047). Re-running is allowed; manufacturing a positive result is not — a
negative is recorded honestly (ADR-0009).

## Acceptance Criteria

- [ ] The non-batchable task runs live with injected crashes that **actually fire** (no all-skipped matrix)
- [ ] C1–C5 carry dated **live (M2)** evidence with repetition statistics, distinct from M1 / reference notes
- [ ] Transcripts + manifest persisted and offline-replayable
- [ ] Honest framing (ADR-0009): negatives/insufficient evidence recorded, not buried
- [ ] Claims registry + `PAPER.md` updated; trackers updated

## Dependencies

- `AP-0045` (repetition harness), transitively `AP-0043`/`AP-0044`

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M2 entry).
- 2026-06-23 — In Progress. Rewired `benchmarks/live_study.py::run_live_study` onto the
  **non-batchable chain** (AP-0043) with the **repetition harness** (AP-0045): runs the B0-vs-B3
  contrast `repeats` times via `run_repeated`, prints mean±spread + fired/skipped, computes the
  `verdict_c1`, and writes an auditable **manifest** (`*-chain-study.manifest.json`: model, task,
  steps, repeats, fired/skipped, serialized stats, verdict, honest-scope note) beside the replayable
  transcript. The runner accepts an injected `transport`, so the entire pipeline is validated
  **offline** with the deterministic fake chain transport — `tests/test_live_study.py::
  test_live_study_runs_on_chain_offline` asserts crashes fire (nothing skipped), C1 SUPPORTED with
  stats, and the manifest is written. The script-only `_bootstrap` import was made resilient so the
  module imports cleanly under pytest. Suite **98 → 99 passed**. **The gated live network run
  (owl-alpha, key from `.env`) is pending explicit approval** — only the transport changes from the
  offline-validated path; the claims-registry/PAPER updates follow the real result (positive or
  negative, ADR-0009).
