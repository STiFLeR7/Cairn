---
id: AP-0031
title: Continuation-State ablation study
phase: phase-5-evaluation
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0030]
related_docs: [docs/concepts/recovery-fidelity.md, docs/design/continuation-state-schema.md, docs/research/claims-registry.md]
related_adrs: [ADR-0009]
---

## Objective

Empirically identify the minimal sufficient Continuation State by **ablating** cairn components (drop
ruled-out dead-ends, drop decisions, drop plan, drop world digest) and measuring where recovery fidelity
collapses. Turns "what must be checkpointed?" from assertion into measurement (claims **C5**, and the
unified-vs-checkpoint-only contrast for **C2**).

## Scope

**In:** an ablation that transforms a cairn by removing a named component; an experiment that resumes from
each ablated cairn and reports fidelity per ablation; the unified-vs-checkpoint-only comparison for C2.
**Out:** exhaustive component-subset search (v1 ablates the headline components one at a time).

## Deliverables

- `src/cairn/eval/ablation.py` — `ablate(state, drop=...)` + an ablation experiment over the axes.
- `benchmarks/ablation_study.py` — runnable study printing the fidelity-by-ablation table.
- Tests: ablating the component a scenario depends on degrades resume; ablating slack does not.

## Acceptance Criteria

- [x] Ablation can drop each headline cairn component independently
- [x] At least one ablation demonstrably degrades recovery (a fidelity cliff) and one does not (slack)
- [x] Unified distillation scores no worse than a checkpoint-only cairn on the same scenario (C2 evidence)
- [x] Honest scope: deterministic reference harness, not a live-LLM study (ADR-0009)
- [x] Documentation + trackers updated; unit tests pass

## Dependencies

- AP-0030 (metrics to measure fidelity per ablation)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 5 entry).
- 2026-06-15 — Accepted → Done. Delivered `eval/ablation.py` + `benchmarks/ablation_study.py`; C5 cliff (plan) located; tests pass.
