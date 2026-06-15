---
id: AP-0024
title: Checkpoint persistence + workspace snapshot integration
phase: phase-4-recovery-v1
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0023]
related_docs: [docs/design/boundary-contract.md]
related_adrs: [ADR-0003, ADR-0008]
---

## Objective

Make a checkpoint and its workspace snapshot survive a **process restart**, so a freshly-constructed
runtime (the resume case) can `load_latest()` and `restore_workspace()` correctly. This fixes the
**snapshot-numbering watch-item** logged in Phase 3: `WorkspaceManager` numbers snapshots from `0` on each
construction, while `CheckpointStore` continues-from-highest — so a resumed runtime would mint `snap_0`
again and **overwrite** the snapshot an existing checkpoint references, violating invariant **I4** (mutual
consistency). Snapshot numbering must continue-from-highest, exactly like checkpoints.

## Scope

**In:** make `WorkspaceManager` scan existing `snap_N` dirs and continue numbering from the highest
(survives reconstruction); verify checkpoint→snapshot→effect-offset stay mutually consistent across a
simulated restart (new `LocalRuntime` over the same `base_dir`); integrate the AP-0023 world digest into
the checkpoint write so a checkpoint records the digest of the snapshotted workspace.
**Out:** snapshot GC / retention policy (later); non-local snapshot backends (plugins).

## Deliverables

- `src/cairn/runtime/workspace.py` — continue-from-highest snapshot numbering.
- Checkpoint path records the world digest at snapshot time (via AP-0023 distill in checkpoint mode).
- Tests: fresh-runtime restart does not collide/overwrite snapshots; `load_latest` after restart returns a
  checkpoint whose `snap_id` is restorable and whose digest matches the restored workspace.

## Acceptance Criteria

- [x] `WorkspaceManager` continues snapshot numbering from the highest existing `snap_N` (no reset to 0)
- [x] A new `LocalRuntime` over an existing `base_dir` neither overwrites nor loses prior snapshots (I4)
- [x] `load_latest()` after restart returns `(state, snap, offset)` with a restorable snapshot
- [x] Restored workspace matches the checkpoint's recorded `world.digest`
- [x] No hardcoded paths (ADR-0007); documentation + ADR-0008 updated; tests pass

## Dependencies

- AP-0023 (digest used in the checkpoint write)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 4 entry). Carries the Phase 3 snapshot-numbering
  watch-item as its primary fix.
- 2026-06-15 — Accepted → Done. Fixed `WorkspaceManager` continue-from-highest numbering; restart-survival tests pass (I4 holds across reconstruction).
