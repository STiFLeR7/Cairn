---
id: AP-0037
title: Public positioning (README, announcement)
phase: phase-6-paper-release
status: Blocked
owner: maintainers
created: 2026-06-15
updated: 2026-06-15
depends_on: [AP-0036]
related_docs: [README.md, docs/vision/positioning.md]
related_adrs: [ADR-0009]
---

## Objective

Finalize the public-facing positioning — a polished README and a short announcement draft that present
Cairn honestly (a reference implementation + benchmark for recoverable agents; deterministic v1 evidence,
live-LLM study as future work). **Any external posting is gated on explicit approval.**

## Scope

**In:** README final polish (status, results, repro, citation, how-to-cite); an `ANNOUNCEMENT.md` draft
(what it is, the thesis, the headline results with scope, links). **Posting anywhere external happens only
on explicit approval.**
**Out:** paid promotion; social scheduling; anything that publishes without a human in the loop.

## Acceptance Criteria

- [x] README presents status, headline results (with honest scope), repro pointer, and citation
- [x] `ANNOUNCEMENT.md` drafted — accurate, non-overclaiming (ADR-0009)
- [ ] **Gate:** no external posting without explicit approval (recorded in the log)
- [x] Documentation + trackers updated

## Dependencies

- AP-0036 (release exists to point at)

## Status / Log

- 2026-06-15 — Proposed → Accepted (refined on Phase 6 entry). External posting gated on approval.
- 2026-06-15 — Prepared: `ANNOUNCEMENT.md` drafted (short + medium form, honest scope); README polished.
  **Remaining (gated on approval):** post the announcement externally.
- 2026-06-15 — **Decision: deferred.** Do not post the announcement; `ANNOUNCEMENT.md` stays an internal draft until the v1.0 milestone. Status → Blocked (deliberate hold).
