---
id: AP-0042
title: v1.0 go/no-go gate (unblock AP-0036/0037 on success)
phase: milestone-1-live-llm-validation
status: Done
owner: maintainers
created: 2026-06-16
updated: 2026-06-16
depends_on: [AP-0041]
related_docs: [docs/research/claims-registry.md, docs/release/RELEASE_NOTES_v1.0.0.md, ANNOUNCEMENT.md, ROADMAP.md]
related_adrs: [ADR-0009]
---

## Objective

Make and record the **v1.0 go/no-go decision** on the strength of the live evidence (AP-0041). If the live
study supports the headline claims, this gate unblocks the deferred release (AP-0036) and announcement
(AP-0037) — which then proceed only on **explicit human approval** for the outward, irreversible steps. If
the evidence is insufficient or refuting, the project stays at 0.x and the gap becomes the next milestone's
input. This AP closes the loop opened by the Phase 6 hold decision.

## Scope

**In:** a written decision record (go / no-go) citing the AP-0041 live verdicts; on "go" — moving AP-0036
and AP-0037 from `Blocked` to actionable and refreshing their drafts (`RELEASE_NOTES_v1.0.0.md`,
`ANNOUNCEMENT.md`, `CITATION.cff`) against the live results; on "no-go" — recording what failed and the
follow-up. Updating ROADMAP/trackers to reflect the outcome.
**Out:** actually cutting the tag/GitHub release or posting the announcement — those remain the **gated**
AP-0036/0037 steps requiring explicit go-ahead even after a "go" here; this AP only authorizes them to
proceed, it does not perform them.

## Decision (2026-06-16): **NO-GO** for v1.0 — the project stays at **0.x**.

The first live run (AP-0040/0041) validated the live *pipeline* but did **not** validate the claims: the
real model batched the task into a single action and finished before the injected crash, so recovery was
never exercised and the Phase-5 metrics were ill-defined and unstable. C1–C5 remain **reference-harness-only**.
Shipping a "v1.0" on this evidence would overstate maturity — exactly what the hold exists to prevent.
AP-0036 (release) and AP-0037 (announcement) **stay `Blocked`**. **Next step / next milestone input:** a
benchmark task that forces **non-batchable sequential** steps (so a crash genuinely interrupts partial work),
metrics robust to a real model's action granularity, and repetitions with seeds + statistics.

## Acceptance Criteria

- [x] A dated go/no-go decision record exists, citing the live verdict (this section + claims registry)
- [x] On "no-go": the shortfall and next steps are recorded; the project **remains at 0.x**
- [x] AP-0036/0037 stay `Blocked` (not unblocked — the "go" condition was not met)
- [x] No tag cut, no release published, no announcement posted by this AP
- [x] ROADMAP + trackers reflect the decision; docs updated

## Dependencies

- `AP-0041` (live verdicts feed the decision)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M1 entry).
- 2026-06-16 — Accepted → Done. **Decision: NO-GO.** Live evidence insufficient/invalid for C1–C5; project
  stays 0.x; AP-0036/0037 remain `Blocked`. The hold from Phase 6 is *confirmed by evidence*, not just
  deferred. Recorded the concrete redesign needed before a future go/no-go.
