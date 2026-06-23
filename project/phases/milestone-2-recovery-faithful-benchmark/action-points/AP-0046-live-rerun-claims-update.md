---
id: AP-0046
title: Live re-run + claims update (C1–C5, with statistics)
phase: milestone-2-recovery-faithful-benchmark
status: Done
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

- [x] The non-batchable task runs live with injected crashes that **actually fire** (no all-skipped matrix)
      — **fired=4, skipped=0** against `nvidia/nemotron-3-super-120b-a12b:free`.
- [x] C1–C5 carry dated **live (M2)** evidence with repetition statistics, distinct from M1 / reference notes
      — C1 has dated M2 live stats (suggestive, n=2); C2/C4/C5 explicitly remain reference-harness; C3 not wired.
- [~] Transcripts + manifest persisted and offline-replayable — **manifest persisted** (the citable artifact);
      the raw transcript was lost to a record-truncation footgun (now fixed) and **regeneration is rate-limited
      (free-tier HTTP 429)**. Disclosed, not buried.
- [x] Honest framing (ADR-0009): negatives/insufficient evidence recorded, not buried — C1 reported
      **suggestive, NOT confirmed**; underpowered n=2 and the rate-limit block are recorded.
- [x] Claims registry + `PAPER.md` updated; trackers updated

## Dependencies

- `AP-0045` (repetition harness), transitively `AP-0043`/`AP-0044`

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M2 entry).
- 2026-06-23 — In Progress. Rewired `benchmarks/live_study.py::run_live_study` onto the
  **non-batchable chain** (AP-0043) with the **repetition harness** (AP-0045): runs the B0-vs-B3
  contrast `repeats` times via `run_repeated`, prints mean±spread + fired/skipped, computes the
  `verdict_c1`, and writes an auditable **manifest** beside the replayable transcript. The runner
  accepts an injected `transport`, so the entire pipeline is validated **offline** with the
  deterministic fake chain transport (`tests/test_live_study.py::test_live_study_runs_on_chain_offline`).
- 2026-06-23 — **Live run executed (user-approved) — Done with one partial deliverable.** Ran the chain
  study live against `nvidia/nemotron-3-super-120b-a12b:free` (OpenRouter; owl-alpha was format-unreliable
  and `nemotron-3-ultra-550b` returned gateway 504s). **The injected crash fired in all 4 cells (skipped=0)
  — the M1 blocker is resolved; recovery was exercised against a real model for the first time.** At n=2:
  **B3/RGR 2/2 success, tax 1.0±0.0**; **B0/cold-restart 1/2 success, tax 2.5±2.5**. RGR dominates on every
  axis mean and on reliability, but the strict `verdict_c1` is **NOT SHOWN** (B0's failed repeat has tax 0,
  overlapping B3; n=2 underpowered) — recorded honestly as **C1 suggestive, not confirmed live**. Claims
  registry + `PAPER.md §9` updated (2026-06-23). **Hardening shipped for the live path:** a `retrying`
  control in `live_controls.py` (bounded backoff on transient 429/5xx/"Provider returned error"; permanent
  4xx fail fast; 4 tests), filesystem-safe transcript slugs (the `:free` colon was opening an NTFS ADS on
  Windows), and **record-to-`.partial`-then-finalize** so a crashing re-run never clobbers a prior transcript.
  **Partial deliverable:** the raw transcript was lost to that footgun *before* it was fixed (a rate-limited
  larger run truncated it); the **manifest** survived and is the persisted evidence. A **powered re-run**
  (more repeats / both crash points / a clean replayable transcript) is **blocked by the free-tier rate limit
  (HTTP 429)** and remains available when the window resets. Suite **99 → 103 passed**.
