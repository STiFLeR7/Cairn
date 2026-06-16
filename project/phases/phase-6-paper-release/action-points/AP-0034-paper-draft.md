---
id: AP-0034
title: Paper draft ("Checkpoints Are Compactions")
phase: phase-6-paper-release
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: []
related_docs: [docs/concepts/problem-formalization.md, docs/concepts/recovery-fidelity.md, docs/design/unified-distillation.md, docs/design/resume-protocol.md, docs/research/claims-registry.md]
related_adrs: [ADR-0005, ADR-0009]
---

## Objective

Synthesize Phases 0–5 into a self-contained research paper draft built around the thesis **"Checkpoints
Are Compactions."** It states the agent-recovery problem, presents the two-layer model + Continuation
State, the Re-grounding Recovery protocol, effect-safety, and unified distillation, then reports the
Phase 5 evaluation with honest scope, limitations, and future work.

## Scope

**In:** `PAPER.md` (Markdown draft) with: abstract, introduction, related work, the two-layer model,
Continuation State, RGR, effect-safety, unified distillation, evaluation (Phase 5 results + the C1–C5
verdicts), limitations/honest scope, future work, references to the in-repo docs.
**Out:** a typeset PDF / venue submission (the Markdown draft is the deliverable; LaTeX/venue formatting is
later); new experiments (it reports existing Phase 5 results).

## Deliverables

- `PAPER.md` — the draft, internally consistent with the claims registry and Phase 5 results.

## Acceptance Criteria

- [x] Covers problem → two-layer model → Continuation State → RGR → effect-safety → unified distillation
- [x] Reports the Phase 5 evaluation (baselines, axes, C1–C5) with the **honest scope** from ADR-0009
- [x] States limitations and future work (live-LLM study, non-crash failure types, B1/B2 in non-determinism)
- [x] Cross-references the in-repo concept/design docs and the claims registry (single source of truth)
- [x] Documentation + trackers updated; tests remain green (no code change expected)

## Dependencies

- none (synthesis of merged Phases 0–5)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 6 entry).
- 2026-06-15 — Accepted → Done. Delivered `PAPER.md` (problem→method→evaluation→limitations, cites in-repo docs, honest scope per ADR-0009).
