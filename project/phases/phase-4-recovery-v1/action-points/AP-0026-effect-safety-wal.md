---
id: AP-0026
title: Effect-safety WAL + idempotency enforcement
phase: phase-4-recovery-v1
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0025]
related_docs: [docs/design/effect-safety-protocol.md, docs/design/tool-recovery-policy.md, docs/concepts/tool-effect-taxonomy.md]
related_adrs: [ADR-0006, ADR-0008]
---

## Objective

Enforce **effect-safety** so a resumed agent never re-executes an irreversible effect. Provide the
write-ahead helper that wraps an effect as INTENT → execute → COMPLETE (invariant I1), and the resume-time
**danger-window resolution** that, for every `INTENT`-without-`COMPLETE` key, applies the policy for its
tool class. This is the mechanism behind claim **C3** (no duplicate effects for the two safe classes).

## Scope

**In:** tool-class constants (`safe-to-retry`, `check-before-retry`, `never-retry`); an `EffectfulTool`
(name, class, optional `verify` hook); `perform_effect(runtime, tool, key, run, *, step)` write-ahead
wrapper; `resolve_danger_window(records, tools, runtime) -> [Resolution]` applying per-class policy
(redo / verify-then-redo-or-skip+COMPLETE / escalate); an `EscalationRequired` signal for `never-retry`.
**Out:** real external side effects (v1 uses injected `run`/`verify` callables so effects are testable);
the tool *taxonomy doc* already exists (Phase 1) — this AP implements its policy.

## Deliverables

- `src/cairn/harness/effects.py` — tool classes, `EffectfulTool`, `perform_effect`,
  `resolve_danger_window`, `Resolution`, `EscalationRequired`.
- Reconcile (AP-0025) calls `resolve_danger_window` for the danger window it surfaces.
- Tests (claim C3): `check-before-retry` with verify=already-done → **skip, no duplicate**, COMPLETE
  written; `safe-to-retry` → redo; `never-retry` → escalation raised, no auto-retry.

## Acceptance Criteria

- [x] `perform_effect` writes INTENT durably before running and COMPLETE only after success (I1)
- [x] Danger window = exactly the `INTENT`-without-`COMPLETE` keys since the checkpoint offset
- [x] `check-before-retry`: an authoritative verify decides skip-vs-redo → **no duplicate effect** (C3)
- [x] `safe-to-retry` redoes; `never-retry` escalates and is **not** auto-retried
- [x] A COMPLETE is written after resolution so the key leaves the danger window
- [x] No hardcoded tools (classes/verify injected — ADR-0007); docs + ADR-0008 + trackers updated; tests pass

## Dependencies

- AP-0025 (reconcile surfaces the danger window this AP resolves)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 4 entry).
- 2026-06-15 — Accepted → Done. Delivered `harness/effects.py` (write-ahead + danger-window resolution); C3 skip/redo/escalate tests pass.
