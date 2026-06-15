---
title: ADR-0002 — Continuation State is a typed object with durable core + elastic tail
status: frozen
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0013]
related_adrs: [ADR-0001]
---

# ADR-0002 — Continuation State shape

- **Status:** Accepted
- **Date:** 2026-06-15

## Context

Recovery needs a representation of the sufficient state `S`
([problem-formalization](../concepts/problem-formalization.md)). The naive choice is to checkpoint the
raw context window (a blob). But the decisive state (working memory) is huge, redundant, and
non-serializable in a faithful way, and the same object must serve *both* online compaction and durable
checkpointing (the *Checkpoints Are Compactions* thesis).

## Decision

The Continuation State is a **typed, structured object** with two parts:

- a **durable core** — the sufficient statistic, never pruned; and
- an **elastic tail** — recent detail, pruned during compaction and frozen at checkpoint time.

It is **not** a serialized context blob. Field membership in the core is governed by the rule: *include
iff losing it breaks continuation equivalence.* See
[continuation-state-schema.md](../design/continuation-state-schema.md).

## Consequences

- **Enables the unification** (ADR-0005): compaction prunes the tail; checkpoint freezes it; both keep the
  core. One mechanism, no fidelity loss in the core.
- **Compression, not capture:** producing the object is lossy distillation under a fidelity constraint,
  matching the problem framing.
- **Costs:** a schema must be maintained and versioned; the distillation policy must decide core-vs-tail
  membership (designed in AP-0016). Accepted as the price of dual-purpose, fidelity-bounded state.

## Supersedes / superseded by

None.
