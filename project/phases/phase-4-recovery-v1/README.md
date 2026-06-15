# Phase 4 — Recovery v1 (three pillars)

- **Status:** 🟢 Complete & merged *(2026-06-15 — PR #4, merge commit `b008a4f`; `pytest` 33 passed)*
- **Goal:** Turn the Phase 3 substrate into a **recoverable** agent. Implement the three recovery
  pillars defined in Phase 2 — **unified distillation**, **re-grounding resume (RGR)**, and
  **effect-safety** — and prove them with an **end-to-end recovery from an injected failure**.

## Goals

Phase 3 built the durable mechanism (snapshot, atomic checkpoint, append-only effect ledger) but wrote
only a *minimal* cairn and never resumed from one. Phase 4 makes recovery real:

- **Unified distillation** (`AP-0023`) — one `distill` that produces a real durable core (intent, plan +
  status, decisions incl. ruled-out, **world digest**) and handles the tail two ways (prune for
  compaction, freeze for checkpoint). Implements ADR-0005 / claim **C2**.
- **Checkpoint ↔ snapshot integration** (`AP-0024`) — make checkpoint + snapshot survive a *process
  restart*. Fixes the snapshot-numbering watch-item (snapshot ids must continue-from-highest, like
  checkpoints, so a resumed runtime never overwrites a referenced snapshot — invariant I4).
- **Re-grounding resume** (`AP-0025`) — implement `reconcile` + `CodeHarness.resume`: load → re-observe →
  reconcile (torn writes, plan drift, effect danger window) → re-plan → continue. Implements ADR-0004.
- **Effect-safety WAL** (`AP-0026`) — write-ahead `perform_effect` + resume-time danger-window resolution
  keyed to tool class (redo / verify-then-redo-or-skip / escalate). Implements ADR-0006 / claim **C3**.
- **End-to-end recovery** (`AP-0027`) — inject a failure mid-run, resume in a fresh runtime, and show the
  task completes with **no duplicate effect** and a measured **recovery tax**.

**Hard constraint (ADR-0007):** *no hardcoded harness.* Tool classes/verify hooks, failure points, model,
and storage stay injected — the recovery logic must not assume a concrete task, tool, or model.

## Action Points

| ID | Title | Status |
|---|---|---|
| [AP-0023](action-points/AP-0023-unified-distillation-engine.md) | Unified distillation engine (cairn writer) | Done |
| [AP-0024](action-points/AP-0024-checkpoint-snapshot-integration.md) | Checkpoint persistence + workspace snapshot integration | Done |
| [AP-0025](action-points/AP-0025-regrounding-resume.md) | Re-grounding resume protocol implementation | Done |
| [AP-0026](action-points/AP-0026-effect-safety-wal.md) | Effect-safety WAL + idempotency enforcement | Done |
| [AP-0027](action-points/AP-0027-end-to-end-recovery.md) | End-to-end recovery from injected failure | Done |

## Dependency order

```
AP-0023 (distill: real core + world digest)
   └─→ AP-0024 (checkpoint/snapshot survive restart; numbering fix)
          └─→ AP-0025 (reconcile + resume use the restored cairn + digest)
                 ├─→ AP-0026 (effect-safety resolves the danger window during reconcile)
                 └─→ AP-0027 (inject failure → resume → outcome equivalence, no dup effect)
```

## Checklist

- [x] `distill(goal, history, mode=compact|checkpoint)` builds a real core (intent/plan/decisions/digest); tail pruned vs frozen (AP-0023)
- [x] Snapshot ids continue-from-highest; checkpoint references a restorable snapshot after a fresh-runtime restart (AP-0024)
- [x] `reconcile` + `CodeHarness.resume` re-ground and finish the task after a crash (AP-0025)
- [x] Write-ahead `perform_effect`; danger-window resolution per tool class; no duplicate `check-before-retry` effect (AP-0026)
- [x] End-to-end injected-failure recovery test: task completes, no duplicate effect, recovery tax recorded (AP-0027)
- [x] No hardcoded harness anywhere (ADR-0007); docs + ADR-0008 + trackers updated

## Completion criteria

- [x] An agent recovers from an **injected failure** end-to-end and completes the task (claim **C1** harness exists)
- [x] Unified `distill` yields an identical durable core for compaction and checkpoint paths (claim **C2**)
- [x] No duplicate effect for `safe-to-retry` / `check-before-retry`; `never-retry` escalates (claim **C3**)
- [x] `pytest` green across the new recovery suite **and** the existing Phase 3 tests
- [x] All Phase 4 APs `Done`; ROADMAP, trackers, CHANGELOG, and design/ADR docs updated
