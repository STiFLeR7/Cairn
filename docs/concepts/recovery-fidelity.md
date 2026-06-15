---
title: Recovery Fidelity (Metric Definition)
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0008]
related_adrs: [ADR-0001]
---

# Recovery Fidelity

This document defines what it means for recovery to be *good*. It is the measurable counterpart to
[continuation sufficiency](problem-formalization.md): sufficiency says recovery must reach an equivalent
*outcome*; fidelity says how we *measure* that equivalence. The metric is defined here (conceptually);
its implementation, datasets, and the failure-injection harness are Phase 5
(`AP-0028`–`AP-0033`).

## 1. Why outcome equivalence, not trajectory equivalence

Classical recovery can check "did we restore the exact state?" because replay is deterministic. Agents
cannot: execution is non-deterministic, so a correctly-resumed agent will generally take a *different*
path than the uninterrupted run (see [problem-formalization.md](problem-formalization.md), Assumption 2).
Demanding identical trajectories would mark correct recoveries as failures.

> **Recovery fidelity** measures how close a resumed run's **outcome** is to the **uninterrupted run's
> outcome** for the same task and the same failure-free goal — not how close their paths are.

The reference is always the **uninterrupted run**: the same agent, same task, no failure injected. A
recovery scores well to the extent it lands where the uninterrupted run would have, at acceptable cost,
without harming the world.

## 2. The five axes

| Axis | Question | Direction | Notes |
|---|---|---|---|
| **Task success** | Did the resumed run complete the task? | higher better | Binary or graded against the task's own success check (e.g. tests pass, goal met). |
| **Solution quality** | Is the result as good as the uninterrupted run's? | higher better | Graded vs the uninterrupted baseline (test pass-rate, correctness, or judged quality). Separated from success because a run can "finish" with a worse solution. |
| **No-regression** | Did recovery preserve already-completed work? | higher better | Penalizes undoing/corrupting work that was done before the failure. A resume that discards prior progress can still "succeed" but with low fidelity. |
| **Effect-safety** | Were any irreversible effects duplicated or spuriously fired on resume? | lower better (ideal 0) | Counts duplicate/erroneous external effects. This is a *safety* axis: a single duplicated payment is a serious failure regardless of task success. See [tool-effect-taxonomy.md](tool-effect-taxonomy.md). |
| **Recovery tax** | How much extra cost did recovery impose? | lower better | Extra tokens / wall-clock / dollars to return to productive work versus the uninterrupted run — the "time-to-re-productivity". Includes steady-state checkpointing overhead. |

An **ideal recovery** scores: task success = uninterrupted, solution quality ≈ uninterrupted,
no-regression = full, effect-safety = 0 duplicates, recovery tax = small and bounded.

These axes are not collapsed into a single scalar by default. Effect-safety in particular is a **gate**,
not a tradeable term: a duplicated irreversible effect is not "bought back" by higher task success.

## 3. Baselines (what fidelity is measured against)

Fidelity is comparative. Phase 5 evaluates Re-grounding Recovery (RGR) against:

| ID | Baseline | Description |
|---|---|---|
| **B0** | Cold restart | Start the task over from `k₀`. The current default in most systems. |
| **B1** | Full-log replay | Re-feed the entire recorded trajectory to rebuild context. Breaks under non-determinism. |
| **B2** | Snapshot-only | Restore a Runtime workspace/context snapshot with a fresh model context; no semantic re-grounding. |
| **B3** | **RGR (proposed)** | Re-grounding from the Continuation State + effect ledger + re-observation. |

The claims that these comparisons test are registered in
[`../research/claims-registry.md`](../research/claims-registry.md) (e.g. C1: RGR > B0 on fidelity).

## 4. The sufficiency ablation

Because the Continuation State is the compressed `S` from
[problem-formalization.md](problem-formalization.md), fidelity gives us a way to *empirically identify
the sufficient statistic*: strip components of `S` (drop ruled-out dead-ends, drop decision rationale,
drop verification state, …) and measure where fidelity collapses. The component whose removal breaks
recovery was necessary; the rest was slack. This **ablation** (Phase 5, `AP-0031`) turns "what should be
checkpointed?" from an assertion into a measurement.

## 5. Forward map to Phase 5

| Axis | How Phase 5 will measure it |
|---|---|
| Task success | Task's own success oracle on the resumed run |
| Solution quality | Graded comparison to the uninterrupted run (oracle or LLM-judge) |
| No-regression | Diff of completed-work artifacts pre-failure vs post-resume |
| Effect-safety | Count of duplicate/spurious entries vs the effect ledger ground truth |
| Recovery tax | Tokens / wall-clock / cost from failure to re-productivity, + steady-state checkpoint overhead |

Failure is injected across step index `k` and failure *type* (crash, context overflow, tool timeout,
OOM, model error); see `AP-0028`.

## Summary

Recovery fidelity is **outcome equivalence to the uninterrupted run**, measured on five axes — task
success, solution quality, no-regression, effect-safety (a hard gate), and recovery tax — against four
baselines (cold restart, log-replay, snapshot-only, RGR). It is defined here and measured in Phase 5,
and it doubles as the instrument that empirically identifies the minimal sufficient Continuation State.
