---
id: AP-0022
title: Baseline task suite (no recovery) + smoke tests
phase: phase-3-minimal-harness
status: Accepted
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0019, AP-0020]
related_docs: [docs/design/boundary-contract.md]
related_adrs: [ADR-0007]
---

## Objective

Prove the assembled harness works: at least one baseline `Task` the harness completes end-to-end, plus a
`pytest` smoke suite asserting the contract behaviours (effect-ledger append-only, checkpoint atomicity,
sandbox execution, agent-loop completion). From this AP on, "tests pass" is part of the Definition of
Done.

## Scope

**In:** a `Task` implementation (e.g. "create a file with required content" / "make a trivial test pass")
verified by a success oracle; assembly/config wiring (factory that injects runtime+harness+model+tools);
`tests/` smoke suite + a `README`/quickstart for running it.
**Out:** recovery / failure-injection tests (Phase 4/5); benchmark tasks (Phase 5).

## Deliverables

- `src/cairn/tasks/` — at least one baseline task + success oracle.
- `src/cairn/app.py` (or `factory.py`) — assembles components from config (no hardcoding).
- `tests/` — smoke tests; `README` quickstart.

## Acceptance Criteria

- [ ] At least one baseline task runs end-to-end and its success oracle passes
- [ ] Smoke tests cover: effect-ledger append-only/offsets, checkpoint atomicity, sandbox exec, loop completion
- [ ] `pytest` passes locally (evidence captured)
- [ ] Assembly is config-driven; swapping model/sandbox/task requires no harness edits (ADR-0007)
- [ ] Documentation updated (quickstart); trackers updated

## Dependencies

- AP-0019 (Runtime), AP-0020 (Code Harness)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 3 entry).
