---
id: AP-0050
title: Powered live study + claims update
phase: milestone-3-powered-live-study
status: In progress
owner: maintainers
created: 2026-06-29
updated: 2026-06-29
depends_on: [AP-0048, AP-0049]
related_docs: [benchmarks/live_study.py, docs/research/claims-registry.md]
related_adrs: [ADR-0009]
---

## Objective

Run the non-batchable chain recovery study **powered**: more repetitions and both crash points, across the
available providers (OpenRouter / Groq / ZenMux), to move C1 from *suggestive* (M2) toward *confirmed* — or
to honestly record that it is not yet confirmed. Targets C1 (and C3 where wired); C2/C4/C5 remain
reference-harness for now.

## Scope

**In:** run `run_live_study` against Nemotron 3 Super (OpenRouter) and Groq/ZenMux free models with
`repeats > 2` and `steps=(2,3)`; record manifests + transcripts (secret-free); update the claims registry
with dated live evidence and the success-conditioned verdict; honest scope per ADR-0009.
**Out:** the go/no-go decision (AP-0051); paid/non-free tiers unless approved.

## Acceptance Criteria

- [ ] ≥1 provider/model completes a powered run (more repeats than M2, both crash points), crashes fire
- [ ] Manifests written, transcripts replayable offline, verified secret-free before commit
- [ ] Claims registry updated with dated live C1 (and C3 if wired) evidence + statistics, supporting or refuting
- [ ] Result honestly scoped; the strict `verdict_c1` (now success-conditioned) reported as SHOWN / NOT SHOWN

## Status / Log

- 2026-06-29 — In progress. Harness ready (AP-0048 fix + AP-0049 providers, suite green). Running live
  against the configured providers next.
