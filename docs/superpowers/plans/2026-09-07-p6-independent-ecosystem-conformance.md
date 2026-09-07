# P6 Independent Ecosystem Conformance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a standalone Cairn Conformance Kit v0 and admit it only if an independently authored third implementation passes frozen reference and sealed-holdout recovery semantics without importing Cairn runtime code.

**Architecture:** Extract only admitted behavioral obligations into a four-file, standard-library conformance kit. A target-owned implementation emits linked semantic observations while retaining its own state and runtime formats; Cairn's evaluator checks hashes, ordering, decisions, negative behavior, and equivalence without driving the host. Pydantic AI v2 plus DBOS is capability-gated before any eligible submission is accepted.

**Tech Stack:** Python 3.10+ standard library for Cairn's kit; pytest for repository tests; Pydantic AI v2 and DBOS only in a disposable capability/submission environment; JSON evidence and SHA-256 seals.

**Spec:** `docs/superpowers/specs/2026-09-07-p6-independent-ecosystem-conformance-design.md`

## Global Constraints

- Do not edit P1-P5 contracts, benchmark drivers, fixtures, results, seals, or verdicts.
- Do not edit Cairn runtime, Agent, World, checkpoint, recovery, or effect-ledger behavior.
- `conformance/v0/evaluate.py` must import only the Python standard library and work after its directory is copied outside this repository.
- The evidence envelope describes observations only; it must not define a host checkpoint, continuation, memory, receipt, transcript, workflow, or session format.
- No target SDK dependency may be added to Cairn's core or development dependencies.
- No polling, transcript scraping, or prompt simulation may stand in for a missing host capability.
- No post-seal prompt, workload, verifier, schema, threshold, driver, or contract-mapping change is admissible.
- A Cairn-authored rehearsal can prove kit executability but cannot satisfy independent authorship.
- Stop at the first failed state gate and preserve the negative evidence.

---

## File map

| Path | Responsibility |
|---|---|
| `benchmarks/p6_freeze.py` | Generate and recheck the P6 frozen-input manifest using relative paths. |
| `conformance/v0/README.md` | Normative contract profile, requirement table, submission protocol, matrix, and claim limits. |
| `conformance/v0/evidence.schema.json` | Document the evidence-envelope shape, not host state. |
| `conformance/v0/vectors.json` | Existing receipt/reconciliation decision table and required continuation semantics. |
| `conformance/v0/evaluate.py` | Standalone standard-library seal, structure, ordering, decision, and equivalence evaluator. |
| `tests/test_p6_freeze.py` | Freeze manifest generation and mutation detection. |
| `tests/test_p6_conformance_kit.py` | Positive submission, mutation rejection, copied-kit isolation, and CLI tests. |
| `benchmarks/p6_pydantic_dbos_probe.py` | Host-only capability probe; imports no Cairn module. |
| `tests/test_p6_pydantic_dbos_probe.py` | Offline tests for probe evidence assembly; skips released-host execution when optional packages are absent. |
| `results/phase-6/freeze.json` | P6.0 authoritative frozen baseline. |
| `results/phase-6/capability-acquisition/` | Exact environment, commands, stdout/stderr, raw host records, hashes, and verdict. |
| `results/phase-6/submissions/pydantic-dbos-independent-v1/` | Externally authored source provenance plus reference/holdout raw evidence, seals, and verdicts. |
| `docs/design/phase-6-independent-conformance.md` | Final methodology, target result, causal limitations, and allowed claim. |

## Task 1: Freeze admitted obligations

**Files:**
- Create: `benchmarks/p6_freeze.py`
- Create: `tests/test_p6_freeze.py`
- Create: `results/phase-6/freeze.json`

**Interfaces:**
- Produces: `freeze_manifest(root: Path, paths: Sequence[Path], metadata: Mapping[str, object]) -> dict`
- Produces: `frozen_paths_match(root: Path, manifest: Mapping[str, object]) -> bool`
- Consumed by: kit seal and final admission audit.

- [ ] **Step 1: Write failing relative-path and mutation tests**

