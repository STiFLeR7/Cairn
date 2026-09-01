# Phase 1 Repository Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans task-by-task.

**Goal:** Earn a reproducible proof that a terminal coding agent resumes repository edits after a process crash without losing verified work.

**Architecture:** Reuse Cairn's `World`, `Agent`, `checkpoint()`, `recover()`, and fidelity equations. Add only a repository-backed `TerminalWorld`, four sequential repository fixtures, and a process-isolated runner. Faults occur only after a clean checkpoint; a different Python process resumes through RGR and the fixture's hidden verifier judges the result.

**Tech Stack:** Python stdlib, existing Cairn runtime, pytest; no dependencies.

**Spec:** `docs/superpowers/specs/2026-08-26-phase-1-repository-recovery-design.md`

## Global Constraints

- Preserve `TerminalWorld + reference coding-agent loop + clean checkpoint -> injected process death -> fresh-process RGR -> hidden verifier`.
- Do not change compaction, external-effect, crash-in-place, integration, OpenTelemetry, or generic-agent semantics.
- A clean checkpoint requires command success, one verified work-unit advance, snapshot/digest, and completed persistence.
- Crashes during a command or before the clean checkpoint are invalid/unsupported, never scored.
- Raw output retains valid, skipped, invalid, and errored cells.

## Files

| Path | Purpose |
|---|---|
| `src/cairn/worlds/terminal.py` | Executable repository `World`. |
| `src/cairn/worlds/__init__.py` | Export only `TerminalWorld`. |
| `src/cairn/eval/recoverybench.py` | Fixtures, clean-checkpoint loop, process records, schema, gate. |
| `benchmarks/recoverybench.py` | Parent/worker CLI. |
| `benchmarks/recoverybench_fixtures/` | Four pinned repositories and verifier scripts. |
| `tests/test_terminal_world.py` | World unit tests. |
| `tests/test_recoverybench.py` | Fixtures, receipts, schema, matrix and gate tests. |
| `tests/test_recoverybench_process.py` | Fresh-process proof. |
| `tests/test_recoverybench_live.py` | Opt-in live wiring only. |

## State 1 — Repository world

**Objective:** A terminal repository is a real Cairn `World`, not a second runtime.

**Deliverable:** `TerminalWorld.execute(command) -> ExecResult`, `snapshot()`, `restore()`, and `digest()` implemented using the existing workspace/sandbox pieces.

**Dependency:** Existing `World`, `WorkspaceManager`, `world_digest`, and `Sandbox`.

**Validation:** A test command edits a file; digest changes; restore returns original contents; a failing command preserves its return code; `isinstance(world, World)` is true.

**Evidence:** Test output plus before/edit/restored digest fixture.

**Exit:** Tests pass with no edits to `Agent`, RGR, state schema, or effect code.

### Task 1

**Files:** Create `src/cairn/worlds/terminal.py`, `tests/test_terminal_world.py`; modify `src/cairn/worlds/__init__.py`.

- [ ] Write failing tests:

```python
def test_terminal_world_restores_snapshot(tmp_path):
    world = TerminalWorld.seeded(tmp_path, {"a.txt": "before\n"})
    snap = world.snapshot()
    assert world.execute("printf after > a.txt").returncode == 0
    world.restore(snap)
    assert (world.workspace_dir / "a.txt").read_text() == "before\n"
```

- [ ] Run `pytest tests/test_terminal_world.py -q`; expect import failure.
- [ ] Implement `execute()` as injected-shell `sandbox.run([shell, "-c", command], cwd=workspace_dir)` and delegate snapshot/restore/digest to existing workspace utilities.
- [ ] Add non-zero-return and digest-change tests.
- [ ] Run `pytest tests/test_terminal_world.py -q; pytest -q`; expect pass.
- [ ] Commit: `feat: add repository terminal world`.

## State 2 — Valid sequential fixtures

**Objective:** Ensure the experiment cannot fabricate recovery by finishing in one opaque action.

**Deliverable:** Four versioned 3–5-work-unit repository fixtures: bugfix, config, tests, followup. Each has `progress(root)`, hidden `verify(root)`, and an opaque-batch invalidation check.

**Dependency:** State 1.

**Validation:** A deterministic control trace advances one unit at a time; final verifier accepts only the full trace; an opaque batch is invalid rather than scored.

**Evidence:** Manifest, progress sequence, verifier receipt, invalid-batching receipt.

**Exit:** Every fixture exposes every non-terminal fault boundary and rejects fabricated batching.

### Task 2

