---
id: AP-0016
title: Unified compaction/checkpoint distillation design (core/tail)
phase: phase-2-architecture-protocol
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0013]
related_docs: [docs/design/unified-distillation.md]
related_adrs: [ADR-0005]
---

## Objective

Design the **single distillation mechanism** that produces the Continuation State for *both* online
context compaction and durable checkpointing — the operational realization of *Checkpoints Are
Compactions*. Resolve the core/tail tension: how the same write serves a lossy compaction and a faithful
checkpoint without degrading recovery fidelity (claim C2).

## Scope

**In:** the two write paths (compaction write vs checkpoint write) and why they share one distillation;
the durable-core (always kept) vs elastic-tail (pruned online / frozen at checkpoint) policy; the
distillation triggers (window-pressure, step boundary, pre-effect); what is summarized vs preserved
verbatim; the argument that this does not degrade checkpoint fidelity. An ADR (ADR-0005) for the unified
mechanism.
**Out:** the schema itself (AP-0013); the resume side (AP-0015); implementation and tuning (Phase 4/5).

## Deliverables

- `docs/design/unified-distillation.md` — the mechanism, both write paths, core/tail policy, triggers.
- `docs/adr/ADR-0005-unified-distillation.md` — decision: one mechanism, durable core + frozen tail.

## Acceptance Criteria

- [x] Both write paths (compaction, checkpoint) are specified and shown to share one distillation
- [x] The durable-core / elastic-tail handling per path is defined (prune vs freeze)
- [x] Distillation triggers and the step-boundary definition are specified
- [x] The fidelity-non-degradation argument (C2) is stated and linked to the claims registry
- [x] ADR-0005 records the unified-distillation decision
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- AP-0013 (the object distillation produces)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 2 entry).
- 2026-06-15 — Accepted → Done. Delivered `docs/design/unified-distillation.md` + ADR-0005.
