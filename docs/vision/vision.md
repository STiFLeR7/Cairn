---
title: Vision
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0004]
related_adrs: [ADR-0001]
---

# Vision

> **Agents should survive failure the way good engineers do** — by remembering what they were doing,
> checking what actually happened, and continuing — **not by starting over.**

## The problem

As AI systems evolve from chatbots into autonomous software engineers, the weakest joint is **recovery**.
When an agent fails at step 47, it typically restarts from zero — discarding hours of work, partial
artifacts, and hard-won situational awareness. Recovery is still weak across nearly every agent system.

This is *not* the classical checkpoint/restart problem. Classical recovery (CRIU, VM snapshots, database
WAL, durable-execution engines) assumes serializable state, deterministic replay, and clean transaction
boundaries. Agents violate all three:

1. The most important state lives in the **model's context** — huge, lossy, not faithfully serializable.
2. LLM execution is **non-deterministic** — you cannot replay the log and get the same trajectory.
3. The resume point is **semantically ambiguous** — "step 47" is not a transaction boundary, and
   external effects (sent emails, opened PRs) are not transactional.

## What Cairn makes true

Cairn makes recovery a **first-class, measurable property** of autonomous agents:

- A durable, typed **Continuation State** (a *cairn*) that doubles as the agent's working memory and its
  recovery checkpoint.
- A **Re-grounding Recovery (RGR)** protocol: after loss, the agent re-observes the world and re-grounds
  from the Continuation State — restoring *understanding*, not replaying *tokens*.
- **Effect-safety**: a write-ahead effect ledger ensures a resumed agent never re-acts on the world.

## The thesis

**Checkpoints Are Compactions.** Long-horizon agents already recover from context loss every time they
compact an overflowing window. A checkpoint is a compaction you can roll back to. By building *one*
distillation mechanism for both, the distillation that recovery depends on is continuously exercised by
normal operation — *an agent that compacts well recovers well, by construction.*

## Why this matters

Code-only agent systems are *smart but fragile*. Runtime-only systems are *stable but rigid*. Robust
recovery requires both layers cooperating — the Runtime provides faithful low-level snapshots and an
effect ledger; the Code Harness provides semantic re-grounding. Recovery is therefore the **proof case**
that the two-layer harness is real, not cosmetic.
