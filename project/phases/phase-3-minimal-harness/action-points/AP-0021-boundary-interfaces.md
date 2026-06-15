---
id: AP-0021
title: Boundary-contract interfaces + core data models
phase: phase-3-minimal-harness
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0013, AP-0014]
related_docs: [docs/design/boundary-contract.md, docs/design/continuation-state-schema.md]
related_adrs: [ADR-0003, ADR-0007]
---

## Objective

Define, in code, the interfaces the rest of the harness programs against: the boundary-contract
operations split into a `Runtime` and `CodeHarness` protocol, plus the `Sandbox`, `ModelProvider`,
`ToolRegistry`, and `Task` interfaces, and the `ContinuationState` data model. Interfaces only — concrete
implementations are AP-0019/0020.

## Scope

**In:** `cairn.contract` (Runtime + CodeHarness protocols, invariants documented); `cairn.state`
(ContinuationState dataclasses matching the schema: durable core + elastic tail); `cairn.sandbox.Sandbox`,
`cairn.model.ModelProvider`, `cairn.tools.ToolRegistry`/`Tool`, `cairn.task.Task` as ABCs/Protocols.
Everything injectable — no concrete bindings.
**Out:** implementations (AP-0019/0020); recovery logic (Phase 4).

## Deliverables

- `pyproject.toml` (package `cairn`, pytest config).
- `src/cairn/state.py` — `ContinuationState`, `DurableCore`, `ElasticTail`, sub-models + (de)serialize.
- `src/cairn/contract.py` — `Runtime` and `CodeHarness` Protocols with the AP-0014 operations + invariant docstrings.
- `src/cairn/sandbox.py`, `src/cairn/model.py`, `src/cairn/tools.py`, `src/cairn/task.py` — the pluggable interfaces.

## Acceptance Criteria

- [x] All boundary-contract operations appear as typed methods on `Runtime` / `CodeHarness`
- [x] `ContinuationState` mirrors the schema (durable core + elastic tail) and round-trips to/from dict/JSON
- [x] `Sandbox`, `ModelProvider`, `ToolRegistry`, `Task` are abstract/Protocol — no concrete logic
- [x] No hardcoded model/tool/task/path (ADR-0007)
- [x] Documentation updated; trackers updated

## Dependencies

- AP-0013 (schema), AP-0014 (contract)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 3 entry).
- 2026-06-15 — Accepted → Done. Delivered `cairn.state`, `cairn.contract`, `cairn.sandbox`,
  `cairn.model`, `cairn.tools`, `cairn.task` + `pyproject.toml`. State round-trip test passes.
