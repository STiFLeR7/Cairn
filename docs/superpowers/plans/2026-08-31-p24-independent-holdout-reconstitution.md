# P2.4 Independent Holdout Reconstitution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create, seal, execute, and causally evaluate a clean-room repository holdout without changing Cairn or admitted Phase 1/2 behavior.

**Architecture:** P2.4 adds a task-local fixture registration module and a fresh-process U/R/C orchestrator outside frozen Cairn. A clean-room author creates the public task; all verifier expectations are derived verbatim from that public task, then pinned before any Opus or Sonnet call.

**Tech Stack:** Python 3.12, stdlib JSON/hashlib/runpy/subprocess, pytest, Ruff, existing Docker TerminalWorld, existing Claude Code CLI.

**Spec:** `docs/superpowers/specs/2026-08-31-p24-independent-holdout-reconstitution-design.md`

## Global Constraints

- Do not modify any path named by the P2.4 freeze manifest.
- Use `apply_patch` for repository edits; preserve the dirty worktree and stage only task-owned files.
- The clean-room author sees no Cairn, v12, repository, or prior-model context; Opus and Sonnet are the only evaluated models.
- Do not run an evaluated model before protocol sealing and an explicit admission artifact.
- The matrix is exactly two models × three nonterminal splits × ten repetitions = 60 cells.
- Keep raw primary and retry records; select only the exact registered retry path.
- Preserve existing Phase 2 thresholds; never lower them or combine evidence across holdouts.
- If a post-seal gate fails, classify causally and stop. Do not tune or reuse that holdout.

---

### Task 1: Freeze and clean-room task source

**Files:**
- Create: `benchmarks/p24_freeze.py`
- Create: `benchmarks/p24_author.py`
- Create: `results/phase-2/p24-freeze.json`
- Create: `results/phase-2/p24-author-prompt.txt`
- Create: `results/phase-2/p24-author-output.json`
- Create: `results/phase-2/p24-author-audit.json`
- Test: `tests/test_p24_freeze.py`

**Interfaces:**
- Produces `freeze_manifest(paths: list[Path], metadata: dict) -> dict` with SHA-256 and byte counts.
- Produces `audit_author_output(payload: dict) -> dict` with `admitted: bool`, literal acceptance cases, and rejection reasons.
- Consumes no fixture implementation or evaluated-model evidence.

- [ ] **Step 1: Write failing tests for freeze drift and author audit.**

```python
def test_freeze_manifest_detects_a_changed_frozen_file(tmp_path):
    frozen = tmp_path / "frozen.py"
    frozen.write_text("a = 1\n", encoding="utf-8")
    manifest = freeze_manifest([frozen], {"branch": "test"})
    frozen.write_text("a = 2\n", encoding="utf-8")
    assert frozen_paths_match(manifest) is False


def test_author_audit_rejects_an_unpublished_scored_case():
    payload = valid_author_payload()
    payload["acceptance_cases"].append({"function": "priority_band", "args": [99], "expected": "urgent"})
    assert audit_author_output(payload)["admitted"] is False
```

- [ ] **Step 2: Run the tests and verify they fail because P2.4 helpers do not exist.**

Run: `python -m pytest tests/test_p24_freeze.py -q`

Expected: import/collection failure naming `p24_freeze` or `p24_author`.

- [ ] **Step 3: Implement the smallest freeze and audit helpers.**

`p24_freeze.py` hashes only the exact frozen paths from the spec and compares current bytes to the manifest. `p24_author.py` validates a fixed JSON schema: title, public README, starter source, ordered four functions, and literal acceptance cases. It rejects hidden cases, missing domain text, duplicate functions, nonliteral expected values, v12 names, and absent boundary/empty cases.

- [ ] **Step 4: Run focused tests and record the pre-author freeze.**

Run: `python -m pytest tests/test_p24_freeze.py -q`

Expected: PASS.

Generate `p24-freeze.json`, then write the author prompt. Invoke Claude Code Haiku once from a new empty temporary directory with tools disabled. Preserve its raw JSON output and run the audit. No Opus or Sonnet command runs in this task.

