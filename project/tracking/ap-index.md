# Action Point Index

> Live rollup of all Action Points. **Phases 0–5** APs (AP-0001 … AP-0033) are committed and `Done`;
> **Phase 6** (AP-0034 … AP-0037): AP-0034/0035 `Done`, AP-0036/0037 `Blocked` (deferred to M1's go/no-go).
> **Milestone M1** (AP-0038 … AP-0042) complete & merged (PR #7) 2026-06-16: all five `Done`; **outcome
> NO-GO**; project stays 0.x, AP-0036/0037 stay `Blocked`. **Milestone M2** (AP-0043 … AP-0047) entered
> 2026-06-16: **AP-0043 `Done`** (non-batchable chain task,
> 2026-06-23), the rest `Accepted`.
> Last updated: 2026-06-23.

**Status values:** Proposed · Accepted · In Progress · In Review · Done · Blocked · Superseded

## Phase 0 — Project Definition *(committed)*

| ID | Title | Status |
|---|---|---|
| [AP-0001](../phases/phase-0-definition/action-points/AP-0001-repository-structure.md) | Establish repository structure & skeleton | Done |
| [AP-0002](../phases/phase-0-definition/action-points/AP-0002-documentation-governance.md) | Ratify documentation governance model | Done |
| [AP-0003](../phases/phase-0-definition/action-points/AP-0003-ap-phase-workflow.md) | Define AP & phase workflow process docs | Done |
| [AP-0004](../phases/phase-0-definition/action-points/AP-0004-vision-positioning-scope.md) | Author vision, positioning & scope docs | Done |
| [AP-0005](../phases/phase-0-definition/action-points/AP-0005-master-trackers.md) | Stand up master trackers | Done |
| [AP-0006](../phases/phase-0-definition/action-points/AP-0006-license-contribution-citation.md) | License + contribution + citation scaffolding | Done |

## Phase 1 — Conceptual & Research Foundation *(committed — entered 2026-06-15)*

| ID | Title | Status |
|---|---|---|
| [AP-0007](../phases/phase-1-conceptual-foundation/action-points/AP-0007-formalize-recovery-problem.md) | Formalize the recovery problem (continuation sufficiency) | Done |
| [AP-0008](../phases/phase-1-conceptual-foundation/action-points/AP-0008-recovery-fidelity-metric.md) | Define recovery-fidelity metric & eval dimensions (conceptual) | Done |
| [AP-0009](../phases/phase-1-conceptual-foundation/action-points/AP-0009-related-work-positioning.md) | Related-work survey & positioning matrix | Done |
| [AP-0010](../phases/phase-1-conceptual-foundation/action-points/AP-0010-conceptual-framework.md) | Conceptual framework docs (Code Harness / Runtime / recovery) | Done |
| [AP-0011](../phases/phase-1-conceptual-foundation/action-points/AP-0011-claims-registry.md) | Establish research claims registry | Done |
| [AP-0012](../phases/phase-1-conceptual-foundation/action-points/AP-0012-state-and-tool-taxonomies.md) | State taxonomy + tool effect taxonomy (conceptual) | Done |

## Phase 2 — Architecture & Protocol Design *(committed — entered 2026-06-15)*

| ID | Title | Status |
|---|---|---|
| [AP-0013](../phases/phase-2-architecture-protocol/action-points/AP-0013-continuation-state-schema.md) | Continuation State (cairn) schema spec | Done |
| [AP-0014](../phases/phase-2-architecture-protocol/action-points/AP-0014-boundary-contract.md) | Code Harness ↔ Runtime boundary contract spec | Done |
| [AP-0015](../phases/phase-2-architecture-protocol/action-points/AP-0015-resume-protocol.md) | Re-grounding resume protocol spec | Done |
| [AP-0016](../phases/phase-2-architecture-protocol/action-points/AP-0016-unified-distillation.md) | Unified compaction/checkpoint distillation design (core/tail) | Done |
| [AP-0017](../phases/phase-2-architecture-protocol/action-points/AP-0017-effect-safety-protocol.md) | Effect-safety write-ahead protocol spec | Done |
| [AP-0018](../phases/phase-2-architecture-protocol/action-points/AP-0018-tool-recovery-policy.md) | Tool effect taxonomy → recovery-policy mapping | Done |

## Phase 3 — Minimal Harness *(committed — entered 2026-06-15)*

| ID | Title | Status |
|---|---|---|
| [AP-0021](../phases/phase-3-minimal-harness/action-points/AP-0021-boundary-interfaces.md) | Boundary-contract interfaces + core data models | Done |
| [AP-0019](../phases/phase-3-minimal-harness/action-points/AP-0019-minimal-runtime.md) | Minimal Runtime (sandbox, workspace, effect ledger, checkpoint store) | Done |
| [AP-0020](../phases/phase-3-minimal-harness/action-points/AP-0020-minimal-code-harness.md) | Minimal Code Harness (agent loop, code-as-action, model provider) | Done |
| [AP-0022](../phases/phase-3-minimal-harness/action-points/AP-0022-baseline-tasks-tests.md) | Baseline task suite (no recovery) + smoke tests | Done |

## Phase 4 — Recovery v1 (three pillars) *(committed — entered 2026-06-15)*

| ID | Title | Status |
|---|---|---|
| [AP-0023](../phases/phase-4-recovery-v1/action-points/AP-0023-unified-distillation-engine.md) | Unified distillation engine (cairn writer) | Done |
| [AP-0024](../phases/phase-4-recovery-v1/action-points/AP-0024-checkpoint-snapshot-integration.md) | Checkpoint persistence + workspace snapshot integration | Done |
| [AP-0025](../phases/phase-4-recovery-v1/action-points/AP-0025-regrounding-resume.md) | Re-grounding resume protocol implementation | Done |
| [AP-0026](../phases/phase-4-recovery-v1/action-points/AP-0026-effect-safety-wal.md) | Effect-safety WAL + idempotency enforcement | Done |
| [AP-0027](../phases/phase-4-recovery-v1/action-points/AP-0027-end-to-end-recovery.md) | End-to-end recovery from injected failure | Done |

## Phase 5 — Evaluation & Benchmark *(committed — entered 2026-06-15)*

| ID | Title | Status |
|---|---|---|
| [AP-0028](../phases/phase-5-evaluation/action-points/AP-0028-failure-injection-harness.md) | Failure-injection harness (step × failure-type matrix) | Done |
| [AP-0029](../phases/phase-5-evaluation/action-points/AP-0029-baselines.md) | Baselines (cold restart, log-replay, snapshot-only, RGR) | Done |
| [AP-0030](../phases/phase-5-evaluation/action-points/AP-0030-metrics.md) | Metrics implementation (five fidelity axes) | Done |
| [AP-0031](../phases/phase-5-evaluation/action-points/AP-0031-ablation.md) | Continuation-State ablation study | Done |
| [AP-0032](../phases/phase-5-evaluation/action-points/AP-0032-cross-version-resume.md) | Cross-version resume experiment | Done |
| [AP-0033](../phases/phase-5-evaluation/action-points/AP-0033-results-aggregation.md) | Results aggregation & claims update | Done |

## Phase 6 — Paper & Release *(committed — entered 2026-06-15)*

| ID | Title | Status |
|---|---|---|
| [AP-0034](../phases/phase-6-paper-release/action-points/AP-0034-paper-draft.md) | Paper draft ("Checkpoints Are Compactions") | Done |
| [AP-0035](../phases/phase-6-paper-release/action-points/AP-0035-reproducibility-package.md) | Reproducibility package & artifact polish | Done |
| [AP-0036](../phases/phase-6-paper-release/action-points/AP-0036-v1-release.md) | v1.0 OSS release — *deferred to Milestone M1's go/no-go (AP-0042)* | Blocked |
| [AP-0037](../phases/phase-6-paper-release/action-points/AP-0037-public-positioning.md) | Public positioning / announcement — *deferred to Milestone M1's go/no-go (AP-0042)* | Blocked |

## Milestone M1 — Live-LLM Validation *(committed — entered 2026-06-16)*

| ID | Title | Status |
|---|---|---|
| [AP-0038](../phases/milestone-1-live-llm-validation/action-points/AP-0038-live-model-providers.md) | Live LLM `ModelProvider` adapters (injected, no hardcoding) | Done |
| [AP-0039](../phases/milestone-1-live-llm-validation/action-points/AP-0039-determinism-cost-repro.md) | Determinism, cost & reproducibility controls for live runs | Done |
| [AP-0040](../phases/milestone-1-live-llm-validation/action-points/AP-0040-live-failure-injection-study.md) | Live failure-injection study (Phase 5 matrix, real model) | Done *(ran `owl-alpha`; honest negative)* |
| [AP-0041](../phases/milestone-1-live-llm-validation/action-points/AP-0041-live-results-claims-update.md) | Live results analysis & claims update (C1–C5) | Done |
| [AP-0042](../phases/milestone-1-live-llm-validation/action-points/AP-0042-v1-go-no-go.md) | v1.0 go/no-go gate (unblock AP-0036/0037 on success) | Done *(NO-GO)* |

## Milestone M2 — Recovery-faithful live benchmark *(committed — entered 2026-06-16)*

| ID | Title | Status |
|---|---|---|
| [AP-0043](../phases/milestone-2-recovery-faithful-benchmark/action-points/AP-0043-nonbatchable-sequential-task.md) | Non-batchable sequential benchmark task | Done |
| [AP-0044](../phases/milestone-2-recovery-faithful-benchmark/action-points/AP-0044-action-granularity-metrics.md) | Action-granularity-robust recovery metrics | Accepted |
| [AP-0045](../phases/milestone-2-recovery-faithful-benchmark/action-points/AP-0045-repetition-statistics-harness.md) | Repetition + statistics harness (injection-fired enforced) | Accepted |
| [AP-0046](../phases/milestone-2-recovery-faithful-benchmark/action-points/AP-0046-live-rerun-claims-update.md) | Live re-run + claims update (C1–C5, with statistics) | Accepted |
| [AP-0047](../phases/milestone-2-recovery-faithful-benchmark/action-points/AP-0047-v1-go-no-go-take2.md) | v1.0 go/no-go, take 2 | Accepted |
