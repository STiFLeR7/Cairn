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
- **Phase 2 — Architecture & Protocol Design: complete & merged** (PR #2, 2026-06-15). All six APs
  (AP-0013 … AP-0018) `Done`; ADRs 0002–0006 accepted.

### Added (Phase 3, on branch `phase-3-minimal-harness`) — first runnable code
- `pyproject.toml`; `src/cairn/` package: `state` (ContinuationState), `contract` (Runtime/CodeHarness
  protocols), `sandbox`, `model`, `tools`, `task` interfaces (AP-0021).
- `cairn.runtime` — `LocalSubprocessSandbox`, workspace snapshot/restore, append-only effect ledger,
  atomic checkpoint store, `LocalRuntime` (AP-0019).
- `cairn.harness` — agent loop (code-as-action), minimal distill; `ScriptableMockModel` (AP-0020).
- `cairn.tasks.CreateFileTask`, `cairn.app.build_harness`, `examples/quickstart.py`, `tests/` (AP-0022).
- ADR-0007 — Python stack + no-hardcoded-harness principle.
- `tests/test_workspace.py` — workspace snapshot/restore round-trip + unknown-snapshot guard, added during
  PR #3 review (`restore_workspace` had been delivered but untested).

### Status (Phase 3)
- **Phase 3 — Minimal Harness: complete & merged** (PR #3, 2026-06-15; merge commit `ea658e2`). All four
  APs (AP-0019 … AP-0022) `Done`; **`pytest -q` → 13 passed**; quickstart runs end-to-end. No hardcoded
  harness (ADR-0007). Next: Phase 4 — Recovery v1.

### Added (Phase 4, on branch `phase-4-recovery-v1`) — recovery
- `cairn.harness.distill` — unified `distill(goal, history, mode=compact|checkpoint)`: real durable core
  (intent, plan + status, decisions incl. ruled-out) identical across modes (claim C2), tail pruned vs
  frozen; `cairn.runtime.digest.world_digest` (per-file sha256) recorded in `world.digest` (AP-0023).
- `cairn.runtime.workspace` — snapshot ids now **continue-from-highest** so a resumed (freshly
  constructed) runtime never overwrites a referenced snapshot — invariant I4 across restart (AP-0024).
- `cairn.harness.observe` (`observe_world`) + `cairn.harness.reconcile` (`reconcile` → `ResumePlan`:
  torn writes via digest mismatch, plan drift, effect danger window) + `CodeHarness.resume` implementing
  RGR (load → re-observe → reconcile → re-plan → continue); `reconcile` added to the contract (AP-0025).
- `cairn.harness.effects` — `EffectfulTool`, write-ahead `perform_effect` (INTENT→run→COMPLETE),
  `danger_window`, `resolve_danger_window` (redo / verify-then-redo-or-skip / escalate); claim C3 (AP-0026).
- `cairn.harness.failure` (`InjectedFailure`, `crash_after`) + generic `step_hook` lifecycle seam;
  `examples/recovery_demo.py`; `tests/test_recovery_e2e.py` (AP-0027).
- ADR-0008 — Recovery v1 implementation decisions (snapshot numbering, digest, resume, effects, hook).

### Fixed (Phase 4, PR #4 review/debugging)
- `reconcile` no longer reopens a step when an *unrelated* file diverges (step id `s0` had
  substring-matched a path like `logs0.txt`); regression test added.
- Documented honestly (ADR-0008 §7) that v1 resume is **restore-first**, so torn-write/plan-drift
  detection is a no-op in the integrated flow (reserved for a future crash-in-place mode); reconcile's
  active v1 jobs are effect danger-window resolution + plan re-grounding.

### Status (Phase 4)
- **Phase 4 — Recovery v1: complete & merged** (PR #4, 2026-06-15; merge commit `b008a4f`). All five APs
  (AP-0023 … AP-0027) `Done`; **`pytest -q` → 33 passed**; `examples/recovery_demo.py` shows crash→resume
  with **recovery_tax=1** (vs cold-restart 3) and the effect resolved exactly once (no duplicate). No
  hardcoded harness (ADR-0007). Next: Phase 5 — Evaluation & Benchmark.
