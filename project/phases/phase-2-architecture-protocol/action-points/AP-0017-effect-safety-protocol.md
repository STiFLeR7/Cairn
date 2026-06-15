---
id: AP-0017
title: Effect-safety write-ahead protocol spec
phase: phase-2-architecture-protocol
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0012, AP-0014]
related_docs: [docs/design/effect-safety-protocol.md]
related_adrs: [ADR-0006]
---

## Objective

Specify the **effect-safety write-ahead protocol** that prevents a resumed agent from re-executing
irreversible effects: the INTENT → execute → COMPLETE discipline against the Runtime's append-only effect
ledger, and the resume-time reconciliation that closes the danger window. This is the mechanism behind
claim C3 and the effect-safety fidelity axis.

## Scope

**In:** the effect-ledger record format (intent, idempotency key, status, timestamp/step); the
write-ahead sequence; resume-time detection of INTENT-without-COMPLETE; the redo/skip/escalate decision
keyed to the [tool effect taxonomy](../../../docs/concepts/tool-effect-taxonomy.md); the acknowledged
`never-retry` limit. An ADR (ADR-0006) for the write-ahead effect protocol.
**Out:** the per-tool classification *mapping* (AP-0018); implementation.

## Deliverables

- `docs/design/effect-safety-protocol.md` — record format, WAL sequence, resume reconciliation, escalation.
- `docs/adr/ADR-0006-effect-safety-wal.md` — decision: write-ahead effect ledger + idempotency.

## Acceptance Criteria

- [x] The effect-ledger record format and the INTENT/COMPLETE sequence are specified
- [x] Resume-time reconciliation (detect + resolve the danger window) is defined
- [x] The redo/skip/escalate policy is keyed to the three tool classes
- [x] The `never-retry` scope limit is stated explicitly (escalation path)
- [x] ADR-0006 records the effect-safety decision; C3 is referenced
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- AP-0012 (tool taxonomy), AP-0014 (effect-ledger operations in the contract)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 2 entry).
- 2026-06-15 — Accepted → Done. Delivered `docs/design/effect-safety-protocol.md` + ADR-0006.
