---
id: AP-0054
title: "Pre-registration: freeze protocol + verdict code before any live call"
phase: milestone-5-v1-gate
status: In progress
owner: maintainers
created: 2026-10-19
updated: 2026-10-19
depends_on: [AP-0052, AP-0053]
related_docs: [docs/superpowers/specs/2026-10-19-m5-v1-gate-design.md, results/m5/protocol.json, benchmarks/m5_preregister.py]
related_adrs: [ADR-0009]
---

## Objective

Fix the protocol and verdict code before any live data exists, so the GO / NO-GO / INCONCLUSIVE outcome
cannot be tuned after the fact.

## Scope

**In:** `results/m5/protocol.json` (models, R_cal, eligibility, n, crash steps, repeats, baselines,
effect, all thresholds, loss threshold); `benchmarks/m5_preregister.py` (`snapshot`,
`write_preregistration`, `verify`) hashing every `src/cairn/**/*.py` and `benchmarks/*.py` file plus `results/m5/protocol.json` with SHA-256 (a file added after the freeze is also reported);
the guard in `m5_study.py`. The freeze (`python benchmarks/m5_preregister.py write`) is committed and
pushed before AP-0055 starts. Thresholds are never changed after live data is seen; a change needs a new
pre-registration and invalidates earlier live data for the gate.
**Out:** the live run.

## Acceptance Criteria

- [x] `protocol.json` written with the spec values
- [x] `verify` names every missing or mismatching file; line-ending churn counts as a change (tested)
- [ ] `results/m5/preregistration.json` written, committed and pushed

## Status / Log

- 2026-10-19 — In progress. Tooling, protocol and guard done; freeze pending.
