# Phase 5 — Evaluation & Benchmark

- **Status:** 🟡 In Progress *(entered 2026-06-15)*
- **Goal:** Turn the recovery-fidelity *definition* (Phase 1) into a runnable **benchmark** that
  *measures* recovery instead of asserting it: a failure-injection harness, the four baselines
  (B0–B3), the five fidelity axes, an ablation over the Continuation State, a cross-version resume
  experiment, and an aggregation that updates the **claims registry** with dated evidence.

## Goals

Phase 4 *demonstrated* recovery on one happy path. Phase 5 makes it *measurable and comparative*:

- **Failure-injection harness** (`AP-0028`) — run a task with a failure injected at step `k` of a given
  *type*, over the (step × type) matrix. Generic: task/model/failure-type injected (ADR-0007).
- **Baselines** (`AP-0029`) — B0 cold-restart, B1 log-replay, B2 snapshot-only, B3 RGR as pluggable
  recovery strategies behind one interface, so the same scenario runs through each.
- **Metrics** (`AP-0030`) — the five axes: task success, solution quality, no-regression, **effect-safety
  (a hard gate)**, recovery tax — measured against the **uninterrupted reference run**.
- **Continuation-State ablation** (`AP-0031`) — strip cairn components (ruled-out dead-ends, decisions,
  plan, digest) and measure where fidelity collapses → empirically identify the minimal sufficient `S`
  (claims **C2**, **C5**).
- **Cross-version resume** (`AP-0032`) — checkpoint under model version A, resume under B; show RGR holds
  where log-replay would not (claim **C4**).
- **Results aggregation** (`AP-0033`) — run the matrix, aggregate into a results table, and update the
  claims registry (C1/C3 supported, C2/C4/C5 evidence) with **honest scope** (deterministic reference
  harness, not a live-LLM study).

**Hard constraints:** *no hardcoded harness* (ADR-0007) — tasks, models, failure types, baselines, and
ablations are injected. **Honest results** (ADR-0009) — claim-status updates state plainly that v1
evidence is from the deterministic reference harness; a live-LLM empirical study is future work.

## Action Points

| ID | Title | Status |
|---|---|---|
| [AP-0028](action-points/AP-0028-failure-injection-harness.md) | Failure-injection harness (step × failure-type matrix) | Accepted |
| [AP-0029](action-points/AP-0029-baselines.md) | Baselines (cold restart, log-replay, snapshot-only, RGR) | Accepted |
| [AP-0030](action-points/AP-0030-metrics.md) | Metrics implementation (five fidelity axes) | Accepted |
| [AP-0031](action-points/AP-0031-ablation.md) | Continuation-State ablation study | Accepted |
| [AP-0032](action-points/AP-0032-cross-version-resume.md) | Cross-version resume experiment | Accepted |
| [AP-0033](action-points/AP-0033-results-aggregation.md) | Results aggregation & claims update | Accepted |

## Dependency order

```
AP-0028 (inject failure at step k) ─┐
AP-0029 (B0–B3 recovery strategies) ─┼─→ AP-0030 (metrics vs uninterrupted run)
                                     │        ├─→ AP-0031 (ablation → C2, C5)
                                     │        ├─→ AP-0032 (cross-version → C4)
                                     └────────┴─→ AP-0033 (matrix + aggregate → C1, C3; claims update)
```

## Checklist

- [ ] Failure injected at step `k` by type via a generic seam; uninterrupted reference run available (AP-0028)
- [ ] B0/B1/B2/B3 implemented behind one `RecoveryStrategy` interface (AP-0029)
- [ ] Five axes measured against the uninterrupted run; effect-safety is a gate, not averaged in (AP-0030)
- [ ] Ablation strips cairn components and locates the fidelity cliff (AP-0031)
- [ ] Cross-version checkpoint-A/resume-B succeeds where replay would not (AP-0032)
- [ ] Matrix runner aggregates results; claims registry updated with dated, honestly-scoped evidence (AP-0033)
- [ ] No hardcoded harness (ADR-0007); honest-results policy (ADR-0009); docs + trackers updated; tests pass

## Completion criteria

- [ ] The benchmark runs end-to-end and produces a results table over (step × type × baseline)
- [ ] **C1** supported: B3 (RGR) beats B0 (cold restart) on recovery tax + no-regression
- [ ] **C3** supported: with-WAL resume yields 0 duplicate effects vs the without-WAL baseline
- [ ] **C2/C5** evidenced by the ablation; **C4** evidenced by the cross-version experiment
- [ ] Claims registry statuses updated with dated notes and explicit scope limits
- [ ] `pytest` green across the new eval suite and all prior tests
- [ ] All Phase 5 APs `Done`; ROADMAP, trackers, CHANGELOG, ADR-0009 updated