```python
def test_p6_freeze_is_portable_and_detects_mutation(tmp_path: Path):
    contract = tmp_path / "contract.md"
    contract.write_text("v0\n", encoding="utf-8")
    manifest = freeze_manifest(tmp_path, [contract], {"head": "abc"})
    assert manifest["files"][0]["path"] == "contract.md"
    assert frozen_paths_match(tmp_path, manifest)
    contract.write_text("changed\n", encoding="utf-8")
    assert not frozen_paths_match(tmp_path, manifest)
```

- [ ] **Step 2: Run the test and confirm the missing-module failure**

Run: `python -m pytest tests/test_p6_freeze.py -q`

Expected: collection fails because `benchmarks.p6_freeze` does not exist.

- [ ] **Step 3: Implement the smallest freeze helper**

```python
def freeze_manifest(root, paths, metadata):
    return {
        "schema_version": "cairn.p6-freeze.v0",
        "metadata": dict(metadata),
        "files": [_fingerprint(root, path) for path in paths],
    }

def frozen_paths_match(root, manifest):
    try:
        return all(_fingerprint(root, root / item["path"]) == item for item in manifest["files"])
    except (KeyError, OSError, ValueError):
        return False
```

`_fingerprint` resolves both root and target, rejects a target outside root, and returns POSIX relative
path, byte count, and SHA-256.

- [ ] **Step 4: Generate the authoritative freeze**

Hash exactly:

```text
docs/design/continuation-contract-v0.md
docs/design/receipt-reconciliation-contract-v0.md
results/phase-1/REPORT.md
results/phase-2/p24-verdict.json
results/phase-3/p3-verdict.json
results/phase-4/reconstitution-v6/verdict.json
results/phase-5/two-host-portability-verdict.json
benchmarks/p5_conformance.py
docs/superpowers/specs/2026-09-07-p6-independent-ecosystem-conformance-design.md
```

Metadata records HEAD `4db80e0b9f0b6ba01ec92a50060c4b8d6a6e97fb`, branch, Python version,
platform, and `state=FROZEN_OBLIGATIONS`.

Run: `python benchmarks/p6_freeze.py --output results/phase-6/freeze.json`

Expected: exit 0 and a relative-path JSON manifest.

- [ ] **Step 5: Validate and commit P6.0**

Run: `python -m pytest tests/test_p6_freeze.py -q`

Expected: PASS.

Commit: `research: freeze Phase 6 conformance inputs`

## Task 2: Build the standalone evaluator test-first

**Files:**
- Create: `conformance/v0/evidence.schema.json`
- Create: `conformance/v0/vectors.json`
- Create: `conformance/v0/evaluate.py`
- Create: `tests/test_p6_conformance_kit.py`

**Interfaces:**
- Produces: `evaluate_submission(submission: dict, submission_root: Path, kit_root: Path | None = None) -> dict`
- Produces CLI: `python evaluate.py submission/evidence.json --output submission/verdict.json`
- Verdict shape: `{"schema_version": "cairn.conformance-verdict.v0", "passed": bool, "failures": list[str], "counts": dict}`.

- [ ] **Step 1: Write the minimal passing-submission builder in the test**

The builder creates one U/R/C triplet and all seven negative/effect cells for repetitions 1-3. Each
run has:

```python
{
    "cell": "R",
    "repetition": 1,
    "checkpoint_id": "checkpoint-1",
    "checkpoint_artifact_sha256": digest,
    "checkpoint_verified_work_sha256": verified_digest,
    "process": {"before": "pid-101", "after": "pid-202", "transcript_available": False},
    "events": [
        {"seq": 1, "kind": "checkpoint_durable", "process_id": "pid-101", "evidence_ref": "raw/r.json"},
        {"seq": 2, "kind": "process_death", "process_id": "pid-101", "evidence_ref": "raw/r.json"},
        {"seq": 3, "kind": "process_started", "process_id": "pid-202", "evidence_ref": "raw/r.json"},
        {"seq": 4, "kind": "reobserve", "process_id": "pid-202", "evidence_ref": "raw/r.json"},
        {"seq": 5, "kind": "action", "process_id": "pid-202", "evidence_ref": "raw/r.json"},
        {"seq": 6, "kind": "verification", "process_id": "pid-202", "evidence_ref": "raw/r.json"},
        {"seq": 7, "kind": "termination", "process_id": "pid-202", "evidence_ref": "raw/r.json"},
    ],
    "final": {
        "verified": True,
        "artifact_sha256": digest,
        "outcome_sha256": outcome_digest,
        "verified_work_sha256": verified_digest,
        "unauthorized_action": False,
    },
}
```

