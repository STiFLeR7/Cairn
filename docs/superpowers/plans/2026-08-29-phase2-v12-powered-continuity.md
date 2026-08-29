# Phase 2 v0.12 Powered Continuity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Earn Continuation Contract v0 through a pre-registered 242-cell checkpoint-ready live study, causal replay of every eligible divergence, and a sealed holdout while preserving Phase 1 parity.

**Architecture:** Keep Cairn runtime semantics frozen. Add only a benchmark-level target selector to the existing action-parity replay control, pin separate live and holdout protocols, run the existing TerminalWorld matrix with Claude Code Opus and Sonnet, and admit the holdout only after every live gate passes.

**Tech Stack:** Python 3.12, pytest, stdlib JSON/hashlib, Claude Code CLI, Docker Desktop, existing Cairn TerminalWorld/RecoveryBench tooling.

**Spec:** `docs/superpowers/specs/2026-08-29-phase2-v12-powered-continuity-design.md`

## Global Constraints

- v0.11 remains immutable and is never merged into v0.12.
- No prompt, fixture, verifier, ContinuationState, RGR, framework, effect, or telemetry change.
- Live matrix: `claude_code:opus` plus `claude_code:sonnet`, 11 repetitions, all non-terminal splits of `bugfix`, `config`, `tests`, and `followup`, exactly 242 cells.
- Live gates: zero missing/incomplete cells; at least 100 U-eligible, 100 R successes, 100 C successes, and 100 complete triplets; every eligible divergence receives action-parity replay; no causal system defect.
- Holdout stays unread by model execution until the live gate passes and uses a separately pinned protocol.
- Raw primary, retry, transcript, provider-failure, and verifier evidence is never overwritten or deleted.
- Only provider/model-specific credentials or authenticated CLI state may enter a live process; never load or print the whole `.env`.

---

### Task 1: Generalize causal replay across R and C

**Files:**
- Modify: `benchmarks/phase2_replay_control.py`
- Modify: `tests/test_phase2_replay_control.py`

**Interfaces:**
- Consumes: `ContinuationState`, `continuation_prompt(state)`, `compacted_continuation(state)`, and `regrounded_history(plan)`.
- Produces: `replay_continuation_branch(..., target_branch: str) -> dict`; preserves `replay_compacted_branch(...) -> dict`; CLI adds `--target-branch {R,C}` and allows `--source-branch {U,R,C}`.

- [ ] **Step 1: Write the failing target-branch test**

Replace the single assertion path with a parametrized test that calls the new interface for both recovery and compaction:

```python
import pytest

from benchmarks.phase2_replay_control import replay_continuation_branch


@pytest.mark.parametrize("target_branch", ["R", "C"])
def test_replaying_verified_actions_completes_target_branch(tmp_path, target_branch):
    record = run_live_urc(
        tmp_path / "source", "bugfix", split_step=0,
        config=LiveRunConfig(provider="fake", model="control"),
        prefix_mode="control",
    )
    source_root = tmp_path / "source" / record["run_id"]
    fixture = load_fixture("bugfix")
    replies = [
        f"```python\nfrom pathlib import Path\nPath('project.py').write_text({fixture.steps[step]!r})\n```"
        for step in (1, 2)
    ]

    replay = replay_continuation_branch(
        source_root, "bugfix", split_step=0, replies=replies,
        output_dir=tmp_path / "replay", target_branch=target_branch,
    )

    assert replay["target_branch"] == target_branch
    assert replay["success"] is True, replay
    assert replay["verified"] is True
    assert replay["final_digest"] == world_digest(str(source_root / "U" / "bugfix"))
    assert Path(replay["workspace"]).is_dir()
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
$env:PYTHONPATH='D:\project-unknown-phase1\src;D:\project-unknown-phase1'
python -m pytest tests\test_phase2_replay_control.py -q
```

Expected: collection fails because `replay_continuation_branch` does not exist.

- [ ] **Step 3: Implement the minimum target selector**

