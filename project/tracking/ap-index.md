# Action Point Index

> Live rollup of all Action Points. Only **Phase 0** APs are committed; later-phase APs are
> *provisional* placeholders, refined when their phase is entered (see
> [phase process](../../docs/governance/phase-process.md)). Last updated: 2026-06-15.

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

## Phase 4 — Recovery v1 (three pillars) *(provisional)*

| ID | Title | Status |
|---|---|---|
| AP-0023 | Unified distillation engine (cairn writer) | Proposed |
| AP-0024 | Checkpoint persistence + workspace snapshot integration | Proposed |
| AP-0025 | Re-grounding resume protocol implementation | Proposed |
| AP-0026 | Effect-safety WAL + idempotency enforcement | Proposed |
| AP-0027 | End-to-end recovery from injected failure | Proposed |

## Phase 5 — Evaluation & Benchmark *(provisional)*

| ID | Title | Status |
|---|---|---|
| AP-0028 | Failure-injection harness (step × failure-type matrix) | Proposed |
| AP-0029 | Baselines (cold restart, log-replay, snapshot-only) | Proposed |
| AP-0030 | Metrics implementation (fidelity, recovery tax, effect-safety) | Proposed |
| AP-0031 | Continuation-state ablation study | Proposed |
| AP-0032 | Cross-version resume experiment | Proposed |
| AP-0033 | Results aggregation & analysis | Proposed |

## Phase 6 — Paper & Release *(provisional)*

| ID | Title | Status |
|---|---|---|
| AP-0034 | Paper draft ("Checkpoints Are Compactions") | Proposed |
| AP-0035 | Reproducibility package & artifact polish | Proposed |
| AP-0036 | v1.0 OSS release (docs, examples, citation) | Proposed |
| AP-0037 | Public positioning (README, announcement) | Proposed |
