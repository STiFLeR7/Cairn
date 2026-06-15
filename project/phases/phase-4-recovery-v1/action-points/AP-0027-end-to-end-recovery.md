---
id: AP-0027
title: End-to-end recovery from injected failure
phase: phase-4-recovery-v1
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0025, AP-0026]
related_docs: [docs/design/resume-protocol.md, docs/concepts/recovery-fidelity.md, docs/research/claims-registry.md]
related_adrs: [ADR-0004, ADR-0006, ADR-0008]
---

## Objective

Tie the three pillars together with an **end-to-end recovery from an injected failure**: run a multi-step
task that performs a tracked effect, inject a crash mid-run (between a checkpoint and an effect's
COMPLETE), construct a **fresh runtime** over the same `base_dir`, `resume`, and demonstrate the task
completes with **no duplicate effect** and a measured **recovery tax**. This is the first concrete
demonstration of claim **C1** (the recovery harness exists and works) and exercises C2/C3 together.

## Scope

**In:** a generic, injected failure point — a `step_hook(step)` lifecycle callback on the agent loop that a
test wires to raise `InjectedFailure` after step *k* (no test-specific crash flag baked into the library);
a small multi-step recovery task that writes files **and** performs a `check-before-retry` effect; an
end-to-end test (crash → fresh runtime → resume → assertions); a recovery-tax measurement
(steps/checkpoints after resume vs a cold restart).
**Out:** the full failure-injection *matrix* and baseline comparisons (that is Phase 5); statistical eval.

## Deliverables

- `src/cairn/harness/agent_loop.py` — optional `step_hook` lifecycle callback (generic, injected).
- `src/cairn/harness/failure.py` — `InjectedFailure` + a tiny `crash_after(k)` hook factory (test/util).
- `examples/recovery_demo.py` — runnable crash-then-resume demonstration.
- `tests/test_recovery_e2e.py` — crash mid-run, resume in a fresh runtime, assert completion + no-dup + tax.

## Acceptance Criteria

- [x] A task that crashed after step *k* completes after `resume` in a freshly-constructed runtime (C1)
- [x] The tracked effect appears **exactly once** despite the crash in its danger window (C3)
- [x] Recovery does not restart from scratch — recovery tax (post-resume steps) < cold-restart steps
- [x] The failure point is injected generically (`step_hook`), not hardcoded into the harness (ADR-0007)
- [x] `examples/recovery_demo.py` runs end-to-end; full `pytest` suite green
- [x] Documentation updated; CHANGELOG + trackers updated; Phase 4 completion criteria met

## Dependencies

- AP-0025 (resume), AP-0026 (effect-safety)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 4 entry).
- 2026-06-15 — Accepted → Done. Delivered `step_hook` + `failure.py` + `examples/recovery_demo.py` + `tests/test_recovery_e2e.py`; end-to-end recovery (C1+C3) green, recovery_tax=1 vs cold-restart 3.
