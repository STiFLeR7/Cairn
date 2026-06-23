# Milestone M2 — Recovery-faithful live benchmark

- **Status:** 🟢 Complete *(2026-06-16 → 2026-06-23; branch `milestone-2-recovery-faithful-benchmark`;
  shipped **v0.2.0**; outcome **NO-GO for v1.0** — live C1 suggestive not confirmed, project stays 0.x)*
- **Outcome:** all five APs (AP-0043…AP-0047) `Done`. The live run on the non-batchable chain
  (`nvidia/nemotron-3-super-120b-a12b:free`) **fired the crash in every cell** — recovery was exercised
  against a real model for the first time. RGR (B3) recovered 2/2 with low tax (1.0±0.0); cold restart (B0)
  only 1/2. **v1.0 go/no-go take 2 → NO-GO**: the evidence *leans* toward C1 but is suggestive, not confirmed
  (n=2 underpowered; a powered run was rate-limited). v1.0 stays held; the gate is now a *powered* live study.
- **Goal:** Make the live benchmark **actually exercise recovery** against a capable real model. M1 proved
  the live pipeline works but could not validate C1–C5, because the multi-file task is *batchable* — a real
  model one-shots it and finishes before any injected crash, so recovery never happens (and, until the M1
  fix, vacuous cells were silently scored). M2 replaces that task with one that **forces non-batchable,
  sequential, crash-interruptible work**, adds metrics robust to a real model's action granularity, runs each
  cell with **repetitions + statistics**, then re-runs live and re-decides v1.0.

> **Why this milestone exists.** The M1 NO-GO was not a failure of RGR — it was a failure of the *benchmark
> task* to create a situation where recovery matters. A capable model that completes the task in one action
> has nothing to recover. C1 ("RGR beats cold restart") can only be tested when a crash genuinely destroys
> partial, expensive-to-redo progress. See the [claims registry](../../../docs/research/claims-registry.md)
> (2026-06-16) and `PAPER.md` §9.

## Goals

- **Non-batchable sequential task** (`AP-0043`) — a chained task where each step depends on a value that only
  becomes available *after* the previous step runs (a stateful tool / reactively-generated breadcrumb), so
  the model **cannot** precompute or batch it. A crash at step `k` leaves genuine partial progress.
- **Action-granularity-robust metrics** (`AP-0044`) — recovery fidelity measured in **work units / progress**
  against the reference, not in "one file per step", so the numbers hold whether a model takes one action or
  many. Keep the five axes; redefine `no_regression` / `recovery_tax` in progress terms.
- **Repetition + statistics harness** (`AP-0045`) — run each (k × baseline) cell **N times** across seeds;
  report mean ± spread; **enforce the M1 injection-fired check** (skip + report vacuous cells) so noise and
  vacuous cells are visible, not averaged into a false signal.
- **Live re-run + claims update** (`AP-0046`) — run the new task live against a real model; record dated
  **live** evidence for C1–C5 (supporting *or* refuting) with the repetition statistics (ADR-0009 honesty).
- **v1.0 go/no-go, take 2** (`AP-0047`) — re-decide on the M2 live evidence; on "go", unblock AP-0036/0037
  (still gated on explicit approval); on "no-go", record the gap and the next milestone input.

**Constraints:**
- **No hardcoded harness** (ADR-0007) — the new task/tool/metrics are injected like everything else.
- **Honest results** (ADR-0009) — negatives recorded, not buried; statistics reported with their spread.
- **Builds on M1** — reuses `cairn.model_live`, `cairn.live_controls`, and the injection-fired integrity fix.

## Action Points

| ID | Title | Status |
|---|---|---|
| [AP-0043](action-points/AP-0043-nonbatchable-sequential-task.md) | Non-batchable sequential benchmark task | Accepted |
| [AP-0044](action-points/AP-0044-action-granularity-metrics.md) | Action-granularity-robust recovery metrics | Accepted |
| [AP-0045](action-points/AP-0045-repetition-statistics-harness.md) | Repetition + statistics harness (injection-fired enforced) | Accepted |
| [AP-0046](action-points/AP-0046-live-rerun-claims-update.md) | Live re-run + claims update (C1–C5, with statistics) | Accepted |
| [AP-0047](action-points/AP-0047-v1-go-no-go-take2.md) | v1.0 go/no-go, take 2 | Accepted |

## Dependency order

```
AP-0043 (non-batchable task) ──→ AP-0044 (metrics) ──→ AP-0045 (repetition + stats) ──→ AP-0046 (live re-run + claims)
                                                                                              │
                                                                                              ▼
                                                                                   AP-0047 (v1.0 go/no-go take 2)
```

## Checklist

- [ ] A task a capable model **cannot** one-shot; a crash at step k leaves genuine partial progress (AP-0043)
- [ ] Recovery metrics measured in progress/work-units, robust to action granularity (AP-0044)
- [ ] Each cell run N times with seeds; mean ± spread reported; vacuous cells skipped + reported (AP-0045)
- [ ] Live re-run on a real model; C1–C5 carry dated live evidence with statistics (AP-0046, ADR-0009)
- [ ] Recorded v1.0 go/no-go take 2; AP-0036/0037 unblocked only on "go" **and** explicit approval (AP-0047)
- [ ] No hardcoded harness; docs + trackers updated; tests green

## Completion criteria

- [ ] The new task demonstrably resists batching (a one-shot attempt cannot complete it; verified by test)
- [ ] The benchmark exercises real recovery: with the injection-fired check, k-crash cells fire and are scored
- [ ] Live evidence for C1–C5 exists with repetition statistics, honestly scoped (supporting or refuting)
- [ ] A recorded v1.0 go/no-go take 2; the project's version status reflects the evidence
