---
id: AP-0035
title: Reproducibility package & artifact polish
phase: phase-6-paper-release
status: Done
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: []
related_docs: [docs/adr/ADR-0009-evaluation-framework.md]
related_adrs: [ADR-0007, ADR-0009]
---

## Objective

Make the repository reproducible by anyone: a documented, one-command path to run the test suite, the
recovery demo, and all three benchmarks from a fresh clone, so the paper's headline numbers regenerate
deterministically.

## Scope

**In:** a `REPRODUCE.md` guide (environment, install, commands, expected outputs); a small task runner
(`Makefile` or `scripts/`) wrapping `pytest`, the demo, and the benchmarks; verification that a clean run
reproduces the Phase 5 tables.
**Out:** CI configuration (optional later); containerization (optional later).

## Deliverables

- `REPRODUCE.md` — environment + commands + expected outputs.
- `Makefile` (or `scripts/repro.sh`) — `test`, `demo`, `bench` targets.

## Acceptance Criteria

- [x] A fresh clone runs the tests, the recovery demo, and the three benchmarks via documented commands
- [x] Expected outputs (test count, headline numbers) are documented and match a clean run
- [x] Determinism noted (scripted mock, no wall-clock/network) so results are stable (ADR-0009)
- [x] No hardcoded paths; works from the repo root cross-platform where feasible (ADR-0007)
- [x] Documentation + trackers updated; tests green

## Dependencies

- none

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 6 entry).
- 2026-06-15 — Accepted → Done. Delivered `REPRODUCE.md` + `Makefile`; added self-bootstrap to examples so `python examples/*.py` runs without PYTHONPATH; fixed Makefile PY var (Windows backslash-path env collision). Verified: 42 tests, demo, all benchmarks reproduce; make targets work.
