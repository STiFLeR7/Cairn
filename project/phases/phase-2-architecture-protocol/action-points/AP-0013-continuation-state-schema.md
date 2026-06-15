---
id: AP-0013
title: Continuation State (cairn) schema spec
phase: phase-2-architecture-protocol
status: Accepted
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0007, AP-0012]
related_docs: [docs/design/continuation-state-schema.md]
related_adrs: [ADR-0002]
---

## Objective

Specify the **Continuation State** (a "cairn") — the typed object that is the sufficient state `S` for
continuation. Define its **durable core** and **elastic tail**, every field, field provenance, and the
versioning rules, traced to the [state taxonomy](../../../docs/concepts/state-taxonomy.md).

## Scope

**In:** the full field list of the durable core (intent, plan, decision ledger incl. ruled-out
dead-ends, effect-ledger ref, workspace-snapshot pointer/digest, verification state, provenance) and the
elastic tail; field types and semantics; serialization format choice; schema versioning; the
core-vs-tail boundary rule. An ADR (ADR-0002) for the schema shape.
**Out:** the *policy* that fills it (AP-0016); the *contract* that persists it (AP-0014); code.

## Deliverables

- `docs/design/continuation-state-schema.md` — the schema, field by field, with a worked example.
- `docs/adr/ADR-0002-continuation-state-shape.md` — decision: typed object, durable core + elastic tail.

## Acceptance Criteria

- [ ] Every durable-core field is specified with type, meaning, and its source state-taxonomy layer
- [ ] The elastic tail and the core/tail boundary rule are defined
- [ ] Schema versioning + provenance (model/harness version, step index) are specified
- [ ] A concrete worked example of a populated Continuation State is included
- [ ] ADR-0002 records the schema-shape decision
- [ ] Documentation updated (single source of truth, front-matter current)
- [ ] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- AP-0007 (sufficiency), AP-0012 (state taxonomy → field provenance)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 2 entry).
