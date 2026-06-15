---
id: AP-0019
title: Minimal Runtime (sandbox, workspace, effect ledger, checkpoint store)
phase: phase-3-minimal-harness
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0021]
related_docs: [docs/design/boundary-contract.md]
related_adrs: [ADR-0003, ADR-0007]
---

## Objective

Implement the Runtime side of the boundary contract: a local-subprocess `Sandbox`, workspace
snapshot/restore, the append-only effect ledger, and an atomic checkpoint store — upholding invariants
I1–I5. No recovery orchestration yet (that is Phase 4); just the durable mechanism.

## Scope

**In:** `LocalSubprocessSandbox` (the default `Sandbox` impl); `snapshot_workspace` / `restore_workspace`
(copy-tree snapshots); append-only `EffectLedger` (`append_effect`/`complete_effect`/`list_effects_since`,
monotonic offsets — I3); atomic `CheckpointStore` (`checkpoint`/`load_latest`, write-temp-then-rename for
atomicity — I2); a `LocalRuntime` wiring them to the `Runtime` protocol.
**Out:** the resume protocol (Phase 4); non-local sandboxes (later plugins).

## Deliverables

- `src/cairn/runtime/sandbox_local.py`, `src/cairn/runtime/workspace.py`,
  `src/cairn/runtime/effect_ledger.py`, `src/cairn/runtime/checkpoint_store.py`,
  `src/cairn/runtime/local_runtime.py`.

## Acceptance Criteria

- [x] `LocalRuntime` implements every Runtime-side contract operation
- [x] Effect ledger is append-only with monotonic offsets (I3); write-ahead supported (I1)
- [x] Checkpoints are atomic — `load_latest` never returns a partial cairn (I2)
- [x] Sandbox runs commands via the pluggable interface (local subprocess default)
- [x] No hardcoded paths/model/tools (paths come from config/injection) (ADR-0007)
- [x] Documentation updated; trackers updated; unit tests for ledger + checkpoint atomicity pass

## Dependencies

- AP-0021 (interfaces)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 3 entry).
- 2026-06-15 — Accepted → Done. Delivered `cairn.runtime` (local sandbox, workspace, append-only
  effect ledger, atomic checkpoint store, LocalRuntime). Ledger + checkpoint-atomicity tests pass.