In `benchmarks/phase2_replay_control.py`, keep the existing workspace setup and execution loop, but choose fresh continuation inputs as follows:

```python
from cairn.eval.phase2 import compacted_continuation, continuation_prompt
from cairn.harness.agent_loop import regrounded_history


def _continuation_inputs(checkpoint, target_branch: str):
    if target_branch == "C":
        branch = compacted_continuation(checkpoint)
        return branch.prompt, branch.history
    if target_branch == "R":
        return continuation_prompt(checkpoint), regrounded_history(checkpoint.durable_core.plan)
    raise ValueError(f"unknown replay target: {target_branch}")


def replay_continuation_branch(
    run_root: Path,
    fixture_name: str,
    *,
    split_step: int,
    replies: list[str],
    output_dir: Path,
    target_branch: str,
) -> dict:
    # Use the existing replay_compacted_branch body, replacing its fixed compacted
    # continuation with `_continuation_inputs(loaded[0], target_branch)` and record
    # `target_branch` in the returned dictionary.
```

Retain the old public function as a compatibility wrapper:

```python
def replay_compacted_branch(run_root, fixture_name, *, split_step, replies, output_dir):
    return replay_continuation_branch(
        run_root, fixture_name, split_step=split_step, replies=replies,
        output_dir=output_dir, target_branch="C",
    )
```

Update the CLI:

```python
parser.add_argument("--source-branch", default="R", choices=("U", "R", "C"))
parser.add_argument("--target-branch", default="C", choices=("R", "C"))
```

Pass `target_branch=args.target_branch` and include it in the top-level evidence object.

- [ ] **Step 4: Run focused tests and lint**

Run:

```powershell
python -m pytest tests\test_phase2_replay_control.py -q
ruff check benchmarks\phase2_replay_control.py tests\test_phase2_replay_control.py --cache-dir D:\project-unknown\.ruff-cache-phase2
```

Expected: two replay cases pass and Ruff reports `All checks passed!`.

- [ ] **Step 5: Commit the isolated replay tool change**

```powershell
git add benchmarks/phase2_replay_control.py tests/test_phase2_replay_control.py
git commit -m "test: replay recovery and compaction divergences"
```

---

### Task 2: Freeze live and holdout protocols before model execution

**Files:**
- Create: `results/phase-2/matrix-protocol-v12-powered-control-prefix.json`
- Create: `results/phase-2/holdout-protocol-v12.json`
- Create: `tests/test_phase2_protocol_v12.py`

**Interfaces:**
- Consumes: `matrix_cells(protocol) -> list[dict]` and the five hashes approved in the design.
- Produces: a 242-cell live protocol and a sealed holdout protocol accepted by the existing matrix runner and analyzer.

- [ ] **Step 1: Write the failing protocol-integrity test**

```python
import hashlib
import json
from pathlib import Path

from cairn.eval.phase2 import matrix_cells


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "phase-2"


def _sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_v12_live_protocol_is_hash_pinned_and_has_242_cells():
    protocol = json.loads((RESULTS / "matrix-protocol-v12-powered-control-prefix.json").read_text())
    assert protocol["status"] == "live-tranche-pinned"
    assert protocol["matrix"]["prefix_mode"] == "control"
    assert len(matrix_cells(protocol)) == protocol["matrix"]["expected_attempts"] == 242
    for item in protocol["pinned_inputs"].values():
        assert _sha(item["path"]) == item["sha256"]


def test_v12_holdout_protocol_is_sealed_and_reuses_v11_source_hashes():
    holdout = json.loads((RESULTS / "holdout-protocol-v12.json").read_text())
    v11 = json.loads((RESULTS / "matrix-protocol-v11-neutral-tranche.json").read_text())
    assert holdout["status"] == "sealed-unconsumed"
    assert holdout["holdout"]["consume"] is False
    assert holdout["holdout"]["task_sources"] == v11["task_selection"]["holdout"]["task_sources"]
    assert holdout["gate"]["minimum_complete_triplets"] == 10
```

- [ ] **Step 2: Run the protocol test and verify RED**

