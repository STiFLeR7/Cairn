---
id: AP-0055
title: Powered live run (Claude, Codex)
phase: milestone-5-v1-gate
status: Done
owner: maintainers
created: 2026-10-19
updated: 2026-10-21
depends_on: [AP-0054]
related_docs: [docs/superpowers/specs/2026-10-19-m5-v1-gate-design.md, benchmarks/m5_study.py, results/m5/protocol.json]
related_adrs: [ADR-0009]
---

## Objective

Run the pre-registered study on Claude `sonnet` (effort low) and Codex `gpt-6-sol` (reasoning effort
medium, isolated Codex home).

## Scope

**In:** per model, 10 uncrashed calibration runs (stop for that model if ineligible, recorded); then the
chain study n=6, crash steps k in {2, 3}, B0 and B3, 8 repeats = 32 planned cells, each with the torn
`send-report` effect; transcript and manifest per model under `benchmarks/transcripts/`, including
transport errors and skipped cells. Estimated 1,500-2,500 CLI calls per model. Transport errors are
counted per cell, not retried silently; base-level calls and errors are recorded as `call_stats`. Each
calibration run and study repeat is a checkpointed unit in `results/m5/<label>.partial.jsonl`; two
consecutive errored units (e.g. a usage cap) pause the run, and `python benchmarks/m5_study.py <label>
--resume` reuses finished units, re-attempts errored or missing ones and reports earlier errors as
`resumed_errors`. Every record stores the preregistration digest and commit.
**Out:** any change to code or thresholds after the freeze.

## Acceptance Criteria

- [x] Run refuses to start unless `verify` is clean
- [x] Both models calibrated; ineligibility recorded if it occurs
- [x] Study manifests and transcripts committed for both models

## Status / Log

- 2026-10-21 — Done. Claude (`claude-sonnet-5-5`, [`claude.json`](../../../../results/m5/claude.json)) and Codex
  (`gpt-6-sol`, [`codex.json`](../../../../results/m5/codex.json)): calibration 10/10 each; 32/32 planned cells
  fired (B0 16, B3 16), 0 skipped, 0 lost; 520 calls, 0 errors each.
