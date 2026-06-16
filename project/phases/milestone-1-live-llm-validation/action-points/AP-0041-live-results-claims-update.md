---
id: AP-0041
title: Live results analysis & claims update (C1–C5)
phase: milestone-1-live-llm-validation
status: Done
owner: maintainers
created: 2026-06-16
updated: 2026-06-16
depends_on: [AP-0040]
related_docs: [docs/research/claims-registry.md, PAPER.md, docs/adr/ADR-0009-evaluation-framework.md]
related_adrs: [ADR-0009]
---

## Objective

Analyze the live study results and update the claims registry with dated, **live-LLM-scoped** evidence for
C1–C5 — distinct from the existing reference-harness notes. This is where the milestone's honesty discipline
is enforced: a claim that holds live is marked `supported (live)`, one that weakens is `refined`, one that
fails is `refuted`. Negative or insufficient results are recorded, not buried (ADR-0009).

## Scope

**In:** aggregating/summarizing the AP-0040 results (with whatever simple statistics the repetition count
supports); a per-claim verdict for C1–C5 under the live model, each with a dated registry log line scoped
"live-LLM study"; updating `PAPER.md`'s evaluation/limitations sections to report the live results alongside
the reference-harness results; noting which reference-harness conclusions held vs shifted.
**Out:** the v1.0 go/no-go decision (AP-0042, which reads this analysis); re-running the study (AP-0040);
registering *new* claims unless the live evidence demands one (allowed, per the registry's freeze policy:
supersede, don't edit).

## Acceptance Criteria

- [x] The claims registry carries a dated **live-LLM** note (2026-06-16): pipeline validated; **C1 not
      validated live (invalid/insufficient evidence)**; C1–C5 remain reference-harness-only — kept distinct
      from the reference-harness notes
- [x] Live results summarized **honestly**, including the negative result (batched action → crash never
      fired → metrics ill-defined and unstable across repetitions) and the two bugs it exposed/fixed
- [x] `PAPER.md` §9 reports the live finding alongside the reference-harness results, scope preserved
- [x] Freeze policy respected — no claim *statement* was edited; only dated status evidence was appended
- [x] Docs + trackers updated; **76 tests green**

## Dependencies

- `AP-0040` (live study results)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M1 entry).
- 2026-06-16 — Accepted → Done. Recorded the live finding in the claims registry (dated live-LLM log entry)
  and `PAPER.md` §9. Verdict: the live pipeline works, but **C1–C5 stay reference-harness-only** — the live
  run's evidence is invalid under the current task/metrics (the model batches the task into one action, so
  the injected crash never interrupts partial work). The concrete next step is a **non-batchable sequential
  task + action-granularity-robust metrics + repetitions**. No claim statement changed (registry freeze).