Run: `python -m pytest tests\test_phase2_protocol_v12.py -q`

Expected: both tests fail because the protocol files do not exist.

- [ ] **Step 3: Create the pinned live protocol**

Create `matrix-protocol-v12-powered-control-prefix.json` with these exact operative fields:

```json
{
  "schema_version": "cairn.phase-2-powered-continuity.v0.12",
  "status": "live-tranche-pinned",
  "purpose": "Powered checkpoint-ready replication after the terminal v0.11 acquisition finding.",
  "does_not_replace": "matrix-protocol-v11-neutral-tranche.json",
  "pinned_inputs": {
    "phase1_control_freeze": {"path": "results/phase-2/control-freeze-recheck.json", "sha256": "7f969a9c861ad8e85a8103e3b421c78d3a1f2ddb8a37b3d2316e0e8c80bbcc56"},
    "recoverybench_harness": {"path": "src/cairn/eval/recoverybench.py", "sha256": "86819b8938cd803ad2ddb1acc260fd85d1dc25d74d59f275bc5c3207687772c6"},
    "urc_runner": {"path": "src/cairn/eval/phase2.py", "sha256": "91a66602810f1a2caecfab4e60964bf7c9c0c7b62813643f44fe8f10746f0a32"},
    "matrix_executor": {"path": "benchmarks/phase2_matrix.py", "sha256": "b5e5f27c217be08bf4c79d7435bbef70f6e36fd893ea6f4f6d4b5db37171fc6f"},
    "analyzer": {"path": "benchmarks/phase2_acquisition_continuity.py", "sha256": "89379ea13c8910d3d367d28cc93f04ca4d0fdff6fddace4206a0d44cc45fbe06"}
  },
  "matrix": {
    "models": [{"provider": "claude_code", "model": "opus"}, {"provider": "claude_code", "model": "sonnet"}],
    "fixtures": ["bugfix", "config", "tests", "followup"],
    "split_steps": "all_nonterminal",
    "branches": ["U", "R", "C"],
    "prefix_mode": "control",
    "prompt_composition": "legacy",
    "verification_mode": "empty",
    "repetitions_per_model_fixture_split": 11,
    "expected_attempts": 242,
    "output_directory": "matrix-v12-powered-control-prefix"
  },
  "gate": {
    "complete_matrix": true,
    "minimum_eligible_checkpoints": 100,
    "minimum_conditional_recovery_successes": 100,
    "minimum_conditional_compaction_successes": 100,
    "minimum_complete_triplets": 100,
    "causal_replay_every_eligible_divergence": true,
    "phase1_parity_required": true
  },
  "forbidden": ["v0.11 extension", "prompt changes", "fixture changes", "verifier changes", "schema changes", "RGR changes without causal replay", "framework integrations", "effect semantics", "threshold changes"]
}
```

- [ ] **Step 4: Create the sealed holdout protocol**

Create `holdout-protocol-v12.json` before any v0.12 model call:

```json
{
  "schema_version": "cairn.phase-2-holdout.v0.12",
  "status": "sealed-unconsumed",
  "entry": "All matrix-protocol-v12-powered-control-prefix.json gates pass.",
  "holdout": {
    "task": "phase2_holdout",
    "consume": false,
    "task_sources": {
      "benchmarks/recoverybench_fixtures/phase2_holdout/README.md": "0a36bab771d6bf539994235a93c4f90a9d03f2f9aaa4acde91251a753d862a15",
      "benchmarks/recoverybench_fixtures/phase2_holdout/project.py": "2ac983a16fdac2c6089f87d05c367138b89603bf1e24ddabbd93d9ba52bdc475"
    }
  },
  "matrix": {
    "models": [{"provider": "claude_code", "model": "opus"}, {"provider": "claude_code", "model": "sonnet"}],
    "fixtures": ["phase2_holdout"],
    "split_steps": "all_nonterminal",
    "branches": ["U", "R", "C"],
    "prefix_mode": "control",
    "prompt_composition": "legacy",
    "verification_mode": "empty",
    "repetitions_per_model_fixture_split": 10,
    "output_directory": "matrix-v12-holdout"
  },
  "gate": {
    "complete_matrix": true,
    "minimum_eligible_checkpoints": 10,
    "minimum_conditional_recovery_successes": 10,
    "minimum_conditional_compaction_successes": 10,
    "minimum_complete_triplets": 10,
    "causal_replay_every_eligible_divergence": true,
    "zero_causal_system_defects": true
  },
  "on_failure": "Do not publish Continuation Contract v0 and never reuse this holdout after tuning."
}
```

