---
id: AP-0023
title: Unified distillation engine (cairn writer)
phase: phase-4-recovery-v1
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: []
related_docs: [docs/design/unified-distillation.md, docs/design/continuation-state-schema.md]
related_adrs: [ADR-0005, ADR-0007]
---

## Objective

Replace the Phase 3 `minimal_distill` stub with a real **unified distillation engine**: one `distill`
that builds a genuine durable core (intent, plan + step status, decisions incl. ruled-out dead-ends, and a
**world digest** of the workspace) and handles the elastic tail two ways — **pruned** for online
compaction, **frozen** for a durable checkpoint. This is the operational core of "Checkpoints Are
Compactions" (claim C2): the same call serves both write paths and produces an identical durable core.

## Scope

**In:** a `distill(goal, history, *, mode, ...) -> ContinuationState` with `mode ∈ {"compact",
"checkpoint"}`; derivation of `plan`/`plan.status` and `decisions` (failed steps → `ruled_out`) from the
trajectory; a `world_digest(workspace_dir)` helper (per-file content hash) populating `world.digest`;
tail policy (compact prunes raw detail, checkpoint freezes the last N steps verbatim).
**Out:** the resume/reconcile logic that *consumes* the digest (AP-0025); LLM-based summarization (the
salience policy stays deterministic/rule-based for v1).

## Deliverables

- `src/cairn/harness/distill.py` — the unified `distill` engine (durable core identical across modes).
- `src/cairn/runtime/digest.py` — `world_digest(dir) -> {relpath: sha256}` (deterministic, order-stable).
- Tests: durable core equality across `compact`/`checkpoint`; tail pruned vs frozen; digest stability.

## Acceptance Criteria

- [x] `distill` produces a schema-valid `ContinuationState` with a real core (intent/plan/decisions/digest)
- [x] Durable core is **identical** for `mode="compact"` and `mode="checkpoint"` on the same trajectory (C2)
- [x] Elastic tail is pruned under `compact` and frozen (last N verbatim) under `checkpoint`
- [x] `world.digest` reflects actual workspace file contents and is stable across calls
- [x] No hardcoded model/task/path (ADR-0007); back-compat shim keeps the agent loop working
- [x] Documentation updated; trackers updated; unit tests pass

## Dependencies

- none (extends existing `cairn.harness.distill` and `cairn.state`)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 4 entry).
- 2026-06-15 — Accepted → Done. Delivered unified `distill(mode=...)` + `runtime/digest.py`; durable-core-equality / tail / digest tests pass.
