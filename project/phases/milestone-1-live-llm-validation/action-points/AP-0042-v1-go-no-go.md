---
id: AP-0042
title: v1.0 go/no-go gate (unblock AP-0036/0037 on success)
phase: milestone-1-live-llm-validation
status: Accepted
owner: maintainers
created: 2026-06-16
updated: 2026-06-16
depends_on: [AP-0041]
related_docs: [docs/release/RELEASE_NOTES_v1.0.0.md, ANNOUNCEMENT.md, ROADMAP.md]
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

## Acceptance Criteria

- [ ] A dated go/no-go decision record exists, citing the live C1–C5 verdicts
- [ ] On "go": AP-0036/0037 are moved out of `Blocked` and their drafts refreshed against live results;
      the outward actions are still flagged **pending explicit approval**
- [ ] On "no-go": the shortfall and next steps are recorded; the project remains at 0.x
- [ ] No tag is cut, no release is published, and no announcement is posted by this AP
- [ ] ROADMAP + trackers reflect the decision; docs updated

## Dependencies

- `AP-0041` (live verdicts feed the decision)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M1 entry).
