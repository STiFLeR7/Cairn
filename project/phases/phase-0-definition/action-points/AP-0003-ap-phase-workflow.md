---
id: AP-0003
title: Define AP & phase workflow process docs
phase: phase-0-definition
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0001, AP-0002]
related_docs: [docs/governance/ap-workflow.md, docs/governance/phase-process.md]
related_adrs: [ADR-0001]
---

## Objective

Define how work is organized: the Action Point lifecycle and anatomy, and the phase lifecycle and
completion gating — with reusable templates.

## Scope

**In:** AP workflow (IDs, lifecycle, anatomy, DoD, linkage); phase process (lifecycle, anatomy, gating);
AP and phase templates.
**Out:** the documentation policy itself (AP-0002); populating the tracker tables (AP-0005).

## Deliverables

- `docs/governance/ap-workflow.md`
- `docs/governance/phase-process.md`
- `project/templates/ap-template.md`, `project/templates/phase-template.md`

## Acceptance Criteria

- [x] AP lifecycle, ID scheme, and required fields specified
- [x] Phase lifecycle and completion gating specified
- [x] Templates exist and match the documented schema
- [x] This very AP file demonstrates the schema in practice
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- AP-0001, AP-0002

## Status / Log

- 2026-06-15 — Proposed → In Progress. AP workflow, phase process, and templates authored.
- 2026-06-15 — In Review → Done. Reviewed & approved; all acceptance criteria met.
