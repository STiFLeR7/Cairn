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

### Added (Phase 5, on branch `phase-5-evaluation`) — benchmark
- `cairn.eval` package: `failure` (FailureType), `scenario` (`Scenario`/`EffectSpec`, reference +
  run-until-failure, external-effect model), `baselines` (B0 ColdRestart / B1 LogReplay / B2 SnapshotOnly /
  B3 RGR behind one `RecoveryStrategy`), `metrics` (five axes + `RecoveryReport` gate), `ablation`
  (`ablate` + suite), `runner` (`run_matrix` + aggregate + table) (AP-0028…AP-0031, AP-0033).
- `CodeHarness.continue_from` — public seam for baselines to continue from a supplied history.
- `benchmarks/` — concrete scenarios + runnable studies: `recovery_matrix.py`, `ablation_study.py`,
  `cross_version_resume.py` (AP-0032/0033); `tests/conftest.py` makes them importable.
- ADR-0009 — evaluation-framework design + honest-results policy.
- Claims registry updated with dated, scoped evidence.

### Status (Phase 5)
- **Phase 5 — Evaluation & Benchmark: complete & merged** (PR #5, 2026-06-15; merge commit `d925e2b`). All
  six APs (AP-0028 … AP-0033) `Done`; **`pytest -q` → 42 passed**; the three benchmarks run end-to-end. Evidence
  (deterministic reference harness, ADR-0009): **C1 supported** (RGR tax 1.5 vs cold-restart 5.0,
  no-regression 1.0 vs 0.0), **C3 supported** (0 duplicate effects with WAL vs 1 without; gate PASS vs
  FAIL), **C5 supported** (ablation locates `plan` as the fidelity cliff), **C2 evidenced**, **C4 mechanism
  shown** (cross-version provenance A→B). No hardcoded harness (ADR-0007). Awaiting review + merge. Next:
  Phase 6 — Paper & Release.

### Added (Phase 6, on branch `phase-6-paper-release`) — paper & release prep
- `PAPER.md` — research paper draft ("Checkpoints Are Compactions"): problem → two-layer model →
  Continuation State → RGR → effect-safety → unified distillation → Phase 5 evaluation → limitations,
  with honest scope (ADR-0009) and references to the in-repo docs (AP-0034).
- `REPRODUCE.md` + `Makefile` — one-command reproduction (`make test|demo|bench`) with documented
  expected outputs; examples self-bootstrap `sys.path` so `python examples/*.py` runs without
  `PYTHONPATH`; Makefile uses `PY` to avoid a Windows backslash-path env collision (AP-0035).
- `docs/release/RELEASE_NOTES_v1.0.0.md` (draft) and `ANNOUNCEMENT.md` (draft) — prepared, **gated**.

### Status (Phase 6)
- **Phase 6 — Paper & Release: core complete & merged** (PR #6, 2026-06-15; merge commit `0e36f25`).
  AP-0034 (paper) and AP-0035 (reproducibility) `Done` and verified (42 tests, demo, benchmarks reproduce).
  **Decision (2026-06-15): the v1.0 release (AP-0036) and the public announcement (AP-0037) are deferred**
  to **Milestone M1's go/no-go (AP-0042)**, keeping the project at **0.x** until a live-LLM study validates
  the claims (current evidence is reference-harness only, ADR-0009). Drafts stay ready. This is a deliberate
  hold, not an impediment.

### Added (Milestone M1, on branch `milestone-1-live-llm-validation`) — live-LLM validation (entered)
- Milestone M1 scaffold + five committed APs (AP-0038 … AP-0042): live `ModelProvider` adapters (injected,
  no hardcoding — ADR-0007); determinism/cost/reproducibility controls for live runs; the live
  failure-injection study (Phase 5 matrix against a real model); live results analysis + C1–C5 claims update;
  and a v1.0 go/no-go gate that (on "go") unblocks the deferred AP-0036/0037. An integration ADR (ADR-0010)
  is authored when AP-0038 starts.

- `cairn.model_live` (**AP-0038, `Done`**) — `LiveModelProvider` adapts a real LLM to the existing
  `ModelProvider` seam via an **injected `Transport`** (`prompt -> reply text`): overridable
  `render_prompt`/`parse_action` (fenced block → `CODE`, `TASK_COMPLETE` → `FINISH`, malformed → safe
  `FINISH`), and an `anthropic_transport(*, model, ...)` factory — `model` injected (no default id), key from
  `$ANTHROPIC_API_KEY`, the `anthropic` SDK an optional `cairn[live]` extra imported lazily, fake-`client`
  injection for offline tests. ADR-0010 records the decision; nothing is hardcoded into the harness (ADR-0007).
- `cairn.live_controls` (**AP-0039, `Done`**) — composable transport wrappers that make a live run auditable,
  re-runnable, and bounded: `record_to` (JSONL prompt/reply transcript), `replay_transport` /
  `replay_from_transcript` (FIFO-by-prompt-key replay, offline and key-free — deterministic independent of the
  model), and `Budget`/`budgeted` (call/char ceiling → `BudgetExceeded` before overrun). `REPRODUCE.md` gains
  a "Live runs" section; transcripts carry no secrets.
- Live-pipeline study runner (**AP-0040, `Done`**) — `benchmarks/live_study.py` + live wiring in
  `benchmarks/scenarios.py` (`fake_multifile_transport`, `live_multi_file_scenario`, `live_effectful_scenario`,
  `build_live_transport(model, provider=…)`), plus `make bench-live` and a stdlib `openrouter_transport`
  (OpenAI-compatible; no new dependency). Offline (fake transport) it reproduces C1/C3 through the live code
  path; **run live against `openrouter/owl-alpha`** it exposed an honest negative (below). Two real fixes the
  live run forced: `parse_action` generalized to tolerate XML tool-call and unfenced/`compile()`-checked code
  (real models don't reliably emit fences), and a C1 verdict that had ignored `task_success`.
- **Milestone M1 outcome — `NO-GO` (AP-0041/0042).** The first live run validated the *pipeline* but **not**
  the claims: the real model batches the multi-file task into one action and finishes before the injected
  crash, so the Phase-5 recovery scenario/metrics (built around the mock's one-action-per-step cadence)
  cannot exercise recovery. C1–C5 stay **reference-harness-only** (claims registry + `PAPER.md` §9, dated
  2026-06-16). The project **remains 0.x**; the v1.0 release + announcement (AP-0036/0037) **stay `Blocked`**
  — the Phase-6 hold is now *confirmed by evidence*. The fix becomes **M2** (a non-batchable sequential task
  + action-granularity-robust metrics + repetitions).

### Fixed (Milestone M1, systematic-debugging pass)
- **Failure-injection integrity bug.** `run_until_failure` did not verify the injected crash actually fired;
  a batchable task that the model one-shots produced a *vacuous* cell that `run_matrix` **silently scored as
  a perfect recovery** (`task_success=True, recovery_tax=0` — a false positive). Root-caused with a
  deterministic probe; fixed test-first (`tests/test_eval_injection.py`, 4 tests): `run_until_failure` now
  returns `Injection(fired, completed)` and `run_matrix(..., on_skip=…)` **skips + reports** non-fired cells
  instead of scoring them. `benchmarks/live_study.py` reports skipped cells and refuses to emit a verdict
  from zero valid cells. `pytest -q` → **80 passed**.

### Status (Milestone M1)
- **Milestone M1 — Live-LLM Validation: complete** (2026-06-16; **outcome NO-GO**). Branch
  `milestone-1-live-llm-validation` off `master` (master stays clean, branch-per-phase). All five APs
  (AP-0038 … AP-0042) `Done`: `cairn.model_live` (+ Anthropic & stdlib OpenRouter transports),
  `cairn.live_controls`, ADR-0010, the live-pipeline study runner, and the live run itself against
  `openrouter/owl-alpha`. **`pytest -q` → 76 passed** (offline); core free of model-id/key literals. The live
  run validated the pipeline but **not** the claims (batched-action → crash never fired → metrics invalid),
  so **C1–C5 stay reference-harness-only**, the project **remains 0.x**, and AP-0036/0037 stay `Blocked`. The
  next milestone (**M2**) makes the live benchmark actually exercise recovery.
