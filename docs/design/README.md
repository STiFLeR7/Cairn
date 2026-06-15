---
title: Design
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0013, AP-0014, AP-0015, AP-0016, AP-0017, AP-0018]
related_adrs: [ADR-0002, ADR-0003, ADR-0004, ADR-0005, ADR-0006]
---

# Design

Architecture and protocol specifications (Phase 2). Each spec is implementable; Phase 3 builds the
substrate against them. Load-bearing decisions are recorded as [ADRs](../adr/).

| Spec | Covers | AP | ADR |
|---|---|---|---|
| [continuation-state-schema.md](continuation-state-schema.md) | The cairn: durable core + elastic tail, field by field | AP-0013 | ADR-0002 |
| [boundary-contract.md](boundary-contract.md) | Code Harness ↔ Runtime operations + invariants I1–I5 | AP-0014 | ADR-0003 |
| [resume-protocol.md](resume-protocol.md) | RGR: load → re-observe → reconcile → re-plan → continue | AP-0015 | ADR-0004 |
| [unified-distillation.md](unified-distillation.md) | One `distill` for compaction + checkpoint (core/tail) | AP-0016 | ADR-0005 |
| [effect-safety-protocol.md](effect-safety-protocol.md) | Write-ahead INTENT/COMPLETE ledger + reconciliation | AP-0017 | ADR-0006 |
| [tool-recovery-policy.md](tool-recovery-policy.md) | Tool declaration + per-class resume policy + default | AP-0018 | ADR-0006 |

These specs consume the Phase 1 [concepts](../concepts/) (state taxonomy, tool-effect taxonomy,
fidelity, the two-layer model) and feed Phase 3 implementation.