- [ ] **Step 2: Write mutation tests before evaluator code**

Parameterize one mutation per invariant:

```python
@pytest.mark.parametrize("mutation, expected", [
    (drop_raw_evidence, "missing evidence file"),
    (renumber_events, "event sequence"),
    (reuse_process_identity, "fresh process"),
    (act_before_reobserve, "re-observation must precede action"),
    (lose_verified_work, "verified work"),
    (break_compaction_boundary, "active context"),
    (duplicate_effect, "provider commits"),
    (retry_unknown, "unknown observation must escalate"),
    (change_r_artifact, "U/R/C artifact equivalence"),
    (trust_p5_boolean_only, "unsupported evidence schema"),
])
def test_mutation_is_rejected(valid_submission, mutation, expected):
    mutation(valid_submission)
    verdict = evaluate_submission(valid_submission, valid_submission.root)
    assert not verdict["passed"]
    assert any(expected in failure for failure in verdict["failures"])
```

- [ ] **Step 3: Confirm tests fail because the evaluator is absent**

Run: `python -m pytest tests/test_p6_conformance_kit.py -q`

Expected: collection fails on missing `conformance/v0/evaluate.py`.

- [ ] **Step 4: Add the evidence schema and immutable semantic vectors**

`vectors.json` contains these exact existing decisions:

```json
[
  {"observation":"absent","tool_class":"safe-to-retry","matching":null,"decision":"retry"},
  {"observation":"absent","tool_class":"proven-idempotent","matching":null,"decision":"retry"},
  {"observation":"present","tool_class":"check-before-retry","matching":true,"decision":"skip"},
  {"observation":"unknown","tool_class":"check-before-retry","matching":null,"decision":"escalate"},
  {"observation":"present","tool_class":"check-before-retry","matching":false,"decision":"escalate"},
  {"observation":"absent","tool_class":"never-retry","matching":null,"decision":"escalate"}
]
```

The schema requires kit, implementation, workload, evidence file inventory, and run fields while
leaving host-native metadata open. It contains no host-state property.

- [ ] **Step 5: Implement evaluator primitives with stdlib only**

Implement path-safe hashing, structural validation, event ordering, required-event lookup, fresh
identity checks, raw-evidence link validation, U/R/C triplet comparison, negative-control checks,
and vector-backed effect decisions. Collect every failure instead of failing at the first one.

Critical ordering check:

```python
def _precedes(events, first, second):
    positions = {event["kind"]: event["seq"] for event in events}
    return first in positions and second in positions and positions[first] < positions[second]
```

For recovery cells, `reobserve` must precede the first `action`; for escalation cells, no recovered
`action` or `effect_dispatch` may exist.

- [ ] **Step 6: Run focused tests until all mutations are rejected**

Run: `python -m pytest tests/test_p6_conformance_kit.py -q`

Expected: PASS.

- [ ] **Step 7: Run style and commit the evaluator**

Run: `ruff check conformance/v0/evaluate.py tests/test_p6_conformance_kit.py`

Expected: PASS.

Commit: `feat: add standalone recovery conformance evaluator`

## Task 3: Publish the normative profile and prove copied-kit isolation

**Files:**
- Create: `conformance/v0/README.md`
- Modify: `tests/test_p6_conformance_kit.py`
- Create: `results/phase-6/kit-verdict.json`

**Interfaces:**
- Consumes the evaluator CLI and vectors from Task 2.
- Produces the only material an eligible external implementation may consume.

- [ ] **Step 1: Write the copied-directory test**

