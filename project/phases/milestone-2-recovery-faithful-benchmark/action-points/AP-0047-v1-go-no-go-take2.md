---
id: AP-0047
title: v1.0 go/no-go, take 2
phase: milestone-2-recovery-faithful-benchmark
status: Done
owner: maintainers
created: 2026-06-16
updated: 2026-06-23
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

- [x] A dated go/no-go take-2 record exists, citing the M2 live C1–C5 verdicts + statistics
- [x] On "go": AP-0036/0037 unblocked and drafts refreshed; outward actions still flagged pending approval
      — N/A this take (outcome is no-go).
- [x] On "no-go": shortfall + next steps recorded; project remains 0.x
- [x] No tag cut, no release published, no announcement posted by this AP — the v1.0 release tag (AP-0036)
      stays gated; the separate **v0.2.0 milestone tag** marking M2 is a 0.x dev tag, not the v1.0 release.
- [x] ROADMAP + trackers reflect the decision

## Decision (2026-06-23) — **NO-GO for v1.0; project stays 0.x**

On the M2 live evidence (AP-0046, `nvidia/nemotron-3-super-120b-a12b:free`, 2026-06-23):

**What improved vs the M1 NO-GO (AP-0042).** M1 could not exercise recovery at all — the batchable task let
the model finish before the crash. M2 fixed that: on the **non-batchable chain** the injected crash **fired
in all 4 cells**, and a real model drove genuine sequential recovery. The benchmark is now
**recovery-faithful**, the metrics are **work-unit / granularity-robust**, and the harness reports **repetition
statistics** with vacuous cells skipped. The live evidence **leans in favor of C1**: RGR completed 2/2 with a
consistent low tax (1.0±0.0) while cold restart completed only 1/2 (tax 2.5±2.5).

**Why still no-go.** The evidence is **suggestive, not a confirmation**:
- **Underpowered** — n=2 repetitions, a single crash point (k=2), a single model. The strict `verdict_c1` is
  **NOT SHOWN** (B0's failed repeat has recovery_tax 0 — a non-recovery — overlapping B3).
- **Incomplete claim coverage** — only C1 has live (M2) evidence; **C2/C4/C5 remain reference-harness** and
  **C3 (effect-safety) was not wired** into the live chain run.
- **A powered run is blocked** — the OpenRouter free tier rate-limited (HTTP 429) before a larger sample could
  be collected, and the raw transcript of the n=2 run was lost to a (now-fixed) truncation footgun.

Calling v1.0 on this would overclaim. **Decision: NO-GO.** The project **remains 0.x**; AP-0036 (v1.0 release)
and AP-0037 (announcement) **stay `Blocked`**.

**However, M2 is a real milestone shipped.** It is released as **v0.2.0** (a 0.x dev tag marking "recovery-faithful
live benchmark + first genuine live recovery evidence") — explicitly **not** the held v1.0 release.

**Next-milestone input (the v1.0 gate).** A **powered** live study: ≥1 instruction-reliable model on a
non-free / higher-rate-limit tier; more repetitions and both crash points; wire C3 (effect-safety) and seek
live C2/C4/C5 evidence; a success-conditioned tax comparison so a failed baseline run can't masquerade as a
cheap recovery in the verdict.

## Dependencies

- `AP-0046` (M2 live verdicts feed the decision)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M2 entry).
- 2026-06-23 — Done. **NO-GO for v1.0** recorded (above); project stays 0.x, AP-0036/0037 stay `Blocked`.
  M2 shipped as **v0.2.0** (0.x milestone tag, not the v1.0 release). Supersedes the M1 NO-GO (AP-0042) with
  materially stronger evidence. ROADMAP/CHECKLIST/ap-index/phase-tracking/CHANGELOG updated.
