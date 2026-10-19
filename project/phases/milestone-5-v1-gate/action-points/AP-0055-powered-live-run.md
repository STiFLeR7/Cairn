---
id: AP-0055
title: Powered live run (Claude, Codex)
phase: milestone-5-v1-gate
status: Not started
owner: maintainers
created: 2026-10-19
updated: 2026-10-19
depends_on: [AP-0054]
related_docs: [docs/superpowers/specs/2026-10-19-m5-v1-gate-design.md, benchmarks/m5_study.py, results/m5/protocol.json]
related_adrs: [ADR-0009]
---

## Objective

Run the pre-registered study on Claude `sonnet` and the Codex default model.

## Scope

**In:** per model, 10 uncrashed calibration runs (stop for that model if ineligible, recorded); then the
chain study n=6, crash steps k in {2, 3}, B0 and B3, 8 repeats = 32 planned cells, each with the torn
`send-report` effect; transcript and manifest per model under `benchmarks/transcripts/`, including
transport errors and skipped cells. Estimated 1,500-2,500 CLI calls per model. Transport errors are
counted per cell, not retried silently; usage-cap exhaustion pauses the run and resumption is noted.
**Out:** any change to code or thresholds after the freeze.

## Acceptance Criteria

- [ ] Run refuses to start unless `verify` is clean
- [ ] Both models calibrated; ineligibility recorded if it occurs
- [ ] Study manifests and transcripts committed for both models