```python
def test_kit_runs_after_copy_outside_repository(tmp_path, valid_submission_path):
    kit = tmp_path / "kit"
    shutil.copytree(ROOT / "conformance" / "v0", kit)
    completed = subprocess.run(
        [sys.executable, str(kit / "evaluate.py"), str(valid_submission_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
```

- [ ] **Step 2: Confirm it fails before the profile exists**

Run: `python -m pytest tests/test_p6_conformance_kit.py::test_kit_runs_after_copy_outside_repository -q`

Expected: FAIL because the four-file kit is incomplete.

- [ ] **Step 3: Write the normative profile**

The README contains the requirement identifier, exact P1/P2/P3 source clause, invariant,
counterexample, applicable cells, evidence field, implementation boundary, sealing rules,
submission command, and allowed claim. It explicitly says the schema is not a state format.

- [ ] **Step 4: Produce and verify kit verdict**

Run the copied kit against the positive fixture and every mutation fixture. Record kit file hashes,
Python version, test command, pass counts, and `state=KIT_READY` in
`results/phase-6/kit-verdict.json`.

- [ ] **Step 5: Recheck the P6.0 freeze and commit P6.1**

Run:

```text
python -m pytest tests/test_p6_freeze.py tests/test_p6_conformance_kit.py -q
python benchmarks/p6_freeze.py --check results/phase-6/freeze.json
git diff --check
```

Expected: all commands pass.

Commit: `docs: publish Cairn Conformance Kit v0`

## Task 4: Acquire Pydantic AI/DBOS capabilities without Cairn semantics

**Files:**
- Create: `benchmarks/p6_pydantic_dbos_probe.py`
- Create: `tests/test_p6_pydantic_dbos_probe.py`
- Create: `results/phase-6/capability-acquisition/README.md`
- Generate: raw files beneath `results/phase-6/capability-acquisition/`

**Interfaces:**
- CLI: `python benchmarks/p6_pydantic_dbos_probe.py --output results/phase-6/capability-acquisition/run --mode versions|restart|compaction|effect-boundary|verdict`
- Probe modes: `versions`, `restart`, `compaction`, `effect-boundary`, `verdict`.
- Does not consume or emit Cairn continuation or receipt types.

- [ ] **Step 1: Query stable package versions in a disposable virtual environment**

Create the environment outside the repository. Install the newest stable compatible
`pydantic-ai-slim[dbos]` and record the exact resolved lock with `python -m pip freeze`. Do not edit
`pyproject.toml`.

- [ ] **Step 2: Write offline evidence-assembly tests**

Tests require the verdict builder to reject:

```python
missing = {
    "fresh_process": False,
    "durable_workspace": True,
    "durable_journal": True,
    "compaction_completed": True,
    "active_context_changed": True,
    "ordered_effect_events": True,
    "ambiguous_effect_window": True,
}
assert not capability_verdict(missing)["passed"]
```

The host execution test is marked `skipif` when Pydantic AI or DBOS is absent from Cairn's normal
test environment.

- [ ] **Step 3: Implement and run the restart probe**

Use SQLite DBOS storage and a deterministic Pydantic test model. Start a workflow that durably
records one completed unit, block in the next unit, terminate the process, then launch the same
registered application in a new process. Preserve PIDs, workflow ID, step journal, workspace
digest, commands, stdout, and stderr. Pass only if the fresh process resumes without repeating the
completed unit.

- [ ] **Step 4: Run the host-owned compaction probe**

Use Pydantic AI's public history-processing/compaction operation through DBOS durability. Capture
the host operation event plus the complete active model-message identities before and after. Pass
only if completion is directly observed and the active context changes while declared intent,
verified work, and next-step markers remain. A mere token-count reduction or constructed summary
does not pass.

- [ ] **Step 5: Run the ambiguous effect-boundary probe**

Run a deterministic local provider in a separate process. Terminate the workflow process after the
provider commits but before the local step result is journaled. Preserve provider requests,
commits, IDs, fingerprints, DBOS step records, and the first operation after recovery. This probe
passes only if the ambiguity window and event order are observable; it does not implement Cairn's
resolution decision.

