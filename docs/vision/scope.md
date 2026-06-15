---
title: Scope
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0004]
related_adrs: [ADR-0001]
---

# Scope

## v1 scope (the three pillars)

v1 commits to all three pillars on a **minimal, custom harness** (chosen over OpenHands/LangGraph so the
contribution — the mechanism and the contract — stays unobstructed and the ablations stay trivial):

1. **Unified distillation** — one mechanism writing the Continuation State for both compaction and checkpoint.
2. **Re-grounding resume** — the RGR protocol.
3. **Effect-safety** — write-ahead effect ledger + idempotency, evaluated on a small tool set.

v1 targets a **single agent** and a controlled/code+web evaluation.

## Long-term scope (the ambition arc)

- **Multi-agent recovery** — recovering a swarm; shared coordination state; partial failure of one agent.
- **Cross-model / cross-version resume** — checkpoint on model A, resume on model B (RGR's structural
  advantage over replay).
- **Human-in-the-loop recovery** for the `never-retry` effect class.
- **Contract adoption** — the boundary contract used *by* frameworks as a standard recovery interface.
- **Formal effect-safety guarantees / verification.**
- **Very-long-horizon agents** (days–weeks) — recovery as the enabling subsystem for persistent
  autonomous workers.

## Explicitly out of scope (permanently)

- Being a full agent framework.
- Training or serving models.
- General-purpose workflow orchestration.

Cairn is the **recovery layer** — nothing more, deliberately.

## Boundary with adjacent concerns

Cairn assumes (does not provide) a Code Harness that emits code-as-action and a Runtime that provides a
sandbox, filesystem, and tool access. The minimal harness built in Phase 3 exists *to exercise recovery*,
not to be a general agent platform.