**Files:** Create `benchmarks/recoverybench_fixtures/manifest.json`, four fixture directories; create/modify `src/cairn/eval/recoverybench.py`; modify `tests/test_recoverybench.py`.

- [ ] Write failing tests:

```python
def test_fixture_advances_one_unit(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)
    fixture.apply_control_action(root, 0)
    assert fixture.progress(root) == 1
    assert not fixture.verify(root).passed
```

- [ ] Run `pytest tests/test_recoverybench.py -q`; expect missing loader.
- [ ] Implement only `RepositoryFixture(name, version, work_units, progress, verify)` and task-local verifier scripts; no task DSL.
- [ ] Add parametrized acceptance test for all four full control traces and opaque-batch invalidation test.
- [ ] Run `pytest tests/test_recoverybench.py -q`; expect pass.
- [ ] Commit: `feat: add recoverybench repository fixtures`.

## State 3 — Clean checkpoint receipts

**Objective:** Make checkpoint eligibility auditable and impossible to confuse with an agent action.

**Deliverable:** `CleanCheckpoint(run_id, checkpoint_id, step, work_units, digest, provenance)` emitted only after command success, exactly-one unit advance, snapshot, and durable `checkpoint()` return.

**Dependency:** States 1–2 and existing `checkpoint()`.

**Validation:** Failed command, no progress, and opaque batch emit no receipt. A valid action emits one receipt whose checkpoint is loadable.

**Evidence:** Per-step receipt JSON and invalid-run records.

**Exit:** Crash injection takes a `CleanCheckpoint`; it cannot accept merely a step number.

### Task 3

**Files:** Modify `src/cairn/eval/recoverybench.py`, `tests/test_recoverybench.py`.

- [ ] Write failing tests:

```python
def test_failed_command_has_no_clean_checkpoint(tmp_path):
    run = start_control_run(tmp_path, commands=["exit 9"])
    assert run.clean_checkpoints == []
    assert run.invalid_reason == "command_failed"
```

- [ ] Run focused tests; expect missing control loop.
- [ ] Implement reference loop: execute; reject nonzero result; require `progress == expected_next_unit`; call existing `checkpoint()`; then emit receipt from persisted state/digest.
- [ ] Test opaque batch and `store.load_latest()` receipt ordering.
- [ ] Run `pytest tests/test_recoverybench.py -q; pytest -q`; expect pass.
- [ ] Commit: `feat: gate recoverybench checkpoints on verified work`.

## State 4 — Real process death and fresh-process RGR

**Objective:** Prove recovery depends on durable artifacts, not a caught exception or retained Python memory.

**Deliverable:** Parent/worker runner writes `failure_fired.json` after a clean checkpoint, terminates worker one, and starts worker two to execute existing `recover()` from persistent store/snapshots.

**Dependency:** State 3 and existing `recover()`.

**Validation:** Worker PIDs differ; resume receives no serialized history; absent receipt makes cell invalid; every deterministic non-terminal fault cell reaches hidden-verifier success.

**Evidence:** JSONL pairs with PIDs, receipt, checkpoint ID, digests, verifier receipt, and fidelity report.

**Exit:** The 4-fixture × every-nonterminal-boundary process matrix passes once.

### Task 4

**Files:** Modify `src/cairn/eval/recoverybench.py`; create `benchmarks/recoverybench.py`, `tests/test_recoverybench_process.py`.

- [ ] Write failing test:

```python
def test_recovery_uses_new_process(tmp_path):
    result = run_paired_control(tmp_path, "bugfix", fault_step=1)
    assert result.failure.fired
    assert result.failure.worker_pid != result.recovery.worker_pid
    assert result.recovery.used_in_memory_history is False
    assert result.verification.passed
```

- [ ] Run `pytest tests/test_recoverybench_process.py -q`; expect missing paired runner.
- [ ] Implement parent/worker JSON-file protocol with `subprocess.run`; crash worker writes receipt then exits fixed injected-failure status; resume worker is given only paths/configuration.
- [ ] Test missing receipt invalidation and all non-terminal deterministic fault positions.
- [ ] Run focused suite and `pytest -q`; expect pass.
- [ ] Commit: `feat: add process-isolated recoverybench runner`.

## State 5 — RecoveryBench v0.1 deterministic proof

**Objective:** Record recovery fidelity rather than assert it.

**Deliverable:** JSONL records with fixture/version, run/checkpoint IDs, receipt, provenance, raw verifier outputs, repository digests, and existing five-axis `RecoveryReport`; CLI matrix and documentation.

**Dependency:** State 4 and existing `score()`.

