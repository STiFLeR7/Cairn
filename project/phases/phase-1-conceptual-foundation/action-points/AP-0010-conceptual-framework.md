---
id: AP-0010
title: Conceptual framework docs (Code Harness / Runtime / recovery)
phase: phase-1-conceptual-foundation
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0007]
related_docs: [docs/concepts/code-harness-and-runtime.md, docs/concepts/recovery-in-the-two-layer-model.md]
related_adrs: [ADR-0001]
---

## Objective

Author the canonical conceptual framework: the **Code Harness** and **Agent Runtime Harness**, the
organizing rule that shared concerns are *split by scope, not duplicated* ("same concern, two
altitudes"), the boundary between them, and where recovery lives across the two layers.

## Scope

**In:** definitions of both layers; the shared-concern split rule with the memory/execution/recovery/
planning table; the "logically above, physically inside" topology resolution; recovery as Runtime
*mechanism* + Code Harness *semantics*; the claim that robust recovery is the proof case for the
two-layer model.
**Out:** the concrete boundary-contract *interface* (Phase 2, AP-0014); protocol specifics.

## Deliverables

- `docs/concepts/code-harness-and-runtime.md` — the two-layer model and the split rule.
- `docs/concepts/recovery-in-the-two-layer-model.md` — how recovery maps across the layers.

## Acceptance Criteria

- [x] Both layers are defined with their responsibilities
- [x] The "same concern, two altitudes" rule is stated with the shared-concern table
- [x] The topology is resolved consistently (logically above, physically inside) and diagrams obey it
- [x] Recovery is split into Runtime-mechanism vs Code-Harness-semantics, with the "neither alone" argument
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- AP-0007 (the framework is framed around the recovery problem)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 1 entry).
- 2026-06-15 — Accepted → Done. Delivered `docs/concepts/code-harness-and-runtime.md` and
  `docs/concepts/recovery-in-the-two-layer-model.md` (two-layer model, split rule, topology, recovery split).
