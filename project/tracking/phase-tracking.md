# Phase Tracking

> Live phase status board. Canonical goals/criteria: [ROADMAP.md](../../ROADMAP.md).
> Last updated: 2026-06-23.

| Phase | Name | Status | APs (done / total) |
|---|---|---|---|
| 0 | Project Definition | 🟢 Complete | 6 / 6 |
| 1 | Conceptual & Research Foundation | 🟢 Complete (merged) | 6 / 6 |
| 2 | Architecture & Protocol Design | 🟢 Complete (merged) | 6 / 6 |
| 3 | Minimal Harness | 🟢 Complete (merged) | 4 / 4 |
| 4 | Recovery v1 (three pillars) | 🟢 Complete (merged) | 5 / 5 |
| 5 | Evaluation & Benchmark | 🟢 Complete (merged) | 6 / 6 |
| 6 | Paper & Release | 🟢 Core done (release deferred to M1) | 2 / 4 |
| M1 | Live-LLM Validation | 🟢 Complete & merged (outcome: **NO-GO**; stays 0.x) | 5 / 5 |
| M2 | Recovery-faithful live benchmark | 🟡 In Progress | 4 / 5 |

**Legend:** ⬜ Not started · 🟡 In Progress · 🟢 Complete · 🔴 Blocked

## Current milestone: M2 — Recovery-faithful live benchmark (entered 2026-06-16)

Entered on branch `milestone-2-recovery-faithful-benchmark` (master clean; M1 merged via PR #7, commit
`0e39b5c`). Goal: make the live benchmark **actually exercise recovery** — M1's NO-GO traced to a *batchable*
task that a real model one-shots before any crash. Five APs (AP-0043 … AP-0047) `Accepted`: a **non-batchable
sequential task** (step N+1's input unavailable until step N runs), **action-granularity-robust metrics**
(progress/work-units, not one-file-per-step), a **repetition + statistics harness** (carrying the M1
injection-fired check), a **live re-run** producing dated C1–C5 evidence with statistics, and a **v1.0
go/no-go take 2** (supersedes the M1 NO-GO). See
[`project/phases/milestone-2-recovery-faithful-benchmark/README.md`](../phases/milestone-2-recovery-faithful-benchmark/README.md).

**AP-0043 `Done` (2026-06-23):** the non-batchable task exists. A salted **chain oracle**
(`src/cairn/eval/chain.py`) advances at most once per fresh `python -c` step, so a length-`n`
chain needs `n` separate actions — a batched one-shot leaves `pos == 1` and stays incomplete,
while a step-by-step run completes and a crash at `k` leaves genuine partial progress. A
default-no-op `Task.setup(workspace)` hook lets a task re-plant its environment on each
recovery (the agent's progress stays what RGR restores). `ChainTask` + `chain_scenario` +
live-fake/batching transports wired in `benchmarks/scenarios.py`; `tests/test_eval_chain.py`
(8) prove batching-impossible and that B3/RGR recovers cheaper than B0/cold-restart. **88
tests** (80 → 88).

**AP-0044 `Done` (2026-06-23):** recovery metrics now measured in **work units**, not actions.
A `Task.progress(workspace)` oracle (chain `pos` / file count) feeds `no_regression` and
`recovery_tax`: `redone = max(0, recovery_units - (W - work_at_crash))`,
`no_regression = 1 - redone/work_at_crash`. Plumbed via `RunOutcome.work_units` +
`Injection.work_at_crash`; unitless tasks fall back to the old action/`k` form. The chain pins one
unit per action, so deterministic C1/C5 numbers are unchanged while the definition is now
granularity-robust (traced to the M1 finding in `recovery-fidelity.md` §2a). **90 tests** (88 → 90).

**AP-0045 `Done` (2026-06-23):** repetition + statistics. `run_repeated(..., repeats=N, before_repeat=)`
runs the matrix N times (each a full `run_matrix`, so the M1 injection-fired skip holds);
`aggregate_repeated` → per-baseline `AxisStat(mean, stdev, min, max, n)` + fired/skipped counts
(vacuous cells excluded → `{}`). `verdict_c1` is "supported" only with consistent, no-overlap
evidence and B3 success in every repeat. Offline repeated study on the non-batchable chain wired
into `live_study.py` (the exact machinery AP-0046 runs live). Hygiene fix: `world_digest` now
excludes Python bytecode caches (a `.pyc` from importing the planted oracle was dropping
solution_quality to 0.67 and risking spurious torn-write detection). **98 tests** (90 → 98).

**AP-0046 `Done` (2026-06-23):** the gated live run, **executed** against
`nvidia/nemotron-3-super-120b-a12b:free` (OpenRouter). **The injected crash fired in all 4 cells
(skipped=0) — the M1 blocker is resolved**; recovery was exercised against a real model for the first
time. At n=2: **B3/RGR 2/2 success, tax 1.0±0.0**; **B0/cold-restart 1/2, tax 2.5±2.5**. RGR dominates on
means + reliability, but the strict verdict is **NOT SHOWN** (B0's failed run has tax 0; n=2 underpowered)
→ recorded honestly as **C1 suggestive, not confirmed live**. Claims registry + PAPER §9 updated. Live-path
hardening: `retrying` control (backoff on transient 429/5xx), filesystem-safe slugs, record-to-`.partial`-then-
finalize. Partial deliverable: raw transcript lost to the (now-fixed) truncation footgun; manifest persisted;
a powered re-run is **rate-limited (HTTP 429)**. **103 tests** (98 → 103). Next: AP-0047 (v1.0 go/no-go take 2).

## Prior milestone: M1 — Live-LLM Validation (complete & merged 2026-06-16 — outcome NO-GO)

Ran on branch `milestone-1-live-llm-validation` (master stays clean per branch-per-phase). All five APs
(AP-0038 … AP-0042) `Done`: `src/cairn/model_live.py` (`LiveModelProvider` + injected `anthropic_transport`
/ stdlib `openrouter_transport`), `src/cairn/live_controls.py` (transcript / offline replay / budget),
`ADR-0010`, and the live-pipeline study runner (`benchmarks/live_study.py`, `make bench-live`). **76 tests**,
core free of model-id/key literals (ADR-0007). The live study **ran against a real model**
(`openrouter/owl-alpha` via OpenRouter, user-authorized). **Outcome — NO-GO:** the pipeline works, but the
model batches the task into one action and finishes before the injected crash, so the Phase-5
scenario/metrics do not validate C1–C5 — they stay **reference-harness-only** (claims registry, 2026-06-16).
The project **remains 0.x**; AP-0036/0037 stay `Blocked` (hold now *confirmed by evidence*). **Next-milestone
input:** a non-batchable sequential task + action-granularity-robust metrics + repetitions. See
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
