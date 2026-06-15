# Phase Tracking

> Live phase status board. Canonical goals/criteria: [ROADMAP.md](../../ROADMAP.md).
> Last updated: 2026-06-15.

| Phase | Name | Status | APs (done / total) |
|---|---|---|---|
| 0 | Project Definition | 🟢 Complete | 6 / 6 |
| 1 | Conceptual & Research Foundation | 🟢 Complete (merged) | 6 / 6 |
| 2 | Architecture & Protocol Design | 🟢 Complete (merged) | 6 / 6 |
| 3 | Minimal Harness | 🟢 Complete (merged) | 4 / 4 |
| 4 | Recovery v1 (three pillars) | 🟡 In Progress | 0 / 5 |
| 5 | Evaluation & Benchmark | ⬜ Not started | 0 / 6 |
| 6 | Paper & Release | ⬜ Not started | 0 / 4 |

**Legend:** ⬜ Not started · 🟡 In Progress · 🟢 Complete · 🔴 Blocked

## Current phase: 4 — Recovery v1 (in progress)

Entered 2026-06-15 on branch `phase-4-recovery-v1`. Five APs (AP-0023 … AP-0027) refined to `Accepted`;
ADR-0008 records the implementation decisions. Implements the three recovery pillars from Phase 2:
unified distillation (ADR-0005 / C2), re-grounding resume (ADR-0004), effect-safety WAL (ADR-0006 / C3),
proven by end-to-end recovery from an injected failure (C1). See
[`project/phases/phase-4-recovery-v1/README.md`](../phases/phase-4-recovery-v1/README.md).
Phases 0–3 complete and **merged** (PR #1, #2, #3).
