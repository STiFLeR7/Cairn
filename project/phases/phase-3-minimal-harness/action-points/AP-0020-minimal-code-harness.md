---
id: AP-0020
title: Minimal Code Harness (agent loop, code-as-action, model provider)
phase: phase-3-minimal-harness
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0021]
related_docs: [docs/design/boundary-contract.md, docs/concepts/code-harness-and-runtime.md]
related_adrs: [ADR-0007]
---

## Objective

Implement the Code Harness side: the agent loop (observe → decide → act → observe) where actions are
**code** executed via the Runtime sandbox, driven by an injected `ModelProvider`. Provide the default
`ScriptableMockModel` for deterministic runs. No recovery yet, but the `distill` seam exists (a basic
pass-through is acceptable for Phase 3).

## Scope

**In:** `CodeHarness` loop consuming a `ModelProvider`, `ToolRegistry`, and `Runtime`; a code-as-action
executor that runs model-emitted code in the sandbox and feeds back observations; `ScriptableMockModel`
(deterministic, step-scripted) as the default provider; a minimal `distill` (builds a ContinuationState
from the run — full distillation policy is Phase 4). Everything injected.
**Out:** re-grounding/reconcile (Phase 4); real LLM adapters (later plugins).

## Deliverables

- `src/cairn/harness/agent_loop.py`, `src/cairn/harness/code_action.py`,
  `src/cairn/harness/distill.py` (minimal), `src/cairn/model_mock.py` (`ScriptableMockModel`).

## Acceptance Criteria

- [x] The agent loop runs to task completion using an injected model provider + tool registry + runtime
- [x] Actions are code executed via the Runtime sandbox; observations feed back into the loop
- [x] `ScriptableMockModel` enables deterministic end-to-end runs
- [x] A minimal `distill` produces a schema-valid `ContinuationState` (seam for Phase 4)
- [x] No hardcoded model/tools/tasks (all injected) (ADR-0007)
- [x] Documentation updated; trackers updated; loop unit test passes

## Dependencies

- AP-0021 (interfaces)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 3 entry).
- 2026-06-15 — Accepted → Done. Delivered `cairn.harness` (agent loop, code-as-action, minimal
  distill) + `cairn.model_mock.ScriptableMockModel`. Agent-loop test passes.