- [ ] **Step 5: Run protocol tests and scoped lint**

Run:

```powershell
python -m pytest tests\test_phase2_protocol_v12.py tests\test_phase2_matrix_paths.py -q
ruff check tests\test_phase2_protocol_v12.py --cache-dir D:\project-unknown\.ruff-cache-phase2
```

Expected: tests and lint pass; live enumeration is exactly 242.

- [ ] **Step 6: Commit the frozen protocols and integrity test**

```powershell
git add results/phase-2/matrix-protocol-v12-powered-control-prefix.json results/phase-2/holdout-protocol-v12.json tests/test_phase2_protocol_v12.py
git commit -m "test: pin phase 2 v0.12 protocols"
```

---

### Task 3: Execute the registered 242-cell live matrix

**Files:**
- Create: `results/phase-2/matrix-v12-powered-control-prefix/*.json`
- Create: `results/phase-2/matrix-v12-powered-control-prefix/runs/**`

**Interfaces:**
- Consumes: the frozen v0.12 protocol and authenticated Claude Code CLI.
- Produces: one preserved terminal primary/retry record per registered cell plus local transcripts and workspaces.

- [ ] **Step 1: Verify external prerequisites without a model call**

Run:

```powershell
claude --version
docker ps
```

Expected: Claude Code prints a version and Docker returns without a named-pipe error. If Docker is stopped, start `C:\Program Files\Docker\Docker\Docker Desktop.exe` with `-WindowStyle Hidden`, then poll `docker info` for at most 120 seconds.

- [ ] **Step 2: Re-run offline integrity checks**

Run:

```powershell
$env:PYTHONPATH='D:\project-unknown-phase1\src;D:\project-unknown-phase1'
$env:TEMP='D:\project-unknown\.pytest-tmp'
$env:TMP='D:\project-unknown\.pytest-tmp'
python -m pytest tests\test_phase2_protocol_v12.py tests\test_docker_terminal_sandbox.py tests\test_phase2_matrix_paths.py -q --basetemp D:\project-unknown\.pytest-tmp\v12-preflight
```

Expected: all preflight tests pass.

- [ ] **Step 3: Run the Opus half resume-safely**

```powershell
python benchmarks\phase2_matrix.py `
  --protocol results\phase-2\matrix-protocol-v12-powered-control-prefix.json `
  --model opus `
  --output-dir results\phase-2\matrix-v12-powered-control-prefix
```

Monitor the Python process and durable flat-file count. Never launch a duplicate writer. If interrupted, rerun the exact command; `next_evidence_path()` preserves partial evidence and uses at most one `.retry.json`.

- [ ] **Step 4: Run the Sonnet half resume-safely**

Use the same command with `--model sonnet`. Do not run both models concurrently against the same Claude subscription.

- [ ] **Step 5: Verify matrix completeness without interpreting outcomes**

Run the analyzer:

```powershell
python benchmarks\phase2_acquisition_continuity.py `
  --matrix-dir results\phase-2\matrix-v12-powered-control-prefix `
  --protocol results\phase-2\matrix-protocol-v12-powered-control-prefix.json `
  --output results\phase-2\v12-acquisition-continuity.json
```

Require `attempts == 242`, `missing_cells == []`, and `incomplete == 0`. Otherwise resume only missing/incomplete registered cells; never change the protocol.

---

### Task 4: Apply the live gate and causal replay

