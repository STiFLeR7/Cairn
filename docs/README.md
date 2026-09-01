# Cairn Documentation

This tree holds **knowledge** — the rules we work by and the understanding we build. Live project
*state* (phases, Action Points, trackers) lives under [`../project/`](../project/).

> **Rules vs. state:** `docs/governance/` defines *how we work*; `project/` records *where we are*.

## Map

| Area | Contents |
|---|---|
| [`governance/`](governance/) | [documentation policy](governance/documentation-policy.md) · [AP workflow](governance/ap-workflow.md) · [phase process](governance/phase-process.md) · [glossary](governance/glossary.md) |
| [`vision/`](vision/) | [vision](vision/vision.md) · [positioning](vision/positioning.md) · [scope](vision/scope.md) |
| [`concepts/`](concepts/) | The conceptual framework (Code Harness / Runtime / recovery). *Populated in Phase 1.* |
| [`research/`](research/) | Related-work survey, claims registry, paper drafts. *Populated in Phase 1.* |
| [`design/`](design/) | Legacy architecture/specs plus the admitted Continuation Contract v0 and Receipt/Reconciliation Contract v0. |
| [`adr/`](adr/) | Architecture Decision Records — immutable once accepted. |

## Document front-matter

Active design documents carry machine-readable front-matter so freshness and traceability are visible.
Sealed contracts and raw evidence retain their admitted bytes; their status and evidence boundary are
stated in the document rather than edited for formatting.

```yaml
---
title: ...
status: draft | active | frozen | superseded
last_updated: YYYY-MM-DD
owner: ...
related_aps: [AP-0001, ...]
related_adrs: [ADR-0001, ...]
---
```
