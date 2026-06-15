# Phase 3 — Minimal Harness

- **Status:** 🟢 Complete on branch *(2026-06-15 — `pytest` 11 passed; awaiting review + merge)*
- **Goal:** Build the substrate — a minimal, **fully pluggable** Code Harness + Runtime that honors the
  Phase 2 boundary contract — with **no recovery yet**. First runnable code; "tests pass" is now part of
  the Definition of Done.

## Goals

Turn the Phase 2 design into a working, framework-agnostic substrate that Phase 4 will add recovery to:

- **Interfaces first** — the boundary contract + `Sandbox`, `ModelProvider`, `ToolRegistry`, `Task`, and
  the `ContinuationState` data model, all as ABCs / Protocols (`AP-0021`).
- **Minimal Runtime** — local-subprocess sandbox, workspace snapshotting, effect-ledger store, checkpoint
  store — implementing the Runtime side of the contract (`AP-0019`).
- **Minimal Code Harness** — the agent loop and code-as-action executor, driven by an injected
  `ModelProvider` (scriptable mock default) — the Code Harness side (`AP-0020`).
- **Baseline tasks + smoke tests** — at least one end-to-end task the harness completes, plus tests
  asserting the contract behaviors (`AP-0022`).

**Hard constraint (ADR-0007):** *no hardcoded harness.* Model, tools, tasks, storage, sandbox, and
policies are injected — nothing concrete inline.

## Action Points

| ID | Title | Status |
|---|---|---|
| [AP-0021](action-points/AP-0021-boundary-interfaces.md) | Boundary-contract interfaces + core data models | Done |
| [AP-0019](action-points/AP-0019-minimal-runtime.md) | Minimal Runtime (sandbox, workspace, effect ledger, checkpoint store) | Done |
| [AP-0020](action-points/AP-0020-minimal-code-harness.md) | Minimal Code Harness (agent loop, code-as-action, model provider) | Done |
| [AP-0022](action-points/AP-0022-baseline-tasks-tests.md) | Baseline task suite (no recovery) + smoke tests | Done |

## Dependency order

```
AP-0021 (interfaces + data models)
   ├─→ AP-0019 (Runtime implements Runtime-side contract)
   └─→ AP-0020 (Code Harness implements Code-Harness-side contract)
            └─→ AP-0022 (baseline tasks + smoke tests over the assembled harness)
```

## Checklist

- [x] Boundary-contract + Sandbox/ModelProvider/ToolRegistry/Task interfaces + ContinuationState model (AP-0021)
- [x] Minimal Runtime implements snapshot/checkpoint/effect-ledger/sandbox (AP-0019)
- [x] Minimal Code Harness runs the agent loop via injected model provider (AP-0020)
- [x] Baseline task completes end-to-end; smoke tests pass (AP-0022)
- [x] No hardcoded model/tools/tasks/paths anywhere (ADR-0007)

## Completion criteria

- [x] The assembled harness completes at least one baseline task end-to-end
- [x] `pytest` smoke suite passes (contract behaviors + baseline task)
- [x] Everything is injected/configurable — no hardcoded harness (verified)
- [x] Recovery is **not** implemented here (that is Phase 4) — the seams for it exist
- [x] All Phase 3 APs `Done`; ROADMAP and trackers updated
