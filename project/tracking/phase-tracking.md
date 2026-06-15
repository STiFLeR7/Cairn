# Phase Tracking

> Live phase status board. Canonical goals/criteria: [ROADMAP.md](../../ROADMAP.md).
> Last updated: 2026-06-15.

| Phase | Name | Status | APs (done / total) |
|---|---|---|---|
| 0 | Project Definition | 🟢 Complete | 6 / 6 |
| 1 | Conceptual & Research Foundation | 🟢 Complete (merged) | 6 / 6 |
| 2 | Architecture & Protocol Design | 🟢 Complete (merged) | 6 / 6 |
| 3 | Minimal Harness | 🟢 Complete (merged) | 4 / 4 |
| 4 | Recovery v1 (three pillars) | ⬜ Not started | 0 / 5 |
| 5 | Evaluation & Benchmark | ⬜ Not started | 0 / 6 |
| 6 | Paper & Release | ⬜ Not started | 0 / 4 |

**Legend:** ⬜ Not started · 🟡 In Progress · 🟢 Complete · 🔴 Blocked

## Current phase: 3 — Minimal Harness (complete & merged) → Phase 4 next

All four APs (AP-0019/0020/0021/0022) `Done` and **merged to `master`** via PR #3 (2026-06-15, merge
commit `ea658e2`). `pytest -q` → 13 passed; quickstart runs end-to-end. No hardcoded harness (ADR-0007).
See [`project/phases/phase-3-minimal-harness/README.md`](../phases/phase-3-minimal-harness/README.md).
Phases 1 & 2 also complete and **merged** (PR #1, #2). **Next: Phase 4 — Recovery v1** (AP-0023 … AP-0027).
