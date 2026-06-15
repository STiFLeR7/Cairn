---
title: ADR-0005 — One distillation mechanism for compaction and checkpointing
status: frozen
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0016]
related_adrs: [ADR-0001, ADR-0002]
---

# ADR-0005 — Unified distillation

- **Status:** Accepted
- **Date:** 2026-06-15

## Context

Long-horizon agents already recover from context loss via compaction; crash recovery needs a checkpoint.
These look like two systems. The thesis *Checkpoints Are Compactions* claims they are one operation at
different timescales.

## Decision

Use a **single distillation mechanism** (`distill`) for both online compaction and durable checkpointing.
The two differ only in **elastic-tail handling** (compaction prunes; checkpoint freezes) and
**persistence** (checkpoint persists atomically). The **durable core** — the sufficient statistic — is
produced identically by both. See [unified-distillation.md](../design/unified-distillation.md).

## Consequences

- **Recovery is exercised continuously** by everyday compaction; no separate, rarely-tested checkpoint
  path. "Compacts well ⇒ recovers well."
- **Claim C2** becomes the falsifiable test of this decision: unified distillation must not degrade
  checkpoint fidelity vs a checkpoint-only baseline.
- Depends on ADR-0002 (core/tail shape). If C2 were refuted, this ADR would be revisited (superseded),
  not silently kept.

## Supersedes / superseded by

None.
