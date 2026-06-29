# Changelog

All notable changes to Cairn are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/); the project adheres to
[Semantic Versioning](https://semver.org/) from `v1.0` onward.

Per the [documentation policy](docs/governance/documentation-policy.md), every meaningful change
updates this file.

## [0.2.0] — 2026-06-23 — Milestone M2: recovery-faithful live benchmark

First release to **actually exercise recovery against a real model**. M2 fixed the M1 root cause (a
*batchable* task that a model one-shots before any crash) by building a **non-batchable chain task**,
**work-unit / action-granularity-robust metrics**, and a **repetition + statistics** harness, then **ran it
live** (`nvidia/nemotron-3-super-120b-a12b:free`): the injected crash **fired in every cell** and RGR (B3)
recovered reliably (2/2) and cheaply (tax 1.0±0.0) while cold restart (B0) completed only 1/2. **Outcome:
NO-GO for v1.0** — the live evidence is **suggestive, not confirmed** (n=2 underpowered; a powered run was
rate-limited), so the project **stays 0.x**, released as **v0.2.0** (not the held v1.0). See AP-0043…AP-0047
below, the [claims registry](docs/research/claims-registry.md) (2026-06-23), and `PAPER.md` §9.

- **AP-0047 — v1.0 go/no-go take 2 (`Done`, 2026-06-23): NO-GO.** The M2 live run resolved the M1 blocker and
  the evidence *leans* toward C1, but it is suggestive not confirmed (n=2; strict `verdict_c1` NOT SHOWN;
  C2/C4/C5 reference-only; C3 unwired; powered run rate-limited). Calling v1.0 would overclaim → project stays
  **0.x**; AP-0036 (v1.0 release) and AP-0037 (announcement) stay `Blocked`. M2 shipped as the 0.x tag
  **v0.2.0**. The v1.0 gate is now a **powered** live study (non-free model, more repeats/crash points, wire
  C3, success-conditioned tax verdict). Version bumped `0.1.0 → 0.2.0`.

## Milestone M3 — Powered live study (complete — **NO-GO** take 3, branch `milestone-3-powered-live-study`)

The v1.0 gate: turn M2's *suggestive* live C1 into a powered, confirmable result, and close the fairness gap.
**Outcome: the strongest live signal yet (RGR ≈ halves recovery tax on a powered 28-cell run) but the strict
verdict is NOT SHOWN** — model-competence + rate-limit confounds. v1.0 stays held; project stays 0.x.

- **AP-0048 — success-conditioned recovery tax (`Done`, 2026-06-29).** `recovery_tax` is now the cost of a
  *successful* recovery — aggregated over successful repetitions only — so a run that fails cheaply cannot
  register a misleadingly low tax or "win" by failing. `aggregate_repeated` exposes `n_success` and
  `recovery_tax_all`; `verdict_c1` compares cost-of-success to cost-of-success and declines when the
  competitor (B0) never actually recovers. New `tests/test_eval_tax_fairness.py`.
- **AP-0049 — multi-provider OpenAI-compatible transports (`Done`, 2026-06-29).** Generalized
  `openrouter_transport` into one `openai_chat_transport` (endpoint + key-env injected) and added a provider
  registry (`openrouter` / `groq` / `zenmux`) so the powered run is not hostage to a single rate-limited free
  tier — a vendor is config, not bespoke code (ADR-0010). Keys read from env only (`OPENROUTER_API`,
  `GROQ_API_KEY`, `ZENMUX_API`); inert without a key; unknown provider rejected.
- **AP-0050 — powered live study (`Done`, 2026-06-29).** Ran the chain study with up to 8 repetitions and both
  crash points across four free-tier models / three providers. Added per-repeat resilience to `run_repeated`
  (`resilient`, `errored`, `on_error`) so a rate-limited repeat is isolated and recorded, not study-aborting;
  and a `User-Agent` header to the stdlib poster (Groq is behind Cloudflare). **Headline:** `gpt-oss-120b`
  (Groq, 8 repeats) → **28 fired cells, 0 errored**; RGR (B3) success 0.73 / tax **3.64±0.77** (max 5.0) vs
  cold restart (B0) success 0.46 / tax **6.33±0.47** (min 6.0) — RGR **≈ halves recovery tax with no overlap**,
  higher success, less regression. Nemotron corroborates (tax 3.0 vs 6.5). Two models 0-cell (Groq quota
  exhausted / ZenMux 402). Manifests + the two substantive transcripts committed (secret-scanned clean).
- **AP-0051 — v1.0 go/no-go take 3 (`Done`, 2026-06-29): NO-GO.** Strongest live signal yet, but the strict
  `verdict_c1` is **NOT SHOWN** — free models fail the *task itself* unpredictably (a model-competence
  confound, not an RGR failure) and free tiers can't sustain a powered run. v1.0 stays **held**; project
  stays **0.x**; AP-0036/0037 stay `Blocked`. Next gate: a paid/reliable model + a capability-matched C1
  verdict + C3 wired live. The strict gate was **not** loosened to manufacture a GO (ADR-0009).

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

### Added (Milestone M2, on branch `milestone-2-recovery-faithful-benchmark`) — recovery-faithful benchmark (entered)
- Milestone M2 scaffold + five committed APs (AP-0043 … AP-0047): a **non-batchable sequential task** (step
  N+1's input is unavailable until step N runs, so a capable model cannot one-shot it and a crash leaves real
  partial progress), **action-granularity-robust metrics** (progress/work-units, not one-file-per-step), a
  **repetition + statistics harness** (carrying the M1 injection-fired check), a **live re-run** producing
  dated C1–C5 evidence with statistics, and a **v1.0 go/no-go take 2** (supersedes the M1 NO-GO, AP-0042).
  Directly addresses the M1 root cause: the old benchmark task was batchable, so it could not exercise
  recovery against a real model.
- **AP-0043 — non-batchable sequential task (`Done`, 2026-06-23).** New chain-oracle primitive
  `src/cairn/eval/chain.py` (`Chain` + `render_oracle_module`): a salted hash-chain advanced **at most once
  per process**. Since the harness runs each agent step in a fresh `python -c` subprocess, completing a
  length-`n` chain requires `n` separate steps — a single batched action cannot finish it (it commits one
  token then trips the guard, leaving `pos == 1`), and a crash at step `k` leaves a genuine partial chain
  (`pos == k`). The planted `oracle` module is self-contained (stdlib + ASCII only, since the subprocess has
  no `cairn` on its path) and mirrors `Chain`'s transform exactly, so a completing run is the agreement check.
- New generic `Task.setup(workspace)` hook (default no-op) called by the harness on every
  run/resume/continue (and by the B1 baseline after its wipe): lets a task re-establish its *environment*
  (here, the oracle module) on each recovery attempt while the agent's *progress* stays the thing RGR
  restores. Existing tasks unaffected (duck-typed, `getattr`-guarded).
- `ChainTask`, `chain_scenario`, and live wiring (`fake_chain_transport`, `batching_chain_transport`,
  `live_chain_scenario`) added to `benchmarks/scenarios.py` — usable behind both the scripted mock and
  `LiveModelProvider`; salt is deterministic and no model is hardcoded (ADR-0007/0009).
- `tests/test_eval_chain.py` (8): per-process guard, batching-impossible vs. completing step-by-step run,
  fired crash leaving genuine partial progress, and B3 (RGR) recovering with lower `recovery_tax` + higher
  `no_regression` than B0 (cold restart). Suite **80 → 88 passed**.
- **AP-0044 — action-granularity-robust recovery metrics (`Done`, 2026-06-23).** `no_regression` and
  `recovery_tax` are now defined in **work units** (a task-defined progress increment), not model actions —
  the M1 finding showed action-count metrics are meaningless when a real model chunks work differently than
  the scripted mock. New `Task.progress(workspace) -> Optional[int]` oracle (default `None`; `ChainTask` →
  chain `pos`, `MultiFileTask` → file count). `no_regression(recovery_units, work_at_crash, total_units)`
  scores genuinely-remaining vs. redone units; `recovery_tax` is the work-unit count. Measurements plumbed
  via `RunOutcome.work_units` (reference `W` + each baseline's final units) and `Injection.work_at_crash`
  (progress when the crash fired); `score(...)` threads `work_at_crash` through `runner` and `ablation`. The
  non-batchable chain pins one unit per action, so the deterministic C1 matrix and C5 ablation numbers are
  unchanged; a unitless task falls back to the original action/`k` form. `tests/test_eval_metrics.py`
  rewritten to the work-unit signature (with rationale) + a granularity-robustness test; an exact
  end-to-end `recovery_tax == W - work_at_crash` assertion added on the chain. `recovery-fidelity.md` §2a
  documents the definitions and traces them to M1. Suite **88 → 90 passed**.

- **AP-0045 — repetition + statistics harness (`Done`, 2026-06-23).** `run_repeated(scenario, steps,
  baselines, *, repeats, base_factory, on_skip, before_repeat)` runs the matrix `N` times (each a full
  `run_matrix` pass, so the reference is re-run per repeat and the M1 injection-fired skip is enforced),
  returning `RepeatedRun(reports, fired, skipped, repeats, …)`. `aggregate_repeated` → per-baseline
  `AxisStat(mean, stdev, min, max, n)` per axis (population stdev, 0 for a deterministic model) +
  `effect_duplicates_total` + `gate_pass_rate`; vacuous cells are excluded (all-skipped → `{}`).
  `verdict_c1(summary)` reports "supported" only with consistent evidence: both B0/B3 fired, B3 completes
  the task in *every* repetition, B3 recovery tax strictly lower with no overlap (`B3.tax.max < B0.tax.min`),
  and B3 ≥ B0 on mean no-regression. `before_repeat(i)` is the live-reseed seam; `format_repeated_table`
  renders mean±spread. An offline repeated study on the **non-batchable chain** is wired into
  `benchmarks/live_study.py` (`run_offline_repeated_study`) — the exact machinery AP-0046 runs live.
- **Benchmark-hygiene fix (`world_digest`).** Python bytecode caches (`__pycache__`, `.pyc`/`.pyo`) are now
  excluded from the workspace digest. Importing a planted workspace module (the chain `oracle`) creates a
  `.pyc` with a non-reproducible header that dropped `solution_quality` to 0.67 and could trigger spurious
  torn-write detection on resume; excluded, the recovered chain matches the reference exactly (1.0).
- `tests/test_eval_repetition.py` (8): N-per-cell repetition, zero spread on the deterministic chain,
  work-unit means, vacuous-cell skipping, `verdict_c1` supported/not-supported, the `before_repeat` hook,
  and table rendering; plus a chain `solution_quality == 1.0` regression guard. Suite **90 → 98 passed**.

- **AP-0046 — live re-run on the non-batchable task (`Done`, 2026-06-23).** Rewired
  `benchmarks/live_study.py::run_live_study` onto the chain task (AP-0043) + repetition harness (AP-0045):
  runs B0-vs-B3 `repeats` times, prints mean±spread + fired/skipped, computes `verdict_c1`, and writes an
  auditable manifest. Validated offline (injected transport), then **run live (user-approved) against
  `nvidia/nemotron-3-super-120b-a12b:free`** via OpenRouter. **The injected crash fired in all 4 cells
  (skipped=0) — the M1 blocker is resolved**; recovery was exercised against a real model for the first time.
  n=2 result: **B3/RGR 2/2 success, recovery_tax 1.0±0.0**; **B0/cold-restart 1/2, tax 2.5±2.5** — RGR
  dominates on every axis mean and reliability, but the strict no-overlap verdict is **NOT SHOWN** (B0's
  failed repeat has tax 0; n=2 underpowered). Recorded honestly as **C1 suggestive, not confirmed live**
  (claims registry + `PAPER.md §9`, 2026-06-23); C2/C4/C5 stay reference-harness, C3 not wired.
- **Live-path hardening (AP-0046).** `cairn.live_controls.retrying` — bounded exponential backoff on
  *transient* failures (429/5xx, a stealth model's intermittent "Provider returned error"); permanent 4xx
  (401/404) fail fast (`is_transient`). `run_live_study` now uses filesystem-safe model slugs (the `:free`
  colon was opening an NTFS alternate data stream on Windows) and **records to a `.partial` transcript,
  finalizing on success only** — a crashing re-run (e.g. a rate-limit 429 mid-study) can no longer clobber a
  prior good transcript. `world_digest` exclusion (above) and these are general robustness fixes.
  `tests/test_live_controls.py` +4 (retry recover / fail-fast / give-up / classification);
  `tests/test_live_study.py::test_live_study_runs_on_chain_offline` proves the chain pipeline offline. Suite
  **98 → 103 passed**.
- **Honest limits recorded (ADR-0009).** The live run is **underpowered** (n=2, one crash point, one model);
  a larger run was **blocked by the OpenRouter free-tier rate limit (HTTP 429)**, and the raw transcript was
  lost to the truncation footgun *before* it was fixed (the manifest survived as the citable artifact).
  `nemotron-3-ultra-550b` was unusable (gateway 504). A **powered** live study remains the gate for any
  C1-confirmed-live claim; **v1.0 stays held**.

### Status (Milestone M2)
- **Milestone M2 — Recovery-faithful live benchmark: complete** (2026-06-16 → 2026-06-23; **AP-0043…AP-0047
  all `Done`**, 5 / 5; shipped **v0.2.0**). Branch `milestone-2-recovery-faithful-benchmark` off `master`
  (M1 merged via PR #7, `0e39b5c`). **Outcome: NO-GO for v1.0** — project stays 0.x; AP-0036/0037 remain
  `Blocked`, now gated on a *powered* live study.

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
