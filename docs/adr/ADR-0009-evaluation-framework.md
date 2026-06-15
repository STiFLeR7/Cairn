---
title: ADR-0009 — Evaluation framework design & honest-results policy
status: frozen
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0028, AP-0029, AP-0030, AP-0031, AP-0032, AP-0033]
related_adrs: [ADR-0007]
---

# ADR-0009 — Evaluation framework & honest-results policy

- **Status:** Accepted
- **Date:** 2026-06-15

## Context

Phase 5 measures recovery instead of asserting it. The recovery-fidelity definition (Phase 1) names five
axes and four baselines; the claims registry names C1–C5. Implementing the benchmark forces choices about
*where* the framework lives, *how* the axes/baselines are operationalized, and — critically — *how
strongly* the v1 results may be stated, given that the reference model is a deterministic scriptable mock,
not a live LLM.

## Decision

1. **Eval framework is library code; experiments are scripts.** Reusable machinery (failure injection,
   baselines, metrics, ablation, matrix runner) lives in `src/cairn/eval/`; concrete experiments that wire
   a task/model and print results live in `benchmarks/`. This mirrors the Phase 3 split (library in `src/`,
   concrete wiring in `examples/`) and keeps the no-hardcoded-harness rule (ADR-0007): tasks, models,
   failure types, baselines, and ablations are all injected.

2. **Baselines, operationalized.** B0 cold restart = fresh runtime, run from scratch. B1 log-replay =
   re-feed the recorded action log in a fresh runtime, no re-grounding. B2 snapshot-only = restore the
   latest workspace snapshot then continue with a fresh model context, **no `reconcile`, no effect-safety**.
   B3 RGR = `CodeHarness.resume`. A `no_wal` toggle gives the with-/without-WAL contrast for C3.

3. **Metrics, operationalized deterministically.** Solution quality is an **artifact-digest match ratio**
   against the uninterrupted reference run (not an LLM judge in v1); no-regression diffs pre-failure
   completed artifacts against post-recovery; effect-safety counts duplicate/spurious external effects
   against the ledger ground truth and is a **hard gate** (never averaged into a scalar); recovery tax is
   post-failure steps/work. The uninterrupted run is always the yardstick.

4. **Honest-results policy (overriding).** v1 evidence comes from the **deterministic reference harness
   with a scriptable mock model**. Claim-status updates therefore say *supported/evidenced in the reference
   harness* and explicitly flag that a **live-LLM empirical study with statistical testing is future
   work**. Failure types beyond `crash` (context-overflow, tool-timeout, model-error) are **modeled** as a
   typed stop-at-`k` in v1, not faithfully reproduced; this is labeled wherever reported. No claim is
   marked `supported` on the strength of a tautology (e.g. a deterministic mock that cannot diverge does
   not, by itself, establish the non-determinism robustness of C4 — only the *mechanism* is exercised).

## Consequences

- The benchmark is reproducible and fast (deterministic), and the framework is reusable for the future
  live-LLM study behind the same seams.
- Results are credible because their scope is stated plainly; negative/insufficient results are recorded,
  per the claims-registry freeze policy, rather than overclaimed.
- Some axes (solution quality) use proxies in v1; swapping in an LLM judge later requires no framework
  change, only a different injected grader.

## Supersedes / superseded by

None.