**Files:**
- Create: `results/phase-2/v12-acquisition-continuity.json`
- Create conditionally: `results/phase-2/v12-replay-r-from-c.json`
- Create conditionally: `results/phase-2/v12-replay-c-from-r.json`
- Create conditionally: `results/phase-2/v12-replay-r-from-u.json`
- Create conditionally: `results/phase-2/v12-replay-c-from-u.json`
- Modify: `results/phase-2/REPORT.md`

**Interfaces:**
- Consumes: selected v0.12 records and their recorded U/R/C transcripts.
- Produces: live gate verdict and action-parity evidence for every eligible divergence.

- [ ] **Step 1: Partition eligible divergences deterministically**

For each `selected_sources` record with `branches.U.success == true`:

- R false, C true → replay C replies through target R.
- R true, C false → replay R replies through target C.
- R false, C false → replay U replies once through target R and once through target C.

Save each source filename list in the REPORT reproduction section before running replay commands.

- [ ] **Step 2: Run every non-empty replay group**

Use the frozen analyzer selection to construct and execute all four groups without hand-picking
records:

```powershell
$matrixDir = 'results\phase-2\matrix-v12-powered-control-prefix'
$analysis = Get-Content 'results\phase-2\v12-acquisition-continuity.json' -Raw | ConvertFrom-Json
$rOnly = @()
$cOnly = @()
$both = @()
foreach ($name in $analysis.selected_sources) {
  $path = Join-Path $matrixDir $name
  $record = Get-Content $path -Raw | ConvertFrom-Json
  if ($record.branches.U.success -eq $true) {
    if ($record.branches.R.success -eq $false -and $record.branches.C.success -eq $true) { $rOnly += $path }
    if ($record.branches.R.success -eq $true -and $record.branches.C.success -eq $false) { $cOnly += $path }
    if ($record.branches.R.success -eq $false -and $record.branches.C.success -eq $false) { $both += $path }
  }
}
$groups = @(
  @{ Records=$rOnly; Source='C'; Target='R'; Output='results\phase-2\v12-replay-r-from-c.json' },
  @{ Records=$cOnly; Source='R'; Target='C'; Output='results\phase-2\v12-replay-c-from-r.json' },
  @{ Records=$both; Source='U'; Target='R'; Output='results\phase-2\v12-replay-r-from-u.json' },
  @{ Records=$both; Source='U'; Target='C'; Output='results\phase-2\v12-replay-c-from-u.json' }
)
foreach ($group in $groups) {
  if ($group.Records.Count) {
    python benchmarks\phase2_replay_control.py `
      --matrix-dir $matrixDir --records $group.Records `
      --source-branch $group.Source --target-branch $group.Target --output $group.Output
  }
}
```

Require `verified == replayed` for every group. Any failure is causal system evidence: stop, keep the holdout sealed, and localize the defect before proposing a correction.

- [ ] **Step 3: Apply the frozen live count gate**

Require all of:

```text
attempts == 242
missing_cells == []
incomplete == 0
acquisition.eligible >= 100
continuity.recovery_successes >= 100
continuity.compaction_successes >= 100
continuity.complete_triplets >= 100
all replay groups verified == replayed
```

If any condition fails, record the terminal finding in REPORT.md, leave the holdout sealed, and do not publish the contract.

- [ ] **Step 4: Recheck Phase 1 parity and repository tests**

Regenerate the freeze recheck to a new artifact using the four frozen Phase 1 JSONL inputs listed in REPORT.md, then require its SHA-relevant content to match `control-freeze-recheck.json`. Run:

```powershell
python -m pytest -q --basetemp D:\project-unknown\.pytest-tmp\v12-live-gate
ruff check benchmarks\phase2_replay_control.py tests\test_phase2_replay_control.py tests\test_phase2_protocol_v12.py --cache-dir D:\project-unknown\.ruff-cache-phase2
git diff --check
```

Expected: full suite passes, scoped Ruff passes, and diff check reports no whitespace errors.

- [ ] **Step 5: Record the live verdict**

Append to REPORT.md: protocol identity and hashes, all acquisition/continuity counts, divergence identities, replay outcomes, Phase 1 parity result, test result, and the explicit holdout entry decision. Do not claim a contract yet.

