# Phase Tracking

> Live phase status board. Canonical goals/criteria: [ROADMAP.md](../../ROADMAP.md).
> Last updated: 2026-06-16.

| Phase | Name | Status | APs (done / total) |
|---|---|---|---|
| 0 | Project Definition | 🟢 Complete | 6 / 6 |
| 1 | Conceptual & Research Foundation | 🟢 Complete (merged) | 6 / 6 |
| 2 | Architecture & Protocol Design | 🟢 Complete (merged) | 6 / 6 |
| 3 | Minimal Harness | 🟢 Complete (merged) | 4 / 4 |
| 4 | Recovery v1 (three pillars) | 🟢 Complete (merged) | 5 / 5 |
| 5 | Evaluation & Benchmark | 🟢 Complete (merged) | 6 / 6 |
| 6 | Paper & Release | 🟢 Core done (release deferred to M1) | 2 / 4 |
| M1 | Live-LLM Validation | 🟡 In Progress (entered) | 0 / 5 |

**Legend:** ⬜ Not started · 🟡 In Progress · 🟢 Complete · 🔴 Blocked

## Current milestone: M1 — Live-LLM Validation (entered 2026-06-16)

Entered on branch `milestone-1-live-llm-validation` (master stays clean per branch-per-phase). Goal: replace
the deterministic scripted mock with **real LLM `ModelProvider`s** (injected, no hardcoding — ADR-0007),
re-run the Phase 5 failure-injection benchmark **live**, and re-evaluate C1–C5 under genuine non-determinism.
Five APs (AP-0038 … AP-0042) committed and `Accepted`; an integration ADR (**ADR-0010**) is authored when
AP-0038 starts. On a "go" decision (AP-0042) this unblocks the deferred v1.0 release + announcement
(AP-0036/0037), still pending explicit approval. See
[`project/phases/milestone-1-live-llm-validation/README.md`](../phases/milestone-1-live-llm-validation/README.md).

## Prior phase: 6 — Paper & Release (core done; release deferred to M1)

**AP-0034 (`PAPER.md`) and AP-0035 (`REPRODUCE.md` + `Makefile`) are `Done` and merged** via PR #6
(merge commit `0e36f25`); 42 tests + demo + benchmarks reproduce. **Decision (2026-06-15): hold the v1.0
release and the public announcement** — keep the project at **0.x** until a live-LLM study validates the
claims (current evidence is reference-harness only, ADR-0009). AP-0036/0037 are `Blocked` (a deliberate
hold, not an impediment); their drafts (`docs/release/RELEASE_NOTES_v1.0.0.md`, `ANNOUNCEMENT.md`) stay
ready for a future **v1.0 milestone**. See
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
