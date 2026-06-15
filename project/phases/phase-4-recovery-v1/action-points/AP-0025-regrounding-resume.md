---
id: AP-0025
title: Re-grounding resume protocol implementation
phase: phase-4-recovery-v1
status: Accepted
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0023, AP-0024]
related_docs: [docs/design/resume-protocol.md, docs/design/boundary-contract.md]
related_adrs: [ADR-0004, ADR-0008]
---

## Objective

Implement the **Re-grounding Recovery (RGR)** protocol: after a failure, resume by **load → re-observe →
reconcile → re-plan → continue** rather than replaying the trajectory. This adds the `reconcile` seam
named in the boundary contract and a `CodeHarness.resume(task)` entry point that drives the five steps,
finishing the task from a restored cairn and the *actually observed* world.

## Scope

**In:** `observe_world(runtime, since_offset) -> ObservedWorld` (re-read workspace files + digest + effects
since offset); `reconcile(state, observed) -> ResumePlan` (detect torn writes via digest mismatch, plan
drift via `plan.status` vs world, and the effect danger window — delegating effect resolution to AP-0026);
`CodeHarness.resume(task)` (load_latest → restore_workspace → observe → reconcile → continue the loop to
completion). `reconcile` added to the `CodeHarness` protocol.
**Out:** the per-tool-class effect policy itself (AP-0026 supplies it; reconcile only surfaces the danger
window); LLM re-planning (the injected model handles "re-plan"; v1 continues via the same `ModelProvider`).

## Deliverables

- `src/cairn/harness/observe.py` — `ObservedWorld` + `observe_world(...)`.
- `src/cairn/harness/reconcile.py` — `ResumePlan` + `reconcile(state, observed)`.
- `src/cairn/harness/agent_loop.py` — `CodeHarness.resume(task)`; shared continue-loop with `run`.
- `src/cairn/contract.py` — `reconcile` added to the `CodeHarness` protocol.
- Tests: torn-write detection; plan-drift reconciliation; resume completes a task after a mid-run crash.

## Acceptance Criteria

- [ ] `resume` performs load → restore → re-observe **before** acting ("re-observe before re-act")
- [ ] `reconcile` detects torn writes (digest mismatch) and plan drift, and surfaces the danger window
- [ ] `resume(task)` completes a task that crashed mid-run (outcome equivalence, not replay)
- [ ] Re-planning may take a different valid path; the bar is outcome equivalence
- [ ] No hardcoded harness (ADR-0007); docs + ADR-0008 + trackers updated; tests pass

## Dependencies

- AP-0023 (digest in the cairn), AP-0024 (restorable snapshot after restart)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 4 entry).
