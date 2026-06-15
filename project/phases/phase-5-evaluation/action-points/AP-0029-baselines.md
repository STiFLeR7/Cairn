---
id: AP-0029
title: Baselines (cold restart, log-replay, snapshot-only, RGR)
phase: phase-5-evaluation
status: Accepted
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0028]
related_docs: [docs/concepts/recovery-fidelity.md, docs/design/resume-protocol.md]
related_adrs: [ADR-0007, ADR-0009]
---

## Objective

Implement the four recovery baselines behind a single `RecoveryStrategy` interface so the same failed
scenario can be recovered each way and compared: **B0** cold restart, **B1** full-log replay, **B2**
snapshot-only (restore workspace, no semantic re-grounding), **B3** RGR (the Phase 4 `resume`).

## Scope

**In:** a `RecoveryStrategy` protocol `recover(base_dir, scenario) -> RunResult`; B0 (fresh runtime, run
from scratch), B1 (re-feed the recorded action log in a fresh runtime, no re-grounding), B2 (restore the
latest snapshot then continue with a fresh model context — no `reconcile`, no effect-safety), B3
(`CodeHarness.resume`). A `no_wal` variant toggle for the C3 with-/without-WAL contrast.
**Out:** the metrics (AP-0030); the matrix orchestration (AP-0033).

## Deliverables

- `src/cairn/eval/baselines.py` — `RecoveryStrategy` + `ColdRestart`, `LogReplay`, `SnapshotOnly`, `RGR`.
- Tests: each strategy runs to completion on a simple scenario; B0 discards prior work while B3 preserves it.

## Acceptance Criteria

- [ ] All four baselines implement one interface and run the same failed scenario
- [ ] B0 starts over; B2 restores the workspace but does not re-ground; B3 re-grounds via the cairn
- [ ] A without-WAL contrast is available for the effect-safety claim (C3)
- [ ] No hardcoded harness — strategies parameterized by the injected scenario (ADR-0007)
- [ ] Documentation + trackers updated; unit tests pass

## Dependencies

- AP-0028 (scenarios + failed runs to recover)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 5 entry).
