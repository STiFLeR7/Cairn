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

## Phase 1 — Conceptual & Research Foundation *(provisional)*

| ID | Title | Status |
|---|---|---|
| AP-0007 | Formalize the recovery problem (continuation sufficiency) | Proposed |
| AP-0008 | Define recovery-fidelity metric & eval dimensions (conceptual) | Proposed |
| AP-0009 | Related-work survey & positioning matrix | Proposed |
| AP-0010 | Conceptual framework docs (Code Harness / Runtime / recovery) | Proposed |
| AP-0011 | Establish research claims registry | Proposed |
| AP-0012 | State taxonomy + tool effect taxonomy (conceptual) | Proposed |

## Phase 2 — Architecture & Protocol Design *(provisional)*

| ID | Title | Status |
|---|---|---|
| AP-0013 | Continuation State (cairn) schema spec | Proposed |
| AP-0014 | Code Harness ↔ Runtime boundary contract spec | Proposed |
| AP-0015 | Re-grounding resume protocol spec | Proposed |
| AP-0016 | Unified compaction/checkpoint distillation design (core/tail) | Proposed |
| AP-0017 | Effect-safety write-ahead protocol spec | Proposed |
| AP-0018 | Tool effect taxonomy → recovery-policy mapping | Proposed |

## Phase 3 — Minimal Harness *(provisional)*

| ID | Title | Status |
|---|---|---|
| AP-0019 | Minimal Runtime (workspace, sandbox, execution, effect-ledger store) | Proposed |
| AP-0020 | Minimal Code Harness (agent loop, code-as-action) | Proposed |
| AP-0021 | Implement boundary-contract interfaces | Proposed |
| AP-0022 | Baseline task suite (no recovery) + smoke tests | Proposed |

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
