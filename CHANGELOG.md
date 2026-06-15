# Changelog

All notable changes to Cairn are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/); the project adheres to
[Semantic Versioning](https://semver.org/) from `v1.0` onward.

Per the [documentation policy](docs/governance/documentation-policy.md), every meaningful change
updates this file.

## [Unreleased]

### Added
- Phase 0 foundation: repository scaffold, governance model, vision/positioning/scope docs,
  master trackers, AP/phase templates, and the six Phase-0 Action Points (AP-0001 … AP-0006).
- ADR-0001 recording the foundational decisions (name **Cairn**, Apache-2.0, 7-phase arc,
  `docs/` vs `project/` split, documentation-first / AP-driven operating model).

### Status
- **Phase 0 — Project Definition: complete.** Reviewed and approved 2026-06-15; all six Phase-0
  Action Points (AP-0001 … AP-0006) marked `Done`. Next: Phase 1 — Conceptual & Research Foundation.
- **Phase 1 — Conceptual & Research Foundation: entered 2026-06-15.** Six provisional APs
  (AP-0007 … AP-0012) refined into committed Action Points (`Accepted`); phase scaffold and README added.

### Added (Phase 1, on branch `phase-1-conceptual-foundation`)
- `docs/concepts/problem-formalization.md` — formal agent-recovery problem, three assumption
  violations, continuation sufficiency (AP-0007, `Done`).
- `docs/concepts/code-harness-and-runtime.md` — two-layer model + *one concern, two altitudes* rule,
  topology resolution (AP-0010, `Done`).
- `docs/concepts/recovery-in-the-two-layer-model.md` — recovery = Runtime mechanism + Code Harness
  semantics; neither-alone argument (AP-0010, `Done`).
- `docs/concepts/recovery-fidelity.md` — recovery fidelity as outcome equivalence; five axes; four
  baselines; sufficiency ablation (AP-0008, `Done`).
- `docs/concepts/state-taxonomy.md` — five-layer agent-state taxonomy with owners (AP-0012, `Done`).
- `docs/concepts/tool-effect-taxonomy.md` — three tool classes + write-ahead effect discipline
  (AP-0012, `Done`).
- `docs/research/related-work.md` — prior-art survey, positioning matrix, novelty statement
  (AP-0009, `Done`).
- `docs/research/claims-registry.md` — falsifiable claims C1–C5, schema, freeze policy
  (AP-0011, `Done`).

### Status (Phase 1)
- **Phase 1 — Conceptual & Research Foundation: complete & merged** (PR #1, 2026-06-15). All six APs
  (AP-0007 … AP-0012) `Done` and merged to `master` via merge commit.

### Added (Phase 2, on branch `phase-2-architecture-protocol`)
- `docs/design/continuation-state-schema.md` + ADR-0002 — the cairn schema, durable core + elastic tail (AP-0013).
- `docs/design/boundary-contract.md` + ADR-0003 — Code Harness ↔ Runtime operations + invariants I1–I5 (AP-0014).
- `docs/design/resume-protocol.md` + ADR-0004 — RGR: load → re-observe → reconcile → re-plan → continue (AP-0015).
- `docs/design/unified-distillation.md` + ADR-0005 — one `distill` for compaction + checkpoint, core/tail (AP-0016).
- `docs/design/effect-safety-protocol.md` + ADR-0006 — write-ahead INTENT/COMPLETE ledger + reconciliation (AP-0017).
- `docs/design/tool-recovery-policy.md` — tool declaration + per-class resume policy + conservative default (AP-0018).

### Status (Phase 2)
- **Phase 2 — Architecture & Protocol Design: complete on branch** `phase-2-architecture-protocol`
  (2026-06-15). All six APs (AP-0013 … AP-0018) `Done`; ADRs 0002–0006 accepted. Awaiting review + merge.
  Next: Phase 3 — Minimal Harness.