**Validation:** Missing receipt/digest/provenance records are invalid and unscored. Four fixtures × all valid fault points × 10 repetitions have success, artifact equivalence, and no-regression all equal to 1.0.

**Evidence:** Raw deterministic JSONL plus aggregate derived solely from raw records.

**Exit:** Hard-gate criteria 1–3 are met: deterministic cells pass; no-regression/equivalence are 1.0; every claim carries `failure_fired`.

### Task 5

**Files:** Modify `src/cairn/eval/recoverybench.py`, `benchmarks/recoverybench.py`, `benchmarks/README.md`, `tests/test_recoverybench.py`.

- [ ] Write failing schema test:

```python
def test_record_has_required_evidence(tmp_path):
    record = run_paired_control(tmp_path, "bugfix", 1).to_record()
    assert record["schema_version"] == "recoverybench.v0.1"
    assert record["failure"]["fired"] is True
    assert record["checkpoint"]["digest"]
```

- [ ] Run focused tests; expect missing record API.
- [ ] Implement `RecoveryBenchRecord` and JSONL writer. Score only valid pairs through existing equations; do not add a combined score.
- [ ] Test 10-repeat deterministic matrix exact values.
- [ ] Run twice: `python benchmarks/recoverybench.py --control --repeats 10 --output .tmp/a.jsonl` and equivalent `.tmp/b.jsonl`; normalized records must match.
- [ ] Commit: `feat: add recoverybench fidelity evidence`.

## State 6 — Controlled live pilot

**Objective:** Test external validity without changing the deterministic control or adding integrations.

**Deliverable:** Opt-in runner using the existing injected `ModelProvider`, storing model/provider/budget provenance and all valid/skipped/invalid/errored counts.

**Dependency:** State 5 plus explicit user-approved budget and reliable credentials.

**Validation:** ≥40 valid fired paired recoveries across two model configurations; recovered success is within 10 percentage points of paired uninterrupted success; no excluded bad cells.

**Evidence:** Immutable raw JSONL, prompt/harness/model versions, cost, count summary, and no-overclaim verdict.

**Exit:** Hard-gate criteria 4–5 are met, or an honest direction-changing failure report is published.

### Task 6

**Files:** Modify `src/cairn/eval/recoverybench.py`, `benchmarks/recoverybench.py`, `benchmarks/README.md`; create `tests/test_recoverybench_live.py`.

- [ ] Write opt-in smoke test guarded by `CAIRN_LIVE_MODEL`; ordinary CI must skip it.
- [ ] Run `pytest tests/test_recoverybench_live.py -q`; expect skip without credential.
- [ ] Implement `run_live_matrix(model_factory, fixtures, max_pairs, output)` by calling the exact paired runner from State 4; do not add an SDK/dependency.
- [ ] Test summary retains invalid/skipped/errored counts.
- [ ] Run ordinary tests. Execute `--live --models <a>,<b> --min-valid-pairs 40` only after budget approval.
- [ ] Commit runner wiring only; never commit credentials or paid-study output accidentally.

## State 7 — Binary evidence audit

**Objective:** Decide whether Phase 1 earned proof without averaging away a failure.

**Deliverable:** `phase_1_verdict(records)` and `results/phase-1/REPORT.md` with raw artifact manifest.

**Dependency:** States 1–6.

**Validation:** A passing deterministic set without live evidence fails. Only a seven-criterion complete record set passes.

**Evidence:** Matrix manifest, raw JSONL, source revision/task hashes, all count categories, and criterion-by-criterion audit.

**Exit:** Advance only if every locked Phase 1 criterion passes. Otherwise keep the control, publish the failure, and do not substitute integrations for missing evidence.

### Task 7

**Files:** Modify `src/cairn/eval/recoverybench.py`, `tests/test_recoverybench.py`, `CHECKLIST.md`; create `results/phase-1/REPORT.md`, `results/phase-1/manifest.json` after real runs.

- [ ] Write failing gate test: deterministic-passing records without 40 live pairs must fail.
- [ ] Run focused test; expect missing gate evaluator.
- [ ] Implement a seven-boolean `GateVerdict`; no weighted score or partial-pass result.
- [ ] Test complete synthetic evidence passes.
- [ ] Run `pytest -q` and deterministic 10-repeat command; audit raw output.
- [ ] Commit code/docs: `test: enforce phase one recovery proof gate`.

## Plan self-review

- Every state remains inside the Phase 1 locked boundary.
- The plan adds no later-phase semantics or infrastructure.
- Live work is budget-gated; all code and deterministic evidence are runnable offline.
