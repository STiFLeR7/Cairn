---
id: AP-0047
title: v1.0 go/no-go, take 2
phase: milestone-2-recovery-faithful-benchmark
status: Accepted
owner: maintainers
created: 2026-06-16
updated: 2026-06-16
depends_on: [AP-0046]
related_docs: [docs/release/RELEASE_NOTES_v1.0.0.md, ANNOUNCEMENT.md, ROADMAP.md]
related_adrs: [ADR-0009]
---

## Objective

Re-make the **v1.0 go/no-go decision** on the M2 live evidence (AP-0046) — the first run able to actually
exercise recovery against a real model. On "go", unblock the deferred release (AP-0036) and announcement
(AP-0037), which still proceed only on **explicit human approval** for the outward steps. On "no-go", record
the gap and the next milestone input. This supersedes the M1 NO-GO (AP-0042) with stronger evidence.

## Scope

**In:** a dated go/no-go record citing the M2 live verdicts with statistics; on "go" — moving AP-0036/0037
out of `Blocked` and refreshing their drafts (`RELEASE_NOTES_v1.0.0.md`, `ANNOUNCEMENT.md`, `CITATION.cff`)
against the live results; on "no-go" — the shortfall + follow-up. ROADMAP/tracker updates.
**Out:** actually cutting the tag/release or posting the announcement — those remain the **gated**
AP-0036/0037 steps requiring explicit go-ahead even after a "go"; this AP only authorizes them.

## Acceptance Criteria

- [ ] A dated go/no-go take-2 record exists, citing the M2 live C1–C5 verdicts + statistics
- [ ] On "go": AP-0036/0037 unblocked and drafts refreshed; outward actions still flagged pending approval
- [ ] On "no-go": shortfall + next steps recorded; project remains 0.x
- [ ] No tag cut, no release published, no announcement posted by this AP
- [ ] ROADMAP + trackers reflect the decision

## Dependencies

- `AP-0046` (M2 live verdicts feed the decision)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M2 entry).