- [ ] **Step 5: Commit only Task 1 source, tests, and pre-execution artifacts.**

Run: `git add benchmarks/p24_freeze.py benchmarks/p24_author.py tests/test_p24_freeze.py results/phase-2/p24-freeze.json results/phase-2/p24-author-prompt.txt results/phase-2/p24-author-output.json results/phase-2/p24-author-audit.json && git commit -m "test: freeze P2.4 clean-room holdout inputs"`

Expected: one commit containing only listed files.

### Task 2: Ordered public fixture and deterministic verifier

**Files:**
- Create: `benchmarks/recoverybench_fixtures/p24_queue_policy/README.md`
- Create: `benchmarks/recoverybench_fixtures/p24_queue_policy/project.py`
- Create: `benchmarks/p24_fixture.py`
- Test: `tests/test_p24_fixture.py`

**Interfaces:**
- Produces `register_p24_fixture() -> None`, which adds only `p24_queue_policy` to the in-process fixture maps before `load_fixture` is called.
- Produces `p24_progress(root: Path) -> int`, which returns the count of the leading consecutive public contracts that pass.
- Consumes admitted author output and creates four complete ordered control-source states.

- [ ] **Step 1: Write failing ordered-progress tests.**

```python
def test_p24_fixture_advances_only_the_next_public_contract(tmp_path):
    register_p24_fixture()
    fixture = load_fixture("p24_queue_policy")
    root = fixture.copy_to(tmp_path)
    assert fixture.progress(root) == 0
    fixture.apply_control_action(root, 0)
    assert fixture.progress(root) == 1


def test_p24_fixture_rejects_a_later_contract_before_its_predecessor(tmp_path):
    register_p24_fixture()
    fixture = load_fixture("p24_queue_policy")
    root = fixture.copy_to(tmp_path)
    (root / "project.py").write_text(fixture.steps[2], encoding="utf-8")
    assert fixture.progress(root) == 0
```

- [ ] **Step 2: Run the tests and verify they fail because `p24_fixture` does not exist.**

Run: `python -m pytest tests/test_p24_fixture.py -q`

Expected: import/collection failure naming `p24_fixture`.

- [ ] **Step 3: Materialize the clean-room task exactly and implement the local registration.**

The public README must publish every acceptance case the verifier evaluates, including inputs,
expected outputs, boundary behavior, empty behavior, order, and unscored domains. `p24_progress`
must stop at the first failed contract; it must not sum independently passing later contracts. Control
states replace exactly one next function and preserve all earlier source.

- [ ] **Step 4: Run focused fixture tests, including every published case and full control trace.**

Run: `python -m pytest tests/test_p24_fixture.py -q`

Expected: PASS.

- [ ] **Step 5: Commit only Task 2 files.**

Run: `git add benchmarks/recoverybench_fixtures/p24_queue_policy benchmarks/p24_fixture.py tests/test_p24_fixture.py && git commit -m "feat: add independent P2.4 queue-policy fixture"`

Expected: one commit containing only listed files.

### Task 3: Fresh-process U/R/C reference harness

**Files:**
- Create: `benchmarks/p24_matrix.py`
- Test: `tests/test_p24_matrix.py`

**Interfaces:**
- Produces `run_p24_cell(cell: dict, protocol: dict, output_dir: Path) -> dict`.
- Produces a `--branch-worker` CLI mode for R and C.
- Consumes the frozen `checkpoint`, `recover`, `compacted_continuation`, `run_live_step`, and `TerminalWorld` behavior.
- Produces branch records with start/final progress and digest, parent/worker PIDs, transcript availability, state serialization, and verifier result.

- [ ] **Step 1: Write failing tests for process isolation and continuation evidence.**

