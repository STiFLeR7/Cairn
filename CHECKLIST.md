# Cairn — Master Checklist

> Single always-visible status surface. Rolls up phases and Action Points. Detailed status:
> [`project/tracking/phase-tracking.md`](project/tracking/phase-tracking.md) ·
> [`project/tracking/ap-index.md`](project/tracking/ap-index.md).

## Phases

- [x] **Phase 0 — Project Definition** 🟢 *(complete — reviewed & approved 2026-06-15)*
- [x] **Phase 1 — Conceptual & Research Foundation** 🟢 *(complete & merged — PR #1)*
- [x] **Phase 2 — Architecture & Protocol Design** 🟢 *(complete & merged — PR #2)*
- [ ] **Phase 3 — Minimal Harness** 🟡 *(in progress — entered 2026-06-15)*
- [ ] **Phase 4 — Recovery v1 (three pillars)**
- [ ] **Phase 5 — Evaluation & Benchmark**
- [ ] **Phase 6 — Paper & Release**

## Phase 0 — Action Points

- [x] `AP-0001` Establish repository structure & skeleton
- [x] `AP-0002` Ratify documentation governance model
- [x] `AP-0003` Define AP & phase workflow process docs
- [x] `AP-0004` Author vision, positioning & scope docs
- [x] `AP-0005` Stand up master trackers (ROADMAP, CHECKLIST, ap-index, phase-tracking)
- [x] `AP-0006` License + contribution + citation scaffolding

## Phase 0 completion criteria

- [x] Repository structure scaffolded (`docs/` + `project/` + root trackers)
- [x] Documentation governance model ratified (ADR-0001)
- [x] AP & phase workflow documented with templates
- [x] Vision, positioning, and scope authored and approved
- [x] Master trackers live and cross-linked
- [x] Apache-2.0 license + contribution + citation files present

## Phase 1 — Action Points

- [x] `AP-0007` Formalize the recovery problem (continuation sufficiency)
- [x] `AP-0008` Define recovery-fidelity metric & eval dimensions (conceptual)
- [x] `AP-0009` Related-work survey & positioning matrix
- [x] `AP-0010` Conceptual framework docs (Code Harness / Runtime / recovery)
- [x] `AP-0011` Establish research claims registry
- [x] `AP-0012` State taxonomy + tool effect taxonomy (conceptual)

## Phase 1 completion criteria

- [x] Continuation-sufficiency and recovery-fidelity *defined* (not asserted)
- [x] Related work mapped; white space explicit and defensible
- [x] Conceptual framework + taxonomies authored and internally consistent
- [x] Claims registry populated and frozen
- [x] No code introduced (Phase 1 is conceptual)

## Phase 2 — Action Points

- [x] `AP-0013` Continuation State (cairn) schema spec
- [x] `AP-0014` Code Harness ↔ Runtime boundary contract spec
- [x] `AP-0015` Re-grounding resume protocol spec
- [x] `AP-0016` Unified compaction/checkpoint distillation design (core/tail)
- [x] `AP-0017` Effect-safety write-ahead protocol spec
- [x] `AP-0018` Tool effect taxonomy → recovery-policy mapping

## Phase 2 completion criteria

- [x] All six specs authored in `docs/design/` and internally consistent
- [x] Every design decision traces to a Phase 1 concept
- [x] ADRs accepted for the keystone decisions (schema, boundary contract, unified distillation)
- [x] Design is implementable — Phase 3 can build against these contracts
- [x] No runnable code (Phase 2 is design)

## Phase 3 — Action Points

- [ ] `AP-0021` Boundary-contract interfaces + core data models
- [ ] `AP-0019` Minimal Runtime (sandbox, workspace, effect ledger, checkpoint store)
- [ ] `AP-0020` Minimal Code Harness (agent loop, code-as-action, model provider)
- [ ] `AP-0022` Baseline task suite (no recovery) + smoke tests

## Phase 3 completion criteria

- [ ] Assembled harness completes a baseline task end-to-end
- [ ] `pytest` smoke suite passes (contract behaviors + baseline task)
- [ ] No hardcoded harness — model/tools/tasks/sandbox injected (ADR-0007)
- [ ] Recovery not implemented (Phase 4); seams exist
