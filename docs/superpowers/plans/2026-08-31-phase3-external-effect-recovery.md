# Phase 3 External Effect Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove that a fresh process can resolve one crash-ambiguous, externally observable create-once effect without blindly retrying, duplicating, or silently losing the intended effect.

**Architecture:** Keep Cairn's Phase 1/2 runtime and Continuation Contract frozen by hash. Add only a Phase-3 reference service and a benchmark-local crash-in-place harness. The harness records durable intent, provider evidence, receipt evidence, reconciliation decision, and final closure; its provider root is never restored with the workspace.

**Tech Stack:** Python 3.12, stdlib JSON/hashlib/subprocess, pytest, existing `EffectLedger` and `CheckpointStore`.

**Spec:** User-approved Phase 3 proof ladder in this conversation.

## Global Constraints

- Freeze the Phase 1/2 contract/evidence paths before implementation and recheck their SHA-256 values before admission.
- Do not edit `ContinuationState`, `recover()`, or Phase 1/2 benchmark/runtime paths.
- The first effect is a deterministic, file-backed provider-like create-once service outside the workspace and snapshot roots.
- Every restart is a new OS process with no parent object, transcript, provider client, or receipt object passed in memory.
- Every unresolved effect re-observes before any retry; `unknown`, mismatch, and `never-retry` escalate.
- The exact reference matrix is twelve semantic rows times three independent fresh-process repetitions.
- Seal the reference protocol before matrix execution and seal an independently authored holdout before any holdout run.
- Preserve all primary records. A post-seal failure stops that experiment; do not tune its fixture, schema, prompt, runner, model, or thresholds.

---

### Task 1: P3.0 freeze and evidence vocabulary

**Files:**
- Create: `benchmarks/p3_freeze.py`
- Create: `results/phase-3/p3-freeze.json`
- Test: `tests/test_p3_freeze.py`

**Interfaces:**
- `freeze_manifest(paths: list[Path], metadata: dict) -> dict`
- `frozen_paths_match(manifest: dict) -> bool`

- [ ] Write a failing test that hashes a file, mutates it, and requires `frozen_paths_match()` to return false.
- [ ] Run `python -m pytest tests/test_p3_freeze.py -q`; expect collection/import failure for `p3_freeze`.
- [ ] Implement only SHA-256 path/byte hashing and comparison; create a manifest covering the P2 contract, verdict, analysis, protocol, and Phase 1 control-freeze from the established worktree.
- [ ] Run the focused test and save `p3-freeze.json`; require every entry to match before P3.1.

### Task 2: P3.1 provider and durable trace primitives

**Files:**
- Create: `benchmarks/p3_effect_service.py`
- Create: `benchmarks/p3_trace.py`
- Test: `tests/test_p3_effect_service.py`

**Interfaces:**
- `CreateOnceProvider(root: Path)` with `dispatch(intent)`, `commit(intent)`, and `observe(intent) -> Observation`.
- `Intent`, `Observation`, `Receipt`, `Resolution` immutable JSON records bound by `effect_id`, idempotency key, and request fingerprint.

- [ ] Write failing tests for one commit per matching create-once key, an `absent` observation, a matching `present` observation, and a mismatching observation.
- [ ] Run the focused test; expect import failure for `p3_effect_service`.
- [ ] Implement a file-backed provider whose service root is distinct from workspace/snapshot roots, plus append-only trace records. Do not add a generic provider interface.
- [ ] Run focused tests; require provider event logs to expose calls, commits, resource IDs, and request fingerprints.

### Task 3: P3.2/P3.3 crash-in-place reference reconciler

**Files:**
- Create: `benchmarks/p3_harness.py`
- Test: `tests/test_p3_harness.py`

**Interfaces:**
- `run_reference_cell(cell: dict, protocol: dict, output_dir: Path) -> dict`
- `--recover-worker --input PATH --output PATH` starts a fresh recovery process.
- Recovery order is `intent -> external boundary -> crash -> observe -> reconcile -> retry|skip|escalate`.

- [ ] Write failing tests proving a committed response-loss path skips before a second provider call, an absent path re-observes then retries, and an unknown path escalates without retry.
- [ ] Run focused tests; expect import failure for `p3_harness`.
- [ ] Implement only the local parent/worker boundary. The parent creates the pre-effect checkpoint and injects process death; the worker opens the durable ledger/trace/provider roots, records its PID, re-observes first, then records a resolution and terminal closure.
- [ ] Run focused tests; require fresh PID, zero restore-before-observe calls, and no inherited-memory evidence.

### Task 4: P3.4 sealed 12x3 reference matrix

**Files:**
- Create: `benchmarks/p3_matrix.py`
- Create: `benchmarks/p3_analysis.py`
- Create: `results/phase-3/p3-reference-protocol.json`
- Test: `tests/test_p3_matrix.py`
- Test: `tests/test_p3_analysis.py`

**Interfaces:**
- `reference_cells(protocol: dict) -> list[dict]` emits exactly 36 cells.
- `analyze_records(records: list[dict]) -> dict` reports acquisition, decision correctness, duplicate prevention, recovery completion, and structural failures separately.

- [ ] Write failing tests for exact 36-cell enumeration and for a duplicate-free skip that nevertheless fails when the intended resource is absent.
- [ ] Run focused tests; expect import failure for P3 matrix/analysis modules.
- [ ] Implement the fixed twelve semantic rows: absent/retry, dispatch-no-commit/retry, committed-response-loss/skip, receipt-before-close/skip, unknown/escalate, mismatch/escalate, idempotent convergence controls, never-retry escalation controls, and uninterrupted controls. Seal hashes before any matrix cell.
- [ ] Execute all 36 primary cells and analyze them. Require 100% correct oracle decisions, zero duplicate commits, zero silent losses, and zero structural failures.

### Task 5: P3.5 independently authored sealed holdout

**Files:**
- Create: `benchmarks/p3_holdout_author.py`
- Create: `results/phase-3/p3-holdout-author-output.json`
- Create: `results/phase-3/p3-holdout-protocol.json`
- Create: `results/phase-3/p3-holdout-admission.json`
- Test: `tests/test_p3_holdout.py`

**Interfaces:**
- `audit_holdout(payload: dict) -> dict` rejects unpublished provider semantics and hidden verifier expectations.

- [ ] Write a failing audit test for a hidden response state or an unspecified expected reconciliation decision.
- [ ] Run focused test; expect import failure for `p3_holdout_author`.
- [ ] Independently author a distinct queryable create-once operation, derive all verifier cases from its published specification, seal the author output/protocol, and admit only after hashes, reference verdict, and clean matrix directory pass.
- [ ] Run the sealed holdout matrix using the same fresh-process semantics. Any failure becomes a terminal causal finding.

### Task 6: P3.6 admission and contract decision

**Files:**
- Create: `results/phase-3/p3-analysis.json`
- Create: `results/phase-3/p3-holdout-analysis.json`
- Create: `results/phase-3/p3-verdict.json`
- Create conditionally: `docs/design/receipt-reconciliation-contract-v0.md`
- Modify: `results/phase-3/REPORT.md`

- [ ] Write a failing admission test that rejects a missing raw record, an unsealed input change, a retry before observation, a duplicate commit, a silent loss, or a wrong decision.
- [ ] Run the focused test; expect failure because the admission checker does not exist.
- [ ] Implement the smallest admission checker over existing raw evidence; it must not compute a benchmark score or alter behavior.
- [ ] Recheck Phase 1/2 freeze hashes, run the full suite, scoped Ruff, and `git diff --check`. Publish the contract only if reference and holdout both pass every gate; otherwise publish only evidence and causal verdict.
