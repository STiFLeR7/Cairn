# Phase Tracking

> Live phase status board. Canonical goals/criteria: [ROADMAP.md](../../ROADMAP.md).
> Last updated: 2026-06-15.

| Phase | Name | Status | APs (done / total) |
|---|---|---|---|
| 0 | Project Definition | 🟢 Complete | 6 / 6 |
| 1 | Conceptual & Research Foundation | 🟢 Complete (merged) | 6 / 6 |
| 2 | Architecture & Protocol Design | 🟢 Complete (merged) | 6 / 6 |
| 3 | Minimal Harness | 🟢 Complete (merged) | 4 / 4 |
| 4 | Recovery v1 (three pillars) | 🟢 Complete (merged) | 5 / 5 |
| 5 | Evaluation & Benchmark | 🟢 Complete (branch) | 6 / 6 |
| 6 | Paper & Release | ⬜ Not started | 0 / 4 |

**Legend:** ⬜ Not started · 🟡 In Progress · 🟢 Complete · 🔴 Blocked

## Current phase: 5 — Evaluation & Benchmark (complete on branch) → Phase 6 next

All six APs (AP-0028 … AP-0033) `Done` on branch `phase-5-evaluation` (2026-06-15). `pytest -q` →
**42 passed**; `benchmarks/recovery_matrix.py`, `ablation_study.py`, `cross_version_resume.py` run
end-to-end. Evidence (deterministic reference harness, ADR-0009): **C1 supported** (B3 tax 1.5 vs B0 5.0,
no-regression 1.0 vs 0.0), **C3 supported** (B3 0 duplicates / gate PASS vs B0 1 / gate FAIL), **C5
supported** (ablation: `plan` is the cliff, rest is slack), **C2 evidenced**, **C4 mechanism shown**
(provenance A→B). Claims registry updated with dated, scoped notes. Awaiting review + merge. See
[`project/phases/phase-5-evaluation/README.md`](../phases/phase-5-evaluation/README.md).
Phases 0–4 complete and **merged** (PR #1–#4). **Next: Phase 6 — Paper & Release.**

## Prior phase: 4 — Recovery v1 (complete & merged)

All five APs (AP-0023 … AP-0027) `Done` and **merged to `master`** via PR #4 (2026-06-15, merge commit
`b008a4f`). `pytest -q` → **33 passed**; `examples/recovery_demo.py` shows crash→resume with
**recovery_tax=1** (vs cold-restart 3) and the effect resolved exactly once. Implements the three recovery
pillars: unified distillation (ADR-0005 / C2), re-grounding resume (ADR-0004), effect-safety WAL
(ADR-0006 / C3), proven end-to-end (C1); ADR-0008 records the implementation decisions (incl. §7:
v1 is restore-first, torn-detection reserved). A PR-review debugging pass fixed a `reconcile` substring
false-match. See [`project/phases/phase-4-recovery-v1/README.md`](../phases/phase-4-recovery-v1/README.md).
Phases 0–3 also complete and **merged** (PR #1, #2, #3). **Next: Phase 5 — Evaluation & Benchmark.**
