---
id: AP-0014
title: Code Harness ↔ Runtime boundary contract spec
phase: phase-2-architecture-protocol
status: Accepted
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0010, AP-0013]
related_docs: [docs/design/boundary-contract.md]
related_adrs: [ADR-0003]
---

## Objective

Specify the interface between the Code Harness and the Runtime — the contract recovery forces us to make
explicit. Define each operation, its parameters, its return, and the **invariants** each side must
uphold (e.g. effects are logged write-ahead; checkpoints are atomic).

## Scope

**In:** the operation set — `snapshot_workspace`, `checkpoint`, `load_latest`, `append_effect` /
`complete_effect`, `list_effects_since`, and the Code-Harness-side `distill` / `reconcile` seams;
pre/postconditions and invariants; the durability/atomicity guarantees the Runtime must provide; an ADR
(ADR-0003) for the contract.
**Out:** the resume *protocol* that calls these (AP-0015); the effect-safety *semantics* (AP-0017);
implementation.

## Deliverables

- `docs/design/boundary-contract.md` — operations, signatures, invariants, sequence sketches.
- `docs/adr/ADR-0003-boundary-contract.md` — decision: this is the stable Code Harness ↔ Runtime seam.

## Acceptance Criteria

- [ ] Each operation has a signature, semantics, and pre/postconditions
- [ ] Invariants are stated (write-ahead effects; atomic checkpoint; monotonic effect offsets)
- [ ] The Runtime-owned (mechanism) vs Code-Harness-owned (semantics) operations are clearly split
- [ ] The contract is consistent with the Continuation State schema (AP-0013)
- [ ] ADR-0003 records the contract decision
- [ ] Documentation updated (single source of truth, front-matter current)
- [ ] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- AP-0010 (two-layer model), AP-0013 (the state the contract moves)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 2 entry).
