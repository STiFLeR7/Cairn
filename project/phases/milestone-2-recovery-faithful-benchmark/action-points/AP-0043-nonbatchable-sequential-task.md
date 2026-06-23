---
id: AP-0043
title: Non-batchable sequential benchmark task
phase: milestone-2-recovery-faithful-benchmark
status: Done
owner: maintainers
created: 2026-06-16
updated: 2026-06-23
depends_on: []
related_docs: [benchmarks/scenarios.py, src/cairn/task.py, docs/research/claims-registry.md]
related_adrs: [ADR-0007, ADR-0009]
---

## Objective

Design and implement a benchmark task that a capable real model **cannot one-shot** — so a crash injected at
step `k` genuinely destroys partial, expensive-to-redo progress and recovery actually matters. This is the
root fix for the M1 NO-GO: the multi-file task was batchable (the model created all files in one action and
finished before the crash), so C1 could not be tested.

## Scope

**In:** a task whose step `N+1` depends on a value that only becomes available *after* step `N` runs — e.g.
a **stateful tool** (or reactively-generated breadcrumb) that, given the correct previous result, returns the
next required input. Because the next input is not knowable until the prior step executes, the model must
take one observable step at a time; a single batched action cannot complete it. A crash mid-sequence leaves a
real partial state the cairn must re-ground from. Provide it as an injected `Task` (+ tool) usable by both the
deterministic harness (scripted mock that follows the chain) and the live pipeline.
**Out:** the metrics redesign (AP-0044); repetition/statistics (AP-0045); the live run (AP-0046). The task
must not hardcode a model (ADR-0007).

## Deliverables

- A `Task` (+ supporting stateful tool/breadcrumb mechanism) that forces sequential, non-batchable steps.
- A deterministic scripted-mock driver for it (so the existing offline benchmark/tests can use it).
- A test proving **batching is impossible**: a one-shot attempt (create-everything-at-once) does **not**
  complete the task, while a correct step-by-step run does.

## Acceptance Criteria

- [x] Step `N+1`'s required input is unavailable until step `N` has run (verified: a batched one-shot fails)
- [x] A correct sequential run completes the task; a crash at step `k` leaves genuine partial progress
- [x] Works behind the existing `Task`/harness seams with both the scripted mock and `LiveModelProvider`
- [x] No hardcoded harness (ADR-0007); test + docs added

## Dependencies

- none (builds on the merged M1 harness)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M2 entry).
- 2026-06-23 — Done. Built the **chain-oracle** primitive `src/cairn/eval/chain.py` (`Chain` +
  `render_oracle_module`): a salted hash-chain that `advance()`s **at most once per process**.
  Because the harness runs each agent step in a fresh `python -c` subprocess, completing a
  length-`n` chain needs `n` separate steps — a single batched action cannot finish it, and a
  crash at step `k` leaves a real partial chain (`pos == k`). The planted `oracle` module is
  self-contained (stdlib + ASCII only) since the subprocess has no `cairn` on its path; the
  in-process `Chain.is_complete` mirrors the same salted transform, so a completing run is the
  agreement check. Added a generic, default-no-op `Task.setup(workspace)` hook (called by the
  harness on every run/resume/continue, and by B1 after its wipe) so a task can re-establish
  its *environment* (the oracle) on each recovery while the agent's *progress* stays the thing
  recovery restores. Concrete `ChainTask` + `chain_scenario` + live wiring
  (`fake_chain_transport`, `batching_chain_transport`, `live_chain_scenario`) added in
  `benchmarks/scenarios.py` (no model hardcoded; salt is deterministic — ADR-0007/0009).
  Tests: `tests/test_eval_chain.py` (8) prove the per-process guard, batching-impossible
  (one-shot leaves `pos == 1`, stays incomplete) vs. a completing step-by-step run, a fired
  crash leaving genuine partial progress, and B3 (RGR) recovering with lower `recovery_tax` and
  higher `no_regression` than B0 (cold restart). Full suite **88 passed** (80 → 88).
