---
id: AP-0018
title: Tool effect taxonomy → recovery-policy mapping
phase: phase-2-architecture-protocol
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0012, AP-0017]
related_docs: [docs/design/tool-recovery-policy.md]
related_adrs: [ADR-0006]
---

## Objective

Operationalize the [tool effect taxonomy](../../../docs/concepts/tool-effect-taxonomy.md): specify how a
tool is *declared* to a recovery class, the exact resume policy each class executes, and how tools are
wrapped/promoted (e.g. `never-retry` → `check-before-retry` by adding an idempotency key). This is the
bridge from the conceptual taxonomy to something the harness can enforce.

## Scope

**In:** the per-tool declaration (class + idempotency-key strategy + query/verify hook); the resume
policy table per class; promotion/wrapping rules; the default class for undeclared tools (conservative —
`never-retry` / escalate). Builds on the effect-safety protocol (AP-0017).
**Out:** the WAL mechanism itself (AP-0017); the tool *implementations* (Phase 3/4).

## Deliverables

- `docs/design/tool-recovery-policy.md` — declaration schema, per-class resume policy, promotion rules,
  conservative default.

## Acceptance Criteria

- [x] A tool-declaration schema (class + idempotency/verify hooks) is specified
- [x] The resume policy for each of the three classes is specified operationally
- [x] Promotion/wrapping rules (e.g. add idempotency key to lift a class) are defined
- [x] The conservative default for undeclared tools is specified
- [x] Consistent with AP-0017 and the tool-effect taxonomy
- [x] Documentation updated (single source of truth, front-matter current)
- [x] Trackers updated (`ap-index.md`, `phase-tracking.md`, `CHANGELOG.md`)

## Dependencies

- AP-0012 (taxonomy), AP-0017 (effect-safety protocol it parameterizes)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 2 entry).
- 2026-06-15 — Accepted → Done. Delivered `docs/design/tool-recovery-policy.md` (references ADR-0006).
