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
| 5 | Evaluation & Benchmark | 🟢 Complete (merged) | 6 / 6 |
| 6 | Paper & Release | 🟡 In Progress | 0 / 4 |

**Legend:** ⬜ Not started · 🟡 In Progress · 🟢 Complete · 🔴 Blocked

## Current phase: 6 — Paper & Release (in progress)

Entered 2026-06-15 on branch `phase-6-paper-release`. Four APs (AP-0034 … AP-0037) refined to `Accepted`.
AP-0034 (paper draft) and AP-0035 (reproducibility package) are internal and in progress; **AP-0036 (cut
v1.0 tag) and AP-0037 (public announcement) are outward actions gated on explicit human approval.** See
[`project/phases/phase-6-paper-release/README.md`](../phases/phase-6-paper-release/README.md).
Phases 0–5 complete and **merged** (PR #1–#5).

## Prior phase: 5 — Evaluation & Benchmark (complete & merged) → Phase 6 next

All six APs (AP-0028 … AP-0033) `Done` and **merged to `master`** via PR #5 (2026-06-15, merge commit
`d925e2b`). `pytest -q` → **42 passed**; `benchmarks/recovery_matrix.py`, `ablation_study.py`,
`cross_version_resume.py` run end-to-end. Evidence (deterministic reference harness, ADR-0009):
**C1 supported** (B3 tax 1.5 vs B0 5.0, no-regression 1.0 vs 0.0), **C3 supported** (B3 0 duplicates /
gate PASS vs B0 1 / gate FAIL), **C5 supported** (ablation: `plan` is the cliff, rest is slack),
**C2 evidenced**, **C4 mechanism shown** (provenance A→B). Claims registry updated with dated, scoped
notes. See [`project/phases/phase-5-evaluation/README.md`](../phases/phase-5-evaluation/README.md).
Phases 0–5 complete and **merged** (PR #1–#5). **Next: Phase 6 — Paper & Release.**

## Prior phase: 4 — Recovery v1 (complete & merged)

All five APs (AP-0023 … AP-0027) `Done` and **merged to `master`** via PR #4 (2026-06-15, merge commit
`b008a4f`). `pytest -q` → **33 passed**; `examples/recovery_demo.py` shows crash→resume with
**recovery_tax=1** (vs cold-restart 3) and the effect resolved exactly once. Implements the three recovery
pillars: unified distillation (ADR-0005 / C2), re-grounding resume (ADR-0004), effect-safety WAL
(ADR-0006 / C3), proven end-to-end (C1); ADR-0008 records the implementation decisions (incl. §7:
v1 is restore-first, torn-detection reserved). A PR-review debugging pass fixed a `reconcile` substring
false-match. See [`project/phases/phase-4-recovery-v1/README.md`](../phases/phase-4-recovery-v1/README.md).
Phases 0–3 also complete and **merged** (PR #1, #2, #3). **Next: Phase 5 — Evaluation & Benchmark.**
