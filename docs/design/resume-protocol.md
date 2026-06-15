---
title: Re-grounding Resume Protocol (RGR)
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0015]
related_adrs: [ADR-0004]
---

# Re-grounding Resume Protocol (RGR)

How the agent resumes after a failure. RGR **re-grounds** — re-establishes situational awareness from the
[Continuation State](continuation-state-schema.md) and the re-observed world — rather than **replaying**
the trajectory (impossible under non-determinism). See
[ADR-0004](../adr/ADR-0004-regrounding-not-replay.md). It uses the
[boundary contract](boundary-contract.md) and the [effect-safety protocol](effect-safety-protocol.md).

## The five steps

```
   FAILURE F@k
       │
   ┌───▼──────────────────────────────────────────────── 1. LOAD (Runtime) ──┐
   │ (state, snap, offset) = load_latest()        # I5: latest durable        │
   │ restore_workspace(snap)                                                   │
   │ effects = list_effects_since(offset)                                      │
   └───┬──────────────────────────────────────────────────────────────────────┘
   ┌───▼──────────────────────────────────────── 2. RE-OBSERVE (Code Harness) ┐
   │ read the ACTUAL world: workspace files, the effect ledger.               │
   │ "Re-observe before re-act."                                              │
   └───┬──────────────────────────────────────────────────────────────────────┘
   ┌───▼──────────────────────────────────────── 3. RECONCILE (Code Harness) ─┐
   │ compare cairn vs reality; resolve the torn step (last checkpoint→failure):│
   │   • world.digest mismatch  → a file was mid-written → repair/redo step    │
   │   • INTENT-without-COMPLETE → effect danger window → effect-safety policy  │
   │   • plan.status vs world    → mark steps actually done/undone             │
   └───┬──────────────────────────────────────────────────────────────────────┘
   ┌───▼──────────────────────────────────────────── 4. RE-PLAN (Code Harness)┐
   │ from intent + reconciled plan + decisions(+dead-ends), choose next action.│
   │ A DIFFERENT but valid path is acceptable (outcome equivalence, not replay)│
   └───┬──────────────────────────────────────────────────────────────────────┘
   ┌───▼─────────────────────────────────────────────── 5. CONTINUE ──────────┐
   │ resume directing the Runtime; checkpoint again at the next step boundary. │
   └──────────────────────────────────────────────────────────────────────────┘
```

## Step detail

### 1. Load *(Runtime mechanism)*
`load_latest()` returns the most recent fully-durable checkpoint (invariant I5); the workspace is
restored to its `snap_id`; effects since the checkpoint offset are fetched for reconciliation.

### 2. Re-observe *(the rule)*
The agent's **first act is to look, not to act.** It reads the real workspace and the effect ledger
before deciding anything. This is what separates RGR from "restore bytes and charge ahead."

### 3. Reconcile — the torn step
The dangerous window is between the last checkpoint and the failure. Three divergences are detected:

- **Torn writes** — a `world.digest` entry no longer matches the file → that file's step is redone or
  repaired.
- **Effect danger window** — `INTENT`-without-`COMPLETE` keys → handed to the
  [effect-safety protocol](effect-safety-protocol.md) (redo / verify-then-redo-or-skip / escalate by tool
  class). This is where effect-safety (claim C3) is enforced on resume.
- **Plan drift** — `plan.status` is reconciled against what the world shows actually completed.

> **v1 implementation note (restore-first).** The reference harness performs step 1 (LOAD, including
> `restore_workspace`) *before* step 3 (RECONCILE). The restored workspace therefore matches the cairn's
> `world.digest` by construction, so the **torn-write / plan-drift detection above is a no-op in the v1
> flow** — a post-checkpoint divergence is discarded by the restore and the step is redone from the clean
> checkpoint (outcome equivalence). The detection is implemented and unit-tested but reserved for a future
> restore-less *crash-in-place* mode. In v1, reconcile's active jobs are the **effect danger window** and
> **plan re-grounding**. See [ADR-0008](../adr/ADR-0008-recovery-v1-implementation.md) §7.

### 4. Re-plan *(non-determinism is a feature here)*
With intent, the reconciled plan, and the decision ledger (including ruled-out dead-ends, so failed paths
aren't re-explored), the agent produces the next action. It need not match the original trajectory — the
bar is **outcome equivalence** ([recovery-fidelity.md](../concepts/recovery-fidelity.md)).

### 5. Continue
Normal operation resumes, including re-establishing any runtime handles (taxonomy layer 5) and
checkpointing again at the next step boundary.

## Cross-version resume (claim C4)

Because RGR re-derives from intent and the observed world rather than reproducing tokens, the model that
resumes may differ from the one that checkpointed. `provenance` records both versions; re-grounding
remains valid where log-replay (which depends on the original model's exact behavior) would not.

## Summary

RGR resumes by **load → re-observe → reconcile (torn-step) → re-plan → continue**. Reconciliation detects
torn writes, the effect danger window (delegated to the effect-safety protocol), and plan drift;
re-planning may take a new valid path because the bar is outcome equivalence. This is recovery as
re-grounding, not replay.