```python
def test_fake_cell_runs_r_and_c_in_distinct_processes(tmp_path):
    record = run_p24_cell(fake_cell(), fake_protocol(), tmp_path)
    assert record["branches"]["R"]["worker_pid"] != record["parent_pid"]
    assert record["branches"]["C"]["worker_pid"] != record["parent_pid"]
    assert record["branches"]["R"]["used_in_memory_history"] is False
    assert record["branches"]["C"]["original_transcript_available"] is False


def test_fake_cell_preserves_prefix_and_next_ordered_action(tmp_path):
    record = run_p24_cell(fake_cell(split_step=1), fake_protocol(), tmp_path)
    for branch in record["branches"].values():
        assert branch["start_progress"] == 2
        assert branch["accepted_progress"] == [3, 4]
        assert branch["final_progress"] == 4
        assert branch["verified"] is True
```

- [ ] **Step 2: Run the tests and verify they fail because `p24_matrix` does not exist.**

Run: `python -m pytest tests/test_p24_matrix.py -q`

Expected: import/collection failure naming `p24_matrix`.

- [ ] **Step 3: Implement the minimal parent/worker boundary.**

The parent runs the one shared deterministic control prefix and U continuation. It copies only the
workspace/checkpoint/ledger data into R and C worker directories. R loads durable recovery through
the frozen `recover`; C loads a JSON-serialized checkpoint through frozen `compacted_continuation`.
Workers receive no parent history object and no prefix transcript path. Every branch writes its own
settled evidence atomically before the parent assembles the cell record.

- [ ] **Step 4: Run focused fake-model tests.**

Run: `python -m pytest tests/test_p24_matrix.py -q`

Expected: PASS, with one ordered work unit accepted per continuation step and final verifier success.

- [ ] **Step 5: Commit only Task 3 files.**

Run: `git add benchmarks/p24_matrix.py tests/test_p24_matrix.py && git commit -m "feat: add fresh-process P2.4 U/R/C runner"`

Expected: one commit containing only listed files.

### Task 4: Sealed protocol, analysis, and exact action-parity replay

**Files:**
- Create: `benchmarks/p24_analysis.py`
- Create: `benchmarks/p24_replay.py`
- Create: `results/phase-2/p24-holdout-protocol.json`
- Test: `tests/test_p24_protocol.py`
- Test: `tests/test_p24_analysis.py`

**Interfaces:**
- Produces `analyze_p24_records(records: list[dict]) -> dict` with existing count metrics plus
  checkpoint identity, preserved work, next-action, termination, fresh-process, transcript, and digest metrics.
- Produces `replay_p24_branch(record_path: Path, source: str, target: str, output_dir: Path) -> dict`.
- Consumes selected primary/retry records and source transcripts.
- Produces a sealed protocol and a machine-readable gate verdict.

- [ ] **Step 1: Write failing protocol and replay tests.**

```python
def test_p24_protocol_pins_all_frozen_and_new_inputs():
    protocol = load_protocol()
    assert protocol["status"] == "sealed-unconsumed"
    assert protocol["matrix"]["expected_attempts"] == 60
    assert all(hash_matches(item) for item in protocol["pinned_inputs"].values())


def test_replay_requires_source_digest_equivalence(tmp_path):
    replay = replay_p24_branch(successful_record(), "U", "C", tmp_path)
    assert replay["verified"] is True
    assert replay["final_digest"] == replay["source_final_digest"]
```

- [ ] **Step 2: Run the tests and verify they fail because P2.4 analysis/replay and protocol do not exist.**

Run: `python -m pytest tests/test_p24_protocol.py tests/test_p24_analysis.py -q`

Expected: import/collection failure naming `p24_analysis`, `p24_replay`, or missing protocol.

- [ ] **Step 3: Implement analysis and replay, then create the sealed protocol.**

Analysis selects the registered primary or exact retry, never an arbitrary file. It separates U
acquisition from conditional R/C outcomes and makes all structural evidence explicit. Replay uses
the frozen treatment reconstruction and recorded successful source actions; it fails on verifier or
digest mismatch. Create the protocol only after all deterministic tests pass, pin every named input,
and record a freeze recheck. Do not run Opus or Sonnet yet.

- [ ] **Step 4: Run focused tests, full tests, scoped Ruff, and diff check before sealing.**

