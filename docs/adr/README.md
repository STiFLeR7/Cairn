---
title: Architecture Decision Records
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0002]
related_adrs: []
---

# Architecture Decision Records (ADRs)

An ADR captures **one decision** and its rationale. ADRs are **immutable once accepted** — to change a
decision, write a new ADR that supersedes the old one (and mark the old one `superseded`).

Use the [ADR template](../../project/templates/adr-template.md). Number monotonically: `ADR-0001`, …

## Index

| ID | Title | Status |
|---|---|---|
| [ADR-0001](ADR-0001-foundational-decisions.md) | Foundational project decisions | Accepted |
| [ADR-0002](ADR-0002-continuation-state-shape.md) | Continuation State shape (durable core + elastic tail) | Accepted |
| [ADR-0003](ADR-0003-boundary-contract.md) | Code Harness ↔ Runtime boundary contract | Accepted |
| [ADR-0004](ADR-0004-regrounding-not-replay.md) | Resume by re-grounding, not trajectory replay | Accepted |
| [ADR-0005](ADR-0005-unified-distillation.md) | One distillation mechanism for compaction + checkpointing | Accepted |
| [ADR-0006](ADR-0006-effect-safety-wal.md) | Effect-safety via write-ahead effect ledger + idempotency | Accepted |
| [ADR-0007](ADR-0007-implementation-stack.md) | Implementation stack (Python) + no-hardcoded-harness principle | Accepted |
| [ADR-0008](ADR-0008-recovery-v1-implementation.md) | Recovery v1 implementation decisions (snapshot numbering, digest, resume, effects, failure hook) | Accepted |
| [ADR-0009](ADR-0009-evaluation-framework.md) | Evaluation framework design & honest-results policy | Accepted |
| [ADR-0010](ADR-0010-live-model-provider-integration.md) | Live LLM provider integration via an injected transport | Accepted |
