---
id: AP-0041
title: Live results analysis & claims update (C1–C5)
phase: milestone-1-live-llm-validation
status: Accepted
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

- [ ] C1–C5 each carry a dated **live-LLM** status note in the claims registry (supporting, refining, or
      refuting), kept separate from the reference-harness notes
- [ ] Live results for the matrix, ablation, and cross-version experiments are summarized honestly,
      including negatives/insufficient evidence
- [ ] `PAPER.md` reports the live results alongside the reference-harness results, with scope preserved
- [ ] The registry's freeze policy is respected (statements immutable; supersede to change a statement)
- [ ] Docs + trackers updated; tests green

## Dependencies

- `AP-0040` (live study results)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M1 entry).
