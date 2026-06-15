---
title: ADR-0006 — Effect-safety via write-ahead effect ledger + idempotency
status: frozen
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0017, AP-0018]
related_adrs: [ADR-0001, ADR-0003]
---

# ADR-0006 — Effect-safety write-ahead ledger

- **Status:** Accepted
- **Date:** 2026-06-15

## Context

Irreversible external effects cannot be rolled back, and a resumed agent must not repeat them. Execution
is non-deterministic and there is no transaction boundary, so the world itself must be the source of
truth about what already happened.

## Decision

Adopt a **write-ahead effect ledger**: log `INTENT` (with an idempotency key and the tool's recovery
class) durably *before* executing an irreversible effect, and `COMPLETE` after. On resume, resolve every
`INTENT`-without-`COMPLETE` key by a policy keyed to the [tool class](../concepts/tool-effect-taxonomy.md):
redo (`safe-to-retry`), verify-then-redo-or-skip (`check-before-retry`), or escalate (`never-retry`). See
[effect-safety-protocol.md](../design/effect-safety-protocol.md).

## Consequences

- Eliminates duplicate effects for `safe-to-retry` and `check-before-retry` tools (**claim C3**);
  `never-retry` is an acknowledged, escalated limit — not hidden.
- Requires boundary-contract invariant **I1** (write-ahead durability) and the tool declaration of
  AP-0018.
- Adds a per-effect ledger write — accepted as the cost of safety on the effect-safety fidelity gate.

## Supersedes / superseded by

None.
