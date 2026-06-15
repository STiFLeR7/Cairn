---
id: AP-0006
title: License + contribution + citation scaffolding
phase: phase-0-definition
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0001]
related_docs: [LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, CITATION.cff, CHANGELOG.md]
related_adrs: [ADR-0001]
---

## Objective

Put the open-source legal and contribution scaffolding in place: Apache-2.0 license, contribution guide
(encoding the three rules + Definition of Done), code of conduct, citation metadata, and a changelog.

## Scope

**In:** `LICENSE` (Apache-2.0), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CITATION.cff`, `CHANGELOG.md`.
**Out:** the governance docs they reference (AP-0002/0003).

## Deliverables

- `LICENSE` — Apache-2.0 full text
- `CONTRIBUTING.md` — three rules, workflow, Definition of Done
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1
- `CITATION.cff`
- `CHANGELOG.md`

## Acceptance Criteria

- [x] Apache-2.0 license present (per ADR-0001)
- [x] CONTRIBUTING encodes doc-first / AP-driven / phase-based and the Definition of Done
- [x] Citation metadata present and consistent with positioning
- [x] Changelog initialized with the Phase 0 foundation entry
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`)

## Dependencies

- AP-0001

## Status / Log

- 2026-06-15 — Proposed → In Progress. License, contribution, conduct, citation, and changelog authored.
- 2026-06-15 — In Review → Done. Reviewed & approved; all acceptance criteria met.
