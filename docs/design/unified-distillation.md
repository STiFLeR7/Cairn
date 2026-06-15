---
title: Unified Distillation (Compaction ≡ Checkpoint)
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0016]
related_adrs: [ADR-0005]
---

# Unified Distillation

The operational core of the thesis **Checkpoints Are Compactions**: a *single* distillation mechanism
produces the [Continuation State](continuation-state-schema.md) for both online context compaction and
durable checkpointing. This is what makes recovery quality a by-product of normal operation. See
[ADR-0005](../adr/ADR-0005-unified-distillation.md).

## 1. One function, two write paths

Both paths call the same Code-Harness operation `distill(trajectory, prev_state) -> ContinuationState`
(from the [boundary contract](boundary-contract.md)). They differ only in what happens to the result.

| | **Compaction write** | **Checkpoint write** |
|---|---|---|
| Trigger | context-window pressure | step boundary / pre-effect / interval |
| Frequency | many times per task | periodic, durable points |
| Durable core | recomputed, kept **in-context** | recomputed, **persisted** |
| Elastic tail | **pruned** (drop raw detail, keep going) | **frozen** (snapshot tail as-is, persist) |
| Persisted? | no (stays live) | yes (`checkpoint(...)`, atomic) |
| Goal | keep going cheaply | reconstruct faithfully after loss |

The same distillation produces the same durable core in both; only the **tail handling** and
**persistence** differ.

## 2. Resolving the core/tail tension

The objection: compaction is aggressively lossy ("keep going"), checkpointing wants faithfulness
("reconstruct from nothing") — won't sharing one mechanism drag checkpoint fidelity down to compaction's
lossiness?

**Resolution — the durable core is the shared invariant; the tail is path-specific.**

- The **durable core** is, by the [schema rule](continuation-state-schema.md), exactly the sufficient
  statistic `S`: precisely what compaction must keep to keep going *and* what a checkpoint needs to
  reconstruct. Both paths preserve it identically.
- The **elastic tail** is where the paths legitimately differ: compaction prunes it (the agent is still
  live and can re-derive detail), a checkpoint freezes it at write time (extra, best-effort context for a
  cold resume).

So a persisted checkpoint = `durable core + frozen tail`; an online compaction = `durable core + pruned
tail`. Same distillation, fidelity-appropriate per path.

## 3. Triggers and the step boundary

- **Compaction:** fires on window-pressure (approaching the context limit).
- **Checkpoint:** fires at a **step boundary** (one complete decide-act cycle — never mid-action), and
  additionally **before any irreversible effect** (so the effect ledger and the cairn stay consistent)
  and on a configurable step/time interval.

Checkpointing only at step boundaries guarantees the cairn never captures a half-executed action.

## 4. What is summarized vs preserved

- **Preserved structurally (core):** intent, plan + step status, decisions + ruled-out dead-ends,
  effect/world pointers, verification, provenance.
- **Summarized into the core:** long raw exploration is distilled into `decisions` (including what was
  ruled out) rather than kept verbatim.
- **Kept verbatim, briefly (tail):** the most recent step detail, prunable.

## 5. Why unification helps recovery (claim C2)

Two consequences, both testable:

1. **No core-fidelity loss from unification.** The durable core is identical across paths and a checkpoint
   *additionally* freezes the tail, so checkpoint fidelity ≥ what the core alone provides. This is the
   testable content of **claim C2** ([claims registry](../research/claims-registry.md)).
2. **Continuous exercise.** Because normal long-horizon operation compacts constantly, the exact
   distillation recovery depends on is *continuously exercised and tuned*. An agent that compacts well
   recovers well — by construction, not by a separate, rarely-used code path.

## Summary

One `distill` function feeds two write paths that share a durable core and differ only in tail handling
(prune vs freeze) and persistence. The core/tail split resolves the compaction-vs-checkpoint tension,
yields claim C2 (no core-fidelity loss), and makes recovery a by-product of everyday compaction.
