---
title: Action Point (AP) Workflow
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0003]
related_adrs: [ADR-0001]
---

# Action Point (AP) Workflow

All work in Cairn is organized into **Action Points**. An AP is the unit of *meaningful change* —
larger than a commit, smaller than a phase. One AP = one coherent deliverable with checkable
acceptance criteria.

## Granularity

If you cannot write crisp, verifiable Acceptance Criteria for an AP, it is too big — split it. If a
"change" is a one-line typo with no deliverable, it does not need its own AP (fold it into a related one).

## Identifiers

- Global, monotonic: `AP-0001`, `AP-0002`, … (never reused).
- The owning **phase** is recorded in the AP's front-matter, *not* in the ID — so an AP can move
  between phases without renumbering.

## Lifecycle

```
Proposed → Accepted → In Progress → In Review → Done
                  ↘ Blocked ↗            ↘ Superseded
```

| Status | Meaning |
|---|---|
| Proposed | Drafted, not yet committed to a phase |
| Accepted | Committed; ready to be worked |
| In Progress | Actively being worked |
| In Review | Deliverables complete; under review against Acceptance Criteria |
| Done | Acceptance Criteria met, incl. documentation |
| Blocked | Cannot proceed (record the blocker) |
| Superseded | Replaced by another AP (link it) |

## Anatomy

Every AP file (see [template](../../project/templates/ap-template.md)) contains:

```markdown
---
id: AP-0001
title: ...
phase: phase-0-definition
status: Proposed
owner: ...
created: YYYY-MM-DD
updated: YYYY-MM-DD
depends_on: [AP-...]
related_docs: [...]
related_adrs: [...]
---
## Objective          # why this exists (one paragraph)
## Scope              # explicitly in / out
## Deliverables       # concrete artifacts produced
## Acceptance Criteria  # checkable; MUST include "documentation updated"
## Dependencies       # APs / external blockers
## Status / Log       # dated state transitions
```

## Linkage & Definition of Done

- Branches and commits reference the AP ID (e.g. `AP-0004: author vision doc`).
- A PR closes one or more APs.
- An AP is **Done** only when its Acceptance Criteria are met **and** documentation is updated **and**
  trackers are current (**and** tests pass, from Phase 3 onward). See
  [Definition of Done](../../CONTRIBUTING.md#definition-of-done).

## Tracking

The live rollup lives in [`project/tracking/ap-index.md`](../../project/tracking/ap-index.md).
Every status transition updates that table and the AP's own Status/Log.
