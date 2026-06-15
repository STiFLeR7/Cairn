---
title: Agent State Taxonomy
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0012]
related_adrs: [ADR-0001]
---

# Agent State Taxonomy

[Continuation sufficiency](problem-formalization.md) ranges over *all* of an agent's state, but not all
state is equally recoverable, and different layers own different parts. This taxonomy decomposes agent
state into five classes, gives each its recoverability and its owning layer (per the
[two-layer model](code-harness-and-runtime.md)), and routes each to the recovery mechanism that handles
it. It feeds the Continuation State schema (`AP-0013`) and the effect-safety protocol (`AP-0017`).

## The five layers

| Layer | Examples | Recoverability | Owner | Handled by |
|---|---|---|---|---|
| **1. Durable external** | workspace files, databases, git history | **Easy** — copy-on-write FS snapshot, container image, git commit | Runtime | Workspace snapshot |
| **2. Irreversible effects** | sent emails, payments, opened PRs, posted messages | **None** — cannot be rolled back; must not be repeated | Runtime | Append-only **effect ledger** (WAL) |
| **3. Working memory (`M`)** | active sub-goal, reasoning, hypotheses, ruled-out approaches | **The crux** — not faithfully serializable; non-deterministic to reconstruct | Code Harness | Distilled into the **Continuation State** |
| **4. Plan / intent** | the plan, done/pending/blocked steps, dependency graph | **Recoverable if made explicit** (don't leave it only in `M`) | Code Harness | Continuation State (durable core) |
| **5. Runtime handles** | processes, cwd, env vars, auth/session tokens, open sockets | **Partial** — some via CRIU-style capture; some must be re-established | Runtime | Re-established on resume bootstrap |

## Reading the table

- **Layers 1, 2, 5 are Runtime-owned mechanism.** They are about the *world and the machine*. The
  Runtime can snapshot files (1), must log effects because it cannot undo them (2), and re-establishes or
  captures process handles (5).
- **Layers 3 and 4 are Code-Harness-owned semantics.** They are about the *agent's mind and intent*.
  Layer 3 — **working memory** — is the crux of the whole problem: it holds what matters most for
  continuation yet is the least serializable. Layer 4 — **plan/intent** — is recoverable *only if the
  Code Harness makes it explicit* rather than leaving it implicit inside `M`.

This is the [one concern, two altitudes](code-harness-and-runtime.md) rule applied to *state*: the
Runtime owns the durable/physical facets, the Code Harness owns the logical/intent facets.

## Layer 3 is why naive checkpointing fails

A VM snapshot captures layers 1 and 5 perfectly and is blind to the *meaning* in layer 3. A
context-summarizer captures layer 3 and ignores layers 1, 2, 5. Robust recovery needs both — exactly the
[neither-alone argument](recovery-in-the-two-layer-model.md). The minimal sufficient state `S` is
therefore a *structured* object spanning layers, not a blob of any single one.

## Feeding the Continuation State schema (forward reference, `AP-0013`)

The taxonomy implies the shape of the Continuation State (the "cairn"):

- **Durable core** (never pruned — the sufficient statistic): intent + active sub-goal (4); plan with
  status + dependencies (4); decision ledger incl. **ruled-out dead-ends** (3, distilled); a reference
  into the effect ledger (2); a pointer/digest to the workspace snapshot (1); verification state (3/1);
  provenance (model/harness version, step index).
- **Elastic tail**: recent raw working-memory detail (3) that compaction may prune but a checkpoint
  freezes at write time.

The durable-core / elastic-tail split is what lets one object serve both compaction and checkpointing
(the *Checkpoints Are Compactions* thesis); the distillation policy that produces it is designed in
Phase 2 (`AP-0016`).

## Summary

Agent state splits into five layers — durable external, irreversible effects, working memory, plan/
intent, runtime handles — with sharply different recoverability and clear layer ownership. Working memory
(layer 3) is the crux; effects (layer 2) are the irreversible danger. The taxonomy maps directly onto the
Continuation State's durable core + elastic tail, and onto the Runtime-mechanism / Code-Harness-semantics
division of recovery.