---

### Task 5: Run the sealed holdout and publish only on success

**Files:**
- Create conditionally: `results/phase-2/matrix-v12-holdout/*.json`
- Create conditionally: `results/phase-2/v12-holdout-acquisition-continuity.json`
- Create conditionally: `results/phase-2/v12-holdout-replay-*.json`
- Create conditionally: `docs/design/continuation-contract-v0.md`
- Modify: `results/phase-2/REPORT.md`

**Interfaces:**
- Consumes: a passing v0.12 live gate and the sealed holdout protocol.
- Produces: blinded validation and, only after it passes, Continuation Contract v0.

- [ ] **Step 1: Prove holdout admission before first model call**

Run a machine check that reads only `v12-acquisition-continuity.json` and replay summaries and exits non-zero unless every Task 4 count/replay gate passes. Record the command and output in REPORT.md. Do not edit `holdout-protocol-v12.json` or change `consume: false`; that flag records pre-run sealing, while the admission artifact authorizes execution.

- [ ] **Step 2: Execute both registered holdout model configurations**

Run `benchmarks\phase2_matrix.py` with `holdout-protocol-v12.json`, first `--model opus`, then `--model sonnet`, and output directory `results\phase-2\matrix-v12-holdout`. Preserve and resume records exactly as in Task 3.

- [ ] **Step 3: Analyze and replay holdout divergences**

Run the existing analyzer to `v12-holdout-acquisition-continuity.json`. Require a complete registered matrix plus at least 10 U-eligible, 10 R successes, 10 C successes, and 10 complete triplets. Partition and replay every eligible divergence with the exact Task 4 rules; require every replay to verify.

- [ ] **Step 4: Publish the behavioral contract only after both gates pass**

Create `docs/design/continuation-contract-v0.md` with these normative requirements:

```markdown
# Cairn Continuation Contract v0

Status: externally validated reference contract.

## Scope

This contract applies to repository coding-agent continuation from a clean, verified checkpoint.
It does not guarantee that a model can acquire that checkpoint and does not cover external-effect safety.

## Required preserved semantics

A compacted or recovered continuation MUST preserve equivalent task intent, active subgoal,
accepted decisions, verified work, verification state, repository/world identity, stop conditions,
and the next independently verifiable action boundary. Implementations MAY use any internal schema.

## Fresh-process requirements

Recovery and compaction MUST work in a fresh process without the original in-memory transcript.
The implementation MUST re-ground repository state before acting, MUST NOT treat unverified
mutation as progress, and MUST retain enough provenance to identify the checkpoint and world digest.

## Conformance

An implementation conforms only when U, R, and C start from the same verified checkpoint; a
harness-owned hidden verifier evaluates all branches; acquisition failures are reported separately;
raw failures are preserved; and eligible divergences receive identical-action counterfactual replay.

## Evidence and limitations

Reference evidence: `results/phase-2/v12-acquisition-continuity.json`, the v0.12 replay artifacts,
`results/phase-2/v12-holdout-acquisition-continuity.json`, and `results/phase-2/REPORT.md`.
The reference harness validates Claude Code Opus and Sonnet on the pinned repository tasks and
holdout. This is not a framework API, memory-library schema, or external-effect contract.
```

- [ ] **Step 5: Run the completion audit**

Run the full suite, scoped Ruff, `git diff --check`, verify all protocol hashes, verify every live and holdout record is selected exactly once, verify every count gate, and verify all replay summaries have `verified == replayed`. Update REPORT.md with the final evidence table and contract scope.

- [ ] **Step 6: Commit only reviewed source, protocol, summary, and contract artifacts**

Do not stage run workspaces, secrets, `.env`, Docker state, or unrelated dirty files. Stage the replay tool/test, protocol/test, REPORT.md, final small JSON summaries/replay artifacts, and contract; inspect `git diff --cached` before committing:

```powershell
git commit -m "feat: publish continuation contract v0 evidence"
```