- [ ] **Step 6: Classify the capability verdict**

If all seven capabilities pass, write `state=TARGET_CAPABLE` with exact versions and hashes. If one
fails, write a stopped verdict and preserve all negative evidence. Do not alter Cairn or simulate
the boundary. Only a stopped primary verdict authorizes a separately recorded LangGraph/Deep Agents
probe under the same seven requirements.

- [ ] **Step 7: Run tests and commit P6.2 evidence**

Run:

```text
python -m pytest tests/test_p6_pydantic_dbos_probe.py -q
python -m pytest tests/test_p6_freeze.py tests/test_p6_conformance_kit.py -q
git diff --check
```

Commit either `research: acquire Pydantic DBOS conformance capabilities` or
`research: stop Pydantic DBOS conformance target` according to evidence.

## Task 5: Accept an eligible independent implementation

**Files:**
- Create after receipt: `results/phase-6/submissions/pydantic-dbos-independent-v1/implementation.json`
- Create after receipt: `results/phase-6/submissions/pydantic-dbos-independent-v1/provenance-audit.json`
- Add tests only if the submission exposes an evaluator defect before sealing.

**Interfaces:**
- Consumes only the published `conformance/v0` directory.
- Produces an immutable implementation repository URL, commit, lock hash, author identity, and
  clause-to-host mapping.

- [ ] **Step 1: Publish the kit commit for external consumption**

Push the kit-ready branch or master commit without publishing a conformance claim.

- [ ] **Step 2: Obtain a non-Cairn-authored submission**

The implementer works in its own repository after the kit freeze and may ask specification
questions publicly. Cairn maintainers must not write or patch its host integration.

- [ ] **Step 3: Audit independence mechanically and manually**

Clone the pinned submission into an empty directory, scan its dependency lock and source for
`cairn`, Cairn repository paths, copied P4/P5 driver identifiers, and Cairn fixture content. Record
repository ownership, author commits, kit version, and clause mapping.

- [ ] **Step 4: Enforce the P6.3 exit gate**

If provenance or code independence is missing, record `KIT_READY` or
`TECHNICALLY_CONFORMANT_REHEARSAL` and stop. Do not proceed to sealed execution.

Commit: `research: register independent conformance submission`

## Task 6: Execute and admit the public reference matrix

**Files:**
- Preserve submission-owned raw evidence beneath `results/phase-6/submissions/pydantic-dbos-independent-v1/reference/`
- Create: `results/phase-6/submissions/pydantic-dbos-independent-v1/reference-verdict.json`

**Interfaces:**
- External implementation emits the P6 evidence envelope.
- Cairn's copied evaluator returns the only machine verdict.

- [ ] **Step 1: Pre-register and seal reference inputs**

Record task, verifier, implementation commit, dependency lock, host versions, deterministic model,
matrix, three repetitions, timeouts, crash boundaries, and output locations before the first run.

- [ ] **Step 2: Execute all 30 physical reference cells**

Run U, R, R_NEG, C, C_NEG, E_MATCH, E_ABSENT, E_ESC_UNKNOWN, E_ESC_MISMATCH, and E_ESC_NEVER three
times each. Preserve every attempt; do not replace failed attempts.

- [ ] **Step 3: Evaluate using a copied kit**

Run: `python phase6-kit/evaluate.py results/phase-6/submissions/pydantic-dbos-independent-v1/reference/evidence.json --output results/phase-6/submissions/pydantic-dbos-independent-v1/reference-verdict.json`

Expected: 30/30 cells pass with no failures.

- [ ] **Step 4: Audit host-native evidence samples**

For every cell family, compare at least one evidence-envelope event chain to the immutable raw host
record and record the exact source offsets/IDs. Any unsupported mapping fails the gate.

- [ ] **Step 5: Commit P6.4 evidence**

Commit: `research: pass independent reference conformance`

## Task 7: Author, seal, and execute the independent holdout

**Files:**
- Preserve authoring, public task, private verifier, seal, raw runs, and verdict beneath
  `results/phase-6/submissions/pydantic-dbos-independent-v1/holdout/`.

