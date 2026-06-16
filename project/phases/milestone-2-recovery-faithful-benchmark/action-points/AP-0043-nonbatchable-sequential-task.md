---
id: AP-0043
title: Non-batchable sequential benchmark task
phase: milestone-2-recovery-faithful-benchmark
status: Accepted
owner: maintainers
created: 2026-06-16
updated: 2026-06-16
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

- [ ] Step `N+1`'s required input is unavailable until step `N` has run (verified: a batched one-shot fails)
- [ ] A correct sequential run completes the task; a crash at step `k` leaves genuine partial progress
- [ ] Works behind the existing `Task`/harness seams with both the scripted mock and `LiveModelProvider`
- [ ] No hardcoded harness (ADR-0007); test + docs added

## Dependencies

- none (builds on the merged M1 harness)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M2 entry).
