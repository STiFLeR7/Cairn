---
title: Related Work & Positioning
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0009]
related_adrs: [ADR-0001]
---

# Related Work & Positioning

Recovery is old; agent recovery is the gap. This document surveys the prior art Cairn builds on and
positions Cairn honestly against it. The thesis to defend: existing systems each solve a *slice* of the
problem, but none handle crash-recovery **and** non-determinism **and** effect-safety **and** context-loss
*together*, and none frame recovery as outcome-fidelity-bounded re-grounding with the compaction≡checkpoint
unification.

> Citations below are to families of systems / canonical references; a full bibliography is assembled in
> Phase 6 (`AP-0034`). This survey establishes positioning, not an exhaustive literature review.

## 1. Classical systems recovery

- **Process / HPC checkpoint-restart** — CRIU, DMTCP, BLCR. Snapshot a process's full memory image and
  restore it. Faithful for deterministic processes; assumes serializable, bounded state. Blind to
  *meaning*: restoring an LLM context's bytes is not restoring its understanding.
- **Database recovery** — ARIES, write-ahead logging. Durability and crash-consistency via WAL + redo/undo
  around transaction boundaries. Cairn borrows the **write-ahead** idea for effects, but agents have no
  clean transaction boundary and effects are external, not undoable.
- **Event sourcing** — reconstruct state by replaying an event log. Depends on deterministic application
  of events — unavailable for LLM steps.

## 2. Durable execution

- **Temporal / durable functions** — the closest industrial analogue: workflows survive crashes by
  recording activity results and **replaying** deterministic workflow code to rebuild state. Powerful, but
  rests on two assumptions agents break: activities are **idempotent**, and workflow logic is
  **deterministic** so replay reproduces state. Agent steps are neither.

## 3. Agent-framework persistence

- **LangGraph checkpointers** — persist graph/node state between steps; enable resuming a graph run.
  Mechanism-level persistence that largely assumes deterministic, structured transitions; it does not
  address semantic re-grounding after context loss, non-deterministic divergence, or effect-safety as a
  measured property.
- **OpenHands (and similar SWE agents)** — maintain workspace and some session state; recovery is
  workspace-centric and ad hoc rather than a defined contract with a fidelity metric.

## 4. Virtual context management

- **MemGPT / Letta** — manage a context window that exceeds the model's limit by paging salient state in
  and out — i.e. they *already* recover from context loss during normal operation. This is strong evidence
  for the *Checkpoints Are Compactions* thesis, but the work targets continuous memory management, not
  crash recovery, effect-safety, or rollback to a durable checkpoint.

## 5. Positioning matrix

Columns are the four capabilities that must hold *together* for robust agent recovery, plus whether the
approach defines a recovery-quality metric.

| Approach | Crash recovery | Handles non-determinism | Effect-safety | Context-loss recovery | Fidelity metric |
|---|:--:|:--:|:--:|:--:|:--:|
| CRIU / DMTCP (process) | ✅ | ⚠️ replay-free snapshot | ❌ | ❌ (restores bytes, not meaning) | ❌ |
| ARIES / WAL (DB) | ✅ | ✅ (deterministic) | ⚠️ within-DB only | ❌ | ❌ |
| Event sourcing | ✅ | ❌ (needs determinism) | ⚠️ | ❌ | ❌ |
| Temporal (durable exec) | ✅ | ❌ (assumes determinism) | ⚠️ idempotent activities | ❌ | ❌ |
| LangGraph checkpointers | ✅ | ❌ | ❌ | ⚠️ structural only | ❌ |
| OpenHands state | ⚠️ workspace-centric | ❌ | ❌ | ⚠️ | ❌ |
| MemGPT / Letta | ❌ | n/a | ❌ | ✅ | ❌ |
| **Cairn (RGR)** | ✅ | ✅ (re-grounding, not replay) | ✅ (WAL + tool taxonomy) | ✅ (unified w/ compaction) | ✅ |

Legend: ✅ addressed · ⚠️ partial / assumption-bound · ❌ not addressed.

## 6. Novelty statement (honest)

What is **not** novel: checkpoint/restore mechanics (CRIU, snapshots), write-ahead logging (ARIES),
durable replay (Temporal, event sourcing), structural agent-state persistence (LangGraph), and context
paging (MemGPT) all predate Cairn and are credited.

What **is** novel in combination:

1. **Re-grounding instead of replay** — treating recovery as re-establishing situational awareness from a
   distilled sufficient state under non-determinism, rather than reproducing a trajectory.
2. **Compaction ≡ checkpoint** — one distillation mechanism (durable core + elastic tail) serving both
   context compaction and crash recovery, so the path recovery depends on is exercised continuously.
3. **Effect-safety as a measured, taxonomized guarantee** — a WAL plus a tool-reversibility taxonomy, with
   duplicated-effects counted as a first-class fidelity axis.
4. **A recovery-fidelity metric** — outcome-equivalence measurement that also enables a sufficiency
   ablation.

No surveyed system delivers (1)–(4) together. That intersection is Cairn's white space. This survey is
referenced by [`../vision/positioning.md`](../vision/positioning.md).
