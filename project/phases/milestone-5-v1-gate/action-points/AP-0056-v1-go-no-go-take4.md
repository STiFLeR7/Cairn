---
id: AP-0056
title: v1.0 go/no-go, take 4
phase: milestone-5-v1-gate
status: Not started
owner: maintainers
created: 2026-10-19
updated: 2026-10-19
depends_on: [AP-0055]
related_docs: [docs/superpowers/specs/2026-10-19-m5-v1-gate-design.md, docs/research/claims-registry.md, ROADMAP.md]
related_adrs: [ADR-0009]
---

## Objective

Compute `verdict_v1_gate` from the recorded runs with the pre-registered code and decide v1.0.

## Scope

**In:** record the decision, per-model numbers and the strict `verdict_c1` alongside, in the claims
registry, ROADMAP, CHECKLIST, the M5 README and the v1.0-hold record. On GO, AP-0036/0037 move from
Blocked to "awaiting owner approval". On NO-GO or INCONCLUSIVE, record the gap and next input; the project
stays 0.x.
**Out:** any tag, release or announcement without explicit owner approval.

## Acceptance Criteria

- [ ] Recorded, evidence-cited go/no-go decision
- [ ] Trackers and the v1.0-hold record updated
- [ ] Result published whichever way it falls (ADR-0009)
