# Phase Tracking

> Live phase status board. Canonical goals/criteria: [ROADMAP.md](../../ROADMAP.md).
> Last updated: 2026-06-15.

| Phase | Name | Status | APs (done / total) |
|---|---|---|---|
| 0 | Project Definition | 🟢 Complete | 6 / 6 |
| 1 | Conceptual & Research Foundation | 🟢 Complete (merged) | 6 / 6 |
| 2 | Architecture & Protocol Design | 🟢 Complete (merged) | 6 / 6 |
| 3 | Minimal Harness | 🟡 In Progress | 0 / 4 |
| 4 | Recovery v1 (three pillars) | ⬜ Not started | 0 / 5 |
| 5 | Evaluation & Benchmark | ⬜ Not started | 0 / 6 |
| 6 | Paper & Release | ⬜ Not started | 0 / 4 |

**Legend:** ⬜ Not started · 🟡 In Progress · 🟢 Complete · 🔴 Blocked

## Current phase: 3 — Minimal Harness

Entered 2026-06-15 on branch `phase-3-minimal-harness`; four APs (AP-0019/0020/0021/0022) refined and
committed (`Accepted`). Stack: Python, pluggable sandbox (local-subprocess default), pluggable model
provider (scriptable mock default); no hardcoded harness (ADR-0007). See
[`project/phases/phase-3-minimal-harness/README.md`](../phases/phase-3-minimal-harness/README.md).
Phases 1 & 2 complete and **merged** (PR #1, #2). **First code phase** — "tests pass" now part of DoD.
