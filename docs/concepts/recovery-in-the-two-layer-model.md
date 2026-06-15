---
title: Recovery in the Two-Layer Model
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0010]
related_adrs: [ADR-0001]
---

# Recovery in the Two-Layer Model

Recovery is the canonical proof that the [two-layer split](code-harness-and-runtime.md) is real. This
document maps the [recovery problem](problem-formalization.md) onto the two layers and argues that
neither layer can recover well alone.

## 1. Recovery splits into mechanism and semantics

By the organizing rule (*one concern, two altitudes*), recovery is one concern cut into a durable facet
and a logical facet:

| Facet | Owner | Responsibility |
|---|---|---|
| **Mechanism** | **Runtime** | Snapshot the workspace; maintain the append-only effect ledger; persist checkpoints; detect failure; bootstrap a resumed process. Faithful, dumb, durable. |
| **Semantics** | **Code Harness** | Decide *what is salient* to keep (produce the sufficient state `S`); re-observe and reconcile the world on resume; re-plan; verify coherence. Intelligent, lossy, adaptive. |

The Runtime knows *how* to save and restore bytes and how to record that an effect happened. The Code
Harness knows *what those bytes mean* and *what to do next*. Recovery is their cooperation.

## 2. Why neither layer suffices alone

This is the heart of the argument.

**Runtime-only recovery fails.** A faithful low-level snapshot (VM/container image, even the raw context
bytes) restores the *form* of the agent but not its *situational awareness*. After a model restart or a
context-window loss, the resumed agent holds bytes it did not reason to and cannot reliably re-establish
*what it was doing and why*. Mechanism without semantics restores a body without a mind. And because
execution is non-deterministic, you cannot "replay forward" from the snapshot to recover the lost
understanding.

**Code-Harness-only recovery fails.** An agent that merely summarizes its context and continues — with no
durable workspace snapshot and no effect ledger — loses external and effect state. It cannot tell which
files were half-written or which irreversible actions already fired, so on resume it corrupts completed
work or **re-executes effects** (re-sends the email, re-opens the PR). Semantics without mechanism acts on
a world it can no longer see accurately.

> **Therefore:** robust recovery requires the Runtime's faithful mechanism **and** the Code Harness's
> semantic re-grounding, together. That mutual necessity is exactly what a "two-layer model" should
> predict — which is why recovery is its proof case.

## 3. The recovery loop across the boundary

Recovery is not a restore; it is a loop that crosses the layer boundary. (The concrete protocol is
designed in Phase 2 — resume protocol `AP-0015`, distillation `AP-0016`, effect-safety `AP-0017`;
here we show only the division of labor.)

```
   FAILURE  F@k
      │
   ┌──┴── Runtime (mechanism) ───────────────────────────────┐
   │  detect failure                                          │
   │  load: latest checkpoint S, workspace snapshot, effects  │
   └──┬──────────────────────────────────────────────────────┘
      │ hands S + observable world up to ▼
   ┌──┴── Code Harness (semantics) ──────────────────────────┐
   │  re-observe the actual world (files, effect ledger)      │
   │  reconcile S against reality (detect the torn step)      │
   │  re-plan from intent — a different but valid path is OK   │
   └──┬──────────────────────────────────────────────────────┘
      │ resumes productive work, directing the Runtime again ▼
   continue
```

Two points worth drawing out:

- **Observability is the perception channel.** The Runtime's observability layer is not just for humans;
  it is *how the Code Harness sees the world it must reconcile against*. It is load-bearing in the loop,
  not a sidecar.
- **Recovery begins with re-observation, not re-action.** The resumed agent's first move is to look,
  then reconcile, then act — never to blindly resume the next step.

## 4. The same boundary the framework was missing

Designing recovery forces the **boundary contract** between the layers to become explicit — the very
interface the conceptual framework otherwise leaves implicit. In skeleton form (specified under Phase 2,
`AP-0014`):

```
Runtime:       snapshot_workspace() -> snap_id
               checkpoint(S, snap_id, effect_offset)
               load_latest() -> (S, snap_id, effect_offset)
               append_effect(intent, idempotency_key); complete_effect(key)
               list_effects_since(offset)
Code Harness:  distill(trajectory) -> S          # the salience policy (semantics)
               reconcile(S, observed_world) -> plan
```

Recovery is thus both a feature *and* the forcing function that turns the two-layer model from a taxonomy
into an architecture.

## Summary

Recovery = Runtime **mechanism** (snapshots, effect ledger, checkpoints, resume bootstrap) + Code Harness
**semantics** (salience, re-observation, reconciliation, re-planning). Each alone fails — one restores a
mindless body, the other acts blindly on the world — so their mutual necessity is the proof that the
two-layer split is real. The cooperation is realized through a boundary contract that recovery forces us
to make explicit.
