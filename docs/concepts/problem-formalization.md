---
title: The Agent-Recovery Problem (Formalization)
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0007]
related_adrs: [ADR-0001]
---

# The Agent-Recovery Problem

This document states the problem Cairn addresses precisely enough to build on. It defines the failure
model, shows why classical checkpoint/restart does not transfer to agents, and introduces
**continuation sufficiency** — the formal object the rest of the project optimizes.

## 1. Definitions

We model a long-horizon agent as producing a **trajectory** — a sequence of steps that transform state
over time.

- **Step** `kₜ` — one decision-and-action cycle: the agent observes, reasons, and acts (in a Code
  Harness, by emitting and executing code). Steps are the natural granularity at which progress is made
  and at which failure interrupts.
- **World state** `W` — everything outside the model that the agent's actions have changed: workspace
  files, databases, version control, process state.
- **Working state** `M` — everything *inside the agent's context* that is not in `W`: the active
  sub-goal, the reasoning so far, current hypotheses, ruled-out approaches, what has been verified.
  `M` is large, lossy, and not produced by a serializer — it is the live content of the model's context.
- **Effects** `E` — the subset of actions that changed the world *irreversibly or externally*: a sent
  email, a posted message, an opened PR, a payment. Effects are a part of `W`'s history that cannot be
  undone by restoring files.
- **Failure** `F@k` — an interruption at step `k`: a process crash, an out-of-memory kill, a tool
  timeout, a context-window overflow, or a model error. After `F@k`, `M` is gone; `W` is whatever it was
  at the moment of failure (possibly mid-write); `E` is whatever had fired.

**Recovery** is the task of resuming productive work after `F@k` without restarting from `k₀`.

## 2. Why classical recovery does not transfer

Classical checkpoint/restart is a solved problem — for traditional systems. CRIU and VM snapshots,
HPC checkpoint-restart (DMTCP/BLCR), database write-ahead logging and ARIES, event sourcing, and
durable-execution engines (e.g. Temporal) all perform checkpoint → failure → resume reliably. Each
relies on **three assumptions**. Agents violate all three.

### Assumption 1 — State is fully serializable and bounded

*Classical:* a process's state can be captured to bytes and restored faithfully.

*Agents violate it:* the decisive state is `M`, the model's working context. You can serialize the
*bytes* of a context window, but not the *understanding* — and even the bytes are a poor target: they
are huge, mostly redundant, and re-loading them is not the same as having reasoned to them.

> **Example.** An agent has spent 40 steps narrowing a bug to a race condition in one module and has
> ruled out three other hypotheses. The fact that *matters* for continuation is the conclusion and the
> ruled-out set — a few hundred tokens — buried in tens of thousands of tokens of exploration. Restoring
> the raw bytes restores the noise; it does not isolate the signal.

### Assumption 2 — Replay is deterministic

*Classical:* given a checkpoint and the log of inputs since, replaying reproduces the exact state. This
is the workhorse of WAL, event sourcing, and durable execution.

*Agents violate it:* LLM execution is non-deterministic (sampling, model/version drift, inference
nondeterminism). Re-feeding the same prompts does **not** reproduce the same trajectory. Deterministic
replay — the single most common recovery technique — is structurally unavailable.

> **Example.** Re-running the agent from a checkpoint with identical context yields a *different* next
> action than the original run took. Any recovery scheme that assumes "replay the log to rebuild state"
> rebuilds a *different* state, not the lost one.

### Assumption 3 — The resume point is well-defined (transactional)

*Classical:* state advances through clean commit boundaries; you resume at the last committed
transaction.

*Agents violate it:* "step 47" is not a transaction boundary. A step may have half-written a file, and —
worse — may have fired an irreversible **effect** (`E`) that no rollback can retract and that must not be
repeated on resume.

> **Example.** The agent crashes immediately after calling `send_email(...)` but before recording that
> it did. A naive resume re-issues the email. The world, unlike the workspace, has no undo.

## 3. Continuation sufficiency

Because faithful restoration of `M` is impossible and replay is unavailable, recovery cannot mean
"reproduce the lost state." It must mean "**reconstruct enough to continue equivalently.**" We make this
precise.

> **Continuation equivalence.** Two agent states are *continuation-equivalent* for a task if an agent
> resumed from either completes the task with equivalent **outcome** — same success, comparable solution
> quality, no regression of completed work, no duplicated effects. (Outcome, not trajectory: the paths
> may differ.)

> **Continuation sufficiency.** A reconstructed state `S` is *sufficient* if an agent resumed from `S`
> is continuation-equivalent to the uninterrupted agent. The **recovery problem** is to find a minimal
> such `S`:
>
> ```
> minimize  |S|
> subject to  resume(S)  ≈_outcome  uninterrupted-run
> ```

`S` is a **sufficient statistic for continuation** — the smallest summary of the past that loses nothing
relevant to the future. Two consequences follow immediately:

1. **Checkpointing is compression.** Producing `S` is lossy compression of the trajectory under a
   continuation-fidelity constraint — not a memory dump. This is the seed of the project thesis,
   *Checkpoints Are Compactions*: the same operation that compresses an overflowing context to keep
   going is the operation that produces a recovery checkpoint.
2. **Fidelity is the constraint, not an afterthought.** "Equivalent outcome" must be *measured*, which is
   why recovery fidelity (see [recovery-fidelity.md](recovery-fidelity.md)) is defined alongside the
   problem rather than after the solution.

## 4. What `S` must span (forward reference)

Sufficiency ranges over more than `M`. The crash leaves `W`, `E`, and runtime handles in states that
must be reconciled too. The decomposition of agent state into recoverability classes — and which layer
owns each — is the [state taxonomy](state-taxonomy.md); the classification of effects for safe resume is
the [tool effect taxonomy](tool-effect-taxonomy.md). Both are developed under `AP-0012`.

## 5. Open questions routed to later phases

This formalization deliberately stops at *what* recovery requires. The *how* is downstream:

| Question | Routed to |
|---|---|
| What concrete fields constitute `S`? (the Continuation State schema) | Phase 2 · `AP-0013` |
| At what granularity / step boundary is `S` written? | Phase 2 · `AP-0016` |
| How is `S` produced — the distillation policy that does the compression? | Phase 2 · `AP-0016` |
| How are unrecorded effects detected and made safe on resume? | Phase 2 · `AP-0017` |
| How is continuation equivalence measured in practice? | Phase 1 · `AP-0008`; Phase 5 |
| Which layer provides which guarantee? | [recovery-in-the-two-layer-model.md](recovery-in-the-two-layer-model.md) · `AP-0010` |

## Summary

Agent recovery is not classical checkpoint/restart because the decisive state is non-serializable (`M`),
execution is non-deterministic (no replay), and effects are non-transactional (`E`). Recovery is
therefore reframed as finding a **minimal sufficient state for continuation** under an **outcome-fidelity
constraint** — lossy compression, not state capture. This reframing is what makes the problem tractable
and what the rest of Cairn builds on.