Run: `python -m pytest tests/test_p24_protocol.py tests/test_p24_analysis.py tests/test_p24_fixture.py tests/test_p24_matrix.py -q && python -m pytest -q && ruff check benchmarks/p24_freeze.py benchmarks/p24_author.py benchmarks/p24_fixture.py benchmarks/p24_matrix.py benchmarks/p24_analysis.py benchmarks/p24_replay.py tests/test_p24_freeze.py tests/test_p24_fixture.py tests/test_p24_matrix.py tests/test_p24_protocol.py tests/test_p24_analysis.py && git diff --check`

Expected: every command exits zero.

- [ ] **Step 5: Commit only Task 4 files and sealed artifacts.**

Run: `git add benchmarks/p24_analysis.py benchmarks/p24_replay.py tests/test_p24_protocol.py tests/test_p24_analysis.py results/phase-2/p24-holdout-protocol.json && git commit -m "test: seal independent P2.4 holdout protocol"`

Expected: one commit containing only listed files.

### Task 5: Live admission, execution, causal classification, and publication decision

**Files:**
- Create conditionally: `results/phase-2/p24-holdout-admission.json`
- Create: `results/phase-2/p24-matrix/*.json`
- Create: `results/phase-2/p24-analysis.json`
- Create conditionally: `results/phase-2/p24-replay-*.json`
- Create: `results/phase-2/p24-verdict.json`
- Modify: `results/phase-2/REPORT.md`
- Create conditionally: `docs/design/continuation-contract-v0.md`

**Interfaces:**
- Consumes only sealed protocol inputs and the frozen runtime.
- Produces raw records, selected-record analysis, replay evidence, causal verdict, reproduction commands, and optional contract.

- [ ] **Step 1: Write and run an admission check before the first evaluated-model call.**

The admission artifact must verify the freeze hashes, author audit admission, deterministic suite,
sealed status, exact 60-cell enumeration, and absence of `p24-matrix` records. It exits nonzero if
any condition is false. Record its command and output in `REPORT.md`.

- [ ] **Step 2: Execute all registered Opus cells, preserving raw records and exact retries.**

Run: `python benchmarks/p24_matrix.py --protocol results/phase-2/p24-holdout-protocol.json --model opus --output-dir results/phase-2/p24-matrix`

Expected: 30 registered Opus records settle; any interruption creates only the exact `.retry.json` continuation.

- [ ] **Step 3: Execute all registered Sonnet cells under the same protocol.**

Run: `python benchmarks/p24_matrix.py --protocol results/phase-2/p24-holdout-protocol.json --model sonnet --output-dir results/phase-2/p24-matrix`

Expected: 30 registered Sonnet records settle.

- [ ] **Step 4: Analyze, partition, and replay every eligible divergence.**

Run: `python benchmarks/p24_analysis.py --matrix-dir results/phase-2/p24-matrix --protocol results/phase-2/p24-holdout-protocol.json --output results/phase-2/p24-analysis.json`

For U-success/R-fail/C-success, replay C→R. For U-success/R-success/C-fail, replay R→C. For
U-success/R-fail/C-fail, replay U→R and U→C. Require each replay to verify and reproduce the source
final digest exactly.

- [ ] **Step 5: Apply the immutable hard gate and publish the correct terminal artifact.**

Require the complete 60-cell matrix, at least 10 eligible U checkpoints, at least 10 R and C
successes, at least 10 complete triplets, all structural requirements, every replay success/digest
match, zero causal Cairn defects, unchanged freeze, and a fresh full test pass. If all pass, create
`docs/design/continuation-contract-v0.md` and append reproducible evidence to `REPORT.md`. Otherwise
write only `p24-verdict.json` and a causal `REPORT.md` section; do not publish the contract or alter
the sealed task.

- [ ] **Step 6: Commit evidence and the terminal decision.**

Run: `git add results/phase-2/p24-* results/phase-2/REPORT.md docs/design/continuation-contract-v0.md && git commit -m "docs: record P2.4 independent holdout verdict"`

Expected: stage only existing task-owned paths; if the contract was not created, omit it from the add command.