**Interfaces:**
- Holdout author/sealer is not the implementation author.
- Uses the unchanged kit, matrix, thresholds, and implementation commit from Task 6.

- [ ] **Step 1: Capture independent authorship before revealing the implementation**

Record author identity, neutral author brief, raw authored output, public acceptance audit, and
declaration of no implementation access.

- [ ] **Step 2: Seal the holdout**

Hash the public task, starter repository, private verifier, local effect service, implementation
commit, environment lock, matrix, evaluator, and thresholds. Set `consumed=false`.

- [ ] **Step 3: Execute the unchanged 30-cell matrix**

Preserve all commands, process identities, DBOS journal, workspace snapshots, provider records,
evidence envelopes, stdout, stderr, and final artifacts. Do not rerun failed cells under the same
identity.

- [ ] **Step 4: Evaluate and independently reproduce**

The holdout passes only if the copied evaluator reports 30/30 and an uninvolved reproducer obtains
the same verdict from the published implementation commit and sealed inputs.

- [ ] **Step 5: Commit P6.5 evidence**

Commit: `research: pass sealed independent conformance holdout`

## Task 8: Admission audit, documentation, and publication

**Files:**
- Create: `docs/design/phase-6-independent-conformance.md`
- Modify: `docs/design/README.md`
- Modify: `README.md`
- Modify: `ROADMAP.md`
- Modify: `CHANGELOG.md`
- Modify only if stale: `CHECKLIST.md`, `REPRODUCE.md`, `PAPER.md`, `docs/research/claims-registry.md`
- Create: `results/phase-6/admission-verdict.json`

**Interfaces:**
- Consumes every P6.0-P6.5 verdict and unchanged P1-P5 freeze evidence.
- Produces the final narrow claim or an explicit stopped-state report.

- [ ] **Step 1: Write the admission audit before prose claims**

The machine-readable verdict lists every design requirement, its authoritative artifact, status,
and failure reason. `admitted=true` only when every P6.0-P6.6 condition passes.

- [ ] **Step 2: Recheck frozen contracts and prior evidence**

Run the P6 freeze checker and confirm no P1-P5 path changed relative to branch base.

- [ ] **Step 3: Update documentation to the exact achieved state**

If admitted, claim one independently authored conforming implementation only. If external
authorship or any gate is absent, publish `KIT_READY` or `TECHNICALLY_CONFORMANT_REHEARSAL`, the
blocker, and the smallest next action. Do not use “standard,” “universal,” or “exactly once.”

- [ ] **Step 4: Run complete verification**

Run:

```text
python -m pytest -q
ruff check .
python conformance/v0/evaluate.py results/phase-6/submissions/pydantic-dbos-independent-v1/reference/evidence.json
python conformance/v0/evaluate.py results/phase-6/submissions/pydantic-dbos-independent-v1/holdout/evidence.json
python benchmarks/p6_freeze.py --check results/phase-6/freeze.json
git diff --check
```

Every applicable command must pass. If no eligible submission exists, the two evaluator commands
are inapplicable and the admission verdict must explicitly fail the external-submission gate.

- [ ] **Step 5: Review, commit, and publish only relevant files**

Inspect `git status`, `git diff --stat`, and the complete diff. Commit with either:

```text
research: admit independent ecosystem conformance
```

or the causally accurate stopped-state message. Push the Phase 6 commits to `master`, verify the
remote commit and CI, and leave the Phase 6 tracked worktree clean.

## Plan self-review

- Spec coverage: P6.0-P6.6, target fallback, matrix, sealing, external authorship, documentation,
  regression, push, and clean-tree requirements each map to a task.
- Intentional stop: no plan step manufactures an “independent” submission. Task 5 is a hard external
  gate, not an implementation placeholder.
- Type consistency: `evaluate_submission`, verdict shape, evidence cells, repetitions, and freeze
  interfaces are defined once and consumed under the same names.
- Scope control: four kit files, one freeze helper, one capability probe, and focused tests are the
  minimum new code; no Cairn core or generic adapter abstraction changes.
