---
id: AP-0002
title: Ratify documentation governance model
phase: phase-0-definition
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0001]
related_docs: [docs/governance/documentation-policy.md, docs/governance/glossary.md, docs/adr/README.md]
related_adrs: [ADR-0001]
---

## Objective

Make "documentation is a first-class artifact" enforceable: define the documentation policy, the doc
taxonomy, required front-matter, the change protocol, and the ADR practice.

## Scope

**In:** documentation policy; doc taxonomy; front-matter schema; change protocol; ADR practice + index;
glossary.
**Out:** AP/phase workflow (AP-0003); the docs' *subject-matter* content (later phases).

## Deliverables

- `docs/governance/documentation-policy.md`
- `docs/governance/glossary.md`
- `docs/adr/README.md` + `docs/adr/ADR-0001-foundational-decisions.md`
- ADR template (`project/templates/adr-template.md`)

## Acceptance Criteria

- [x] Documentation policy defines doc-as-DoD, single-source-of-truth, traceability, living/frozen
- [x] Front-matter schema specified and applied to existing docs
- [x] ADR practice documented; ADR-0001 records foundational decisions
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- AP-0001 (skeleton)

## Status / Log

- 2026-06-15 — Proposed → In Progress. Policy, glossary, ADR practice, and ADR-0001 authored.
- 2026-06-15 — In Review → Done. Reviewed & approved; all acceptance criteria met.
