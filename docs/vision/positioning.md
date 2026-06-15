---
title: Positioning
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0004]
related_adrs: [ADR-0001]
---

# Positioning

## Statement

> Cairn is an open, framework-agnostic **reference implementation and benchmark for recoverable
> long-horizon agents**. It defines the Continuation State contract and the Re-grounding Recovery (RGR)
> protocol, and ships a failure-injection harness for measuring recovery fidelity. It is a research
> artifact first and a reusable pattern second — it **complements** agent frameworks (OpenHands,
> LangGraph, custom harnesses) rather than replacing them.

## What Cairn is — and is not

| Cairn **is** | Cairn **is not** |
|---|---|
| A specification (Continuation State + boundary contract) | A production agent framework |
| A minimal reference implementation | A model |
| A failure-injection benchmark + fidelity metric | A general workflow orchestrator |

Staying narrow is deliberate: it keeps the contribution legible and the contract adoptable.

## Audience

| Tier | Need | What they take |
|---|---|---|
| Researchers | Reproduce / extend recovery results | The benchmark, the metric, the ablations |
| Framework authors | Add recovery to their harness | The boundary contract + reference protocol |
| Practitioners | Understand the pattern | The conceptual docs + the thesis |

## Relationship to prior art

Cairn is positioned against — and credits — durable-execution engines (Temporal), agent-framework
persistence (LangGraph checkpointers, OpenHands state), virtual context management (MemGPT/Letta), and
classical recovery (ARIES, event sourcing, CRIU). Each solves a *slice*. The white space Cairn occupies:
crash-recovery **+** non-determinism **+** effect-safety **+** context-loss, unified under
*Checkpoints Are Compactions* with a recovery-fidelity metric. The full survey and positioning matrix
are in [`../research/related-work.md`](../research/related-work.md).

## License

[Apache-2.0](../../LICENSE) — chosen for its explicit patent grant and institutional credibility
(see [ADR-0001](../adr/ADR-0001-foundational-decisions.md)).
