# P2.4 Independent Holdout Reconstitution Design

## Status

Approved in-chat on 2026-08-31. This document is the implementation contract for P2.4.

## Objective

Determine whether Cairn's existing ContinuationState, recovery re-grounding, and compacted
continuation semantics generalize to a newly authored repository task. The exposed v12 holdout is
invalid and unreusable. P2.4 must not tune Cairn, prompts, thresholds, or the new task after sealing.

## Non-goals

- No change to Cairn state, checkpoint, RGR, compaction, prompt, TerminalWorld, or sandbox behavior.
- No change to Phase 1 controls or existing Phase 2 runners, analyzers, replayers, protocols, or evidence.
- No framework integration, effect-receipt work, observability work, or generic fixture-plugin API.
- No reuse of the v12 holdout's domain, function names, task text, verifier cases, or expected values.
- No contract publication based on the passing live tranche alone.

## State machine

```text
P2.4.0 FREEZE
  -> P2.4.1 CLEAN_ROOM_AUTHORED
  -> P2.4.2 AUDITED_UNSEALED
  -> P2.4.3 DETERMINISTICALLY_VALIDATED
  -> P2.4.4 SEALED_UNCONSUMED
  -> P2.4.5 LIVE_COMPLETE
  -> P2.4.6 CAUSALLY_CLASSIFIED
  -> CONTRACT_V0 | TERMINAL_STOP
```

No state may be skipped. Once `SEALED_UNCONSUMED` is reached, any fixture, verifier, protocol,
prompt, model, threshold, or runner change invalidates the run and requires a completely new
holdout identity.

## P2.4.0: frozen boundary

Before authoring the task, write `results/phase-2/p24-freeze.json` with byte length and SHA-256 for:

- `src/cairn/state.py`
- `src/cairn/recovery.py`
- `src/cairn/harness/distill.py`
- `src/cairn/eval/phase2.py`
- `src/cairn/eval/recoverybench.py`
- `src/cairn/runtime/checkpoint_store.py`
- `src/cairn/runtime/sandbox_docker.py`
- `src/cairn/worlds/terminal.py`
- `benchmarks/phase2_matrix.py`
- `benchmarks/phase2_acquisition_continuity.py`
- `benchmarks/phase2_replay_control.py`
- `results/phase-2/control-freeze-recheck-v12.json`
- `results/phase-2/matrix-protocol-v12-powered-control-prefix.json`
- `results/phase-2/v12-acquisition-continuity.json`
- all four v12 causal replay summaries

The freeze also records the branch, HEAD, Python version, Docker server version, and that the
Phase 1 freeze is still byte-identical to SHA-256
`7f969a9c861ad8e85a8103e3b421c78d3a1f2ddb8a37b3d2316e0e8c80bbcc56`.
P2.4 code may import the frozen implementation but must not edit any frozen path.

## P2.4.1: clean-room authoring

Use a fresh non-interactive Claude Code Haiku process in an empty temporary directory with tools
disabled and no repository path in its context. Preserve the exact neutral author prompt and raw
JSON response as:

- `results/phase-2/p24-author-prompt.txt`
- `results/phase-2/p24-author-output.json`

The prompt requests one four-unit Python repository task in a queue/scheduling domain. It requires:

1. four independent named functions completed in a declared order;
2. a starter `project.py` containing only parseable stubs;
3. explicit valid input domains;
4. literal acceptance examples including boundaries and empty inputs;
5. all behavior that any verifier may score stated in the public README;
6. no external dependencies, files beyond README/project.py, randomness, time, network, or effects;
7. no function calling another task function;
8. machine-readable acceptance cases whose expected values are literal, not derived by implementation code.

The author receives no Cairn source, fixture names, prior task text, prior expected values, or model
results. Haiku is not an evaluated model configuration.

## P2.4.2: pre-seal audit

Audit the author output before any fixture or model execution. The audit is allowed to reject an
ambiguous task, but not to change it in response to model performance because no evaluated model
has run. Admission requires all of:

- exactly four independently testable functions and a total order;
- every scored case appears verbatim in the public acceptance criteria;
- input domains say which out-of-domain behavior is unscored;
- boundary and empty cases have one literal interpretation;
- no semantic dependency between work units;
- no overlap with the exposed v12 function names or task domain;
- no hidden formatting, separator, casing, coercion, or error behavior;
- a human reading only README and starter code can derive every verifier result.

Preserve the audit verdict and reasons in `results/phase-2/p24-author-audit.json`. Rejection ends this
holdout identity before execution; a replacement requires a new author output and audit trail.

## Isolated benchmark extension

P2.4 adds benchmark-only files and does not modify the frozen harness:

- `benchmarks/recoverybench_fixtures/<p24-name>/README.md`: public task and acceptance criteria.
- `benchmarks/recoverybench_fixtures/<p24-name>/project.py`: authored starter stubs.
- `benchmarks/p24_fixture.py`: task-local progress verifier, ordered control states, and temporary
  runtime registration into the existing fixture maps.
- `benchmarks/p24_matrix.py`: P2.4 orchestrator and fresh branch-worker entry point.
- `benchmarks/p24_analysis.py`: registered-cell selection, structural continuity evidence,
  divergence partitioning, and gate verdicts.
- `benchmarks/p24_replay.py`: target-aware identical-action replay with source-digest comparison.
- focused tests for fixture behavior, process isolation, protocol sealing, analysis, and replay.

