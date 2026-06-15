---
title: ADR-0003 — The Code Harness ↔ Runtime boundary contract
status: frozen
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0014]
related_adrs: [ADR-0001, ADR-0002]
---

# ADR-0003 — Boundary contract

- **Status:** Accepted
- **Date:** 2026-06-15

## Context

The two-layer model needs a concrete, stable interface or it remains a taxonomy. Recovery makes the
interface unavoidable: someone must snapshot, persist, log effects, and re-observe, and someone must
decide salience and re-plan.

## Decision

Adopt the operation set in [boundary-contract.md](../design/boundary-contract.md) as the **stable seam**
between Code Harness and Runtime, split into Runtime *mechanism* operations and Code Harness *semantics*
operations, governed by invariants **I1–I5** (write-ahead effects, atomic checkpoint, monotonic offsets,
mutual consistency, latest-before-failure).

## Consequences

- The contract is the unit of portability: a different Code Harness or Runtime can interoperate if it
  honors this seam (long-term scope — framework adoption).
- Invariant I1 (write-ahead effects) and I2 (atomic checkpoint) are the load-bearing guarantees recovery
  depends on; the Runtime implementation (Phase 3) is judged against them.
- The contract intentionally excludes storage backend, salience policy, and reconcile logic — these vary
  without changing the seam.

## Supersedes / superseded by

None.
