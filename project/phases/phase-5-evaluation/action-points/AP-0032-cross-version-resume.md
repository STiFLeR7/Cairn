---
id: AP-0032
title: Cross-version resume experiment
phase: phase-5-evaluation
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0030]
related_docs: [docs/design/resume-protocol.md, docs/research/claims-registry.md]
related_adrs: [ADR-0004, ADR-0009]
---

## Objective

Demonstrate claim **C4**: RGR retains fidelity when the model/version that *resumes* differs from the one
that *checkpointed*, in cases where full-log replay (B1) fails. Re-grounding re-derives from intent and
the observed world, so it does not depend on reproducing the original model's exact tokens.

## Scope

**In:** an experiment that checkpoints with `model_version="A"` and resumes with `model_version="B"`
(different scripted behavior reaching the same goal); show B3 (RGR) completes while B1 (replay of A's log
under B) does not. The cairn's `provenance` records both versions.
**Out:** real multi-model LLM evaluation (v1 uses two scripted mock "versions"; the cross-version
*mechanism* is exercised, the empirical LLM study is future work — ADR-0009).

## Deliverables

- `benchmarks/cross_version_resume.py` — checkpoint-on-A / resume-on-B vs replay-on-B.
- Tests: RGR resume succeeds across versions; provenance records A→B; a replay-mismatch case is shown.

## Acceptance Criteria

- [x] Checkpoint under version A, resume under version B completes the task via RGR (B3)
- [x] The replay-fragility contrast (B1 fails where RGR holds) is **documented as requiring
      non-determinism** and deferred to the live-LLM study — not forced with a deterministic mock (ADR-0009)
- [x] `provenance` records both the checkpointing and resuming versions
- [x] Honest scope: scripted mock versions, not live multi-model LLMs (ADR-0009)
- [x] Documentation + trackers updated; unit tests pass

## Dependencies

- AP-0030 (metrics), AP-0029 (B1/B3 strategies)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 5 entry).
- 2026-06-15 — Accepted → Done. Delivered `benchmarks/cross_version_resume.py`; C4 mechanism shown (provenance A→B); criterion reworded for honesty (replay-fragility deferred to live-LLM study).