No generic plugin interface is introduced. Runtime registration exists only for this experiment and
is performed before calling the frozen fixture loader.

## Deterministic validation before sealing

Tests are written first and must demonstrate these behaviors:

- the starter repository has progress zero;
- each control state advances exactly the next ordered unit;
- implementing a later unit before the next required unit does not advance progress;
- every published acceptance case is enforced literally;
- all four control states reach the final verifier;
- fake-model U, fresh-process R, and fresh-process C reach the same semantic artifact;
- R and C worker PIDs differ from the U/orchestrator PID;
- R uses durable recovery with no in-memory prefix history;
- C serializes/reloads compacted state, has no original transcript, and preserves durable world facts;
- identical-action replay reproduces both verifier success and the source artifact digest;
- a mutated expectation or missing durable checkpoint makes the relevant test fail.

The full repository suite and scoped Ruff must pass before sealing.

## P2.4.4: seal

Create `results/phase-2/p24-holdout-protocol.json` only after deterministic validation. It pins:

- the freeze manifest hash;
- author prompt, author output, and audit hashes;
- README, starter source, fixture registration, runner, analyzer, replayer, and focused-test hashes;
- Claude Code Opus and Sonnet configurations;
- all three nonterminal split points;
- ten repetitions per model/split, for exactly 60 registered cells;
- control prefix, legacy prompt composition, and empty verification capture;
- the unchanged 30-second terminal-action bound;
- output paths, retry-selection rules, and raw-evidence preservation rules;
- the hard gates below.

The protocol status is `sealed-unconsumed`, and `consume` remains false as the historical pre-run
state. A separate admission artifact records authorization for the first evaluated model call.

## U/R/C execution boundary

Every cell creates one deterministic control prefix and one durable checkpoint. All branches start
from byte-identical repository state and the same checkpoint digest.

- **U — uninterrupted reference:** continues in the orchestrator with the retained prefix history.
- **R — fresh-process RGR:** a new Python worker receives only the materialized workspace,
  checkpoint store, ledger, fixture identity, split, and model configuration. It calls frozen RGR
  and records that no in-memory prefix history was available.
- **C — transcript-unavailable compacted continuation:** another new Python worker receives the
  same durable inputs, serializes/reloads the compacted state through the frozen compaction helper,
  and never receives the original prefix history or transcript.

The P2.4 runner writes the record after each settled branch. An interrupted primary record is kept;
only the exact registered cell may resume to the existing `.retry.json` selection convention.

## Evidence model

For each selected cell, preserve:

- model, repetition, split, run ID, branch worker PID, and parent PID;
- shared prefix progress, checkpoint ID, checkpoint/world digest, and source hashes;
- branch start progress/digest and final progress/digest;
- raw continuation transcripts and checkpoint files;
- hidden-verifier result and classified failure reason;
- R `used_in_memory_history=false` and fresh PID evidence;
- C `original_transcript_available=false`, serialized/reloaded state evidence, and fresh PID evidence;
- accepted work-unit trajectory, proving preserved work and the next ordered action;
- final verifier result and harness-owned termination after the fourth verified unit.

Artifact equivalence has three separately reported meanings:

1. **Semantic equivalence (hard gate):** U, R, and C satisfy every public acceptance criterion.
2. **Independent exact-digest equality (descriptive):** report whether independently sampled branch
   implementations are byte-identical; do not confuse stylistic model variance with state loss.
3. **Action-parity digest equality (hard gate):** replaying a successful source action sequence
   through another treatment must reproduce the source final digest exactly.

## Hard gates

The new holdout passes only if all conditions are true:

```text
attempts == 60
missing_cells == []
incomplete == 0
terminal_invalid == 0
eligible U checkpoints >= 10
conditional R successes >= 10
conditional C successes >= 10
complete U/R/C triplets >= 10
all selected branches start from the registered checkpoint digest
all successful branches preserve prefix work and take only the next ordered unit
all R branches are fresh-process and use no in-memory prefix history
all C branches are fresh-process, serialized/reloaded, and transcript-unavailable
every eligible divergence receives the registered target-aware replay
every replay passes the verifier and exactly matches its source artifact digest
zero causal Cairn/state/RGR/compaction defects
the P2.4 freeze recheck is byte-identical
the full repository test suite passes
```

Thresholds cannot be lowered and records cannot be combined with v12 or calibration evidence.

## Failure policy

Classify failures in this order:

1. acquisition/model capability;
2. provider or process failure;
3. task/verifier ambiguity or contradiction;
4. harness/orchestrator defect;
5. continuation-state/RGR/compaction defect established by counterfactual replay.

A failure stops the experiment after causal classification. Fixing a pre-seal deterministic defect
is allowed and must be covered by a failing test. Any post-seal fixture, verifier, prompt, model,
threshold, or runner correction invalidates the holdout and forbids reuse.

## Publication rule

Create `docs/design/continuation-contract-v0.md` only after every live and P2.4 holdout hard gate
passes. The contract is behavioral: implementations may use any internal schema but must preserve
task intent, accepted decisions, verified work, verification state, world identity, stop conditions,
and the next independently verifiable action across fresh recovery and transcript-unavailable
compaction. It explicitly excludes external-effect safety and model checkpoint-acquisition claims.

If any gate fails, publish only the raw evidence, causal verdict, limitations, and reproduction
commands. Do not create or weaken the contract.
