---
id: AP-0039
title: Determinism, cost & reproducibility controls for live runs
phase: milestone-1-live-llm-validation
status: Accepted
owner: maintainers
created: 2026-06-16
updated: 2026-06-16
depends_on: [AP-0038]
related_docs: [REPRODUCE.md, docs/adr/ADR-0009-evaluation-framework.md]
related_adrs: [ADR-0009, ADR-0010]
---

## Objective

Make live-LLM runs **auditable, re-runnable, and bounded in cost**. A real model is non-deterministic and
metered, so a study against it needs seed/temperature handling, a response cache + transcript log (so a run
can be replayed and inspected without re-spending tokens), and budget/rate-limit guards that stop a run
before it runs away. These controls are what let live results meet the same reproducibility bar as the
deterministic benchmark.

## Scope

**In:** temperature/seed configuration surfaced through the run config; a transcript recorder that captures
every prompt/response (with the model + version) to disk; a replay cache keyed on prompt so a re-run reuses
recorded responses instead of calling the API; a budget guard (max calls / token ceiling) and basic
rate-limit/backoff handling; documentation of these controls in `REPRODUCE.md`.
**Out:** the live study itself (AP-0040); the provider adapter (AP-0038); statistical analysis of results
(AP-0041).

## Deliverables

- Run-config controls for temperature/seed, transcript path, cache mode, and budget ceiling.
- A transcript/replay-cache mechanism (record live; replay from cache) usable by the benchmark harness.
- `REPRODUCE.md` section documenting how to run live, how to replay from cached transcripts, and the
  cost/seed controls.

## Acceptance Criteria

- [ ] Live runs record full prompt/response transcripts (with model + version) to disk
- [ ] A recorded run can be **replayed deterministically from cache** with no network calls
- [ ] Temperature/seed are configurable; a budget ceiling halts a run before exceeding it
- [ ] `REPRODUCE.md` documents the live-run and replay paths and the cost controls
- [ ] No secrets in transcripts/logs; docs + trackers updated

## Dependencies

- `AP-0038` (a live provider must exist to record/replay)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M1 entry).
