---
id: AP-0051
title: v1.0 go/no-go, take 3
phase: milestone-3-powered-live-study
status: Blocked
owner: maintainers
created: 2026-06-29
updated: 2026-06-29
depends_on: [AP-0050]
related_docs: [docs/research/claims-registry.md, ROADMAP.md, project/phases/phase-6-paper-release]
related_adrs: [ADR-0009]
---

## Objective

Re-decide v1.0 on the M3 powered evidence. On "go", unblock AP-0036 (v1.0 release) and AP-0037
(announcement) — still gated on explicit user approval. On "no-go", record the gap and the next input.

## Scope

**In:** read the AP-0050 manifests + claims registry; decide go/no-go against the v1.0 gate (powered live
study validates the claims); update version status, ROADMAP, and the `hold-v1-until-live-llm` record.
**Out:** the run (AP-0050); cutting any tag or posting any announcement without explicit approval.

## Acceptance Criteria

- [ ] A recorded, evidence-cited go/no-go decision
- [ ] On "go": AP-0036/0037 unblocked (still gated on explicit approval); release/announcement drafts current
- [ ] On "no-go": gap + next-milestone input recorded; project stays 0.x
- [ ] Trackers + the v1.0-hold memory updated to reflect the outcome

## Status / Log

- 2026-06-29 — Blocked on AP-0050 (the powered run must produce the evidence first).
