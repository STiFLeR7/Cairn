# Phase 2 v0.12 Powered Continuity Design

## State transition

Move from the terminal v0.11 finding—live-prefix acquisition made its 100-checkpoint gate
mathematically unreachable—to a separately pre-registered checkpoint-ready continuity
replication. v0.11 remains immutable evidence and is not extended, reclassified, or merged into
v0.12.

The v0.12 claim is conditional: given one clean, verified repository checkpoint, does a fresh
uninterrupted continuation (U), fresh-process recovery (R), and fresh-process compacted
continuation (C) retain equivalent task intent and reach the hidden verifier? It does not claim
that an arbitrary model can reliably acquire the checkpoint.

## Hypothesis and failure model

Hypothesis: the existing ContinuationState, RGR, serialization, and continuation prompt preserve
enough operational state for at least 100 live U/R/C triplets to complete from identical clean
checkpoints while preserving Phase 1 recovery parity.

Failures are classified before interpretation:

- U failure: model/task continuation failure; the cell is continuity-ineligible.
- R or C failure with U success: eligible continuity divergence requiring action-parity replay.
- Provider or CLI failure: transport failure, retained as raw evidence and never counted as a
  Cairn continuity failure.
- C action-parity replay failure using a successful U or R action sequence: causal evidence of a
  compaction/state path defect and the only trigger for a state or RGR correction.

## Frozen architecture boundary

Reuse the current TerminalWorld reference harness, deterministic fixture control commands, clean
checkpoint creation, ContinuationState, RGR, compaction path, prompt composition, Claude Code
transport, and hidden verifier. No runtime or schema change is part of v0.12.

The two external configurations are `claude_code:opus` and `claude_code:sonnet`. Each runs every
non-terminal split of `bugfix`, `config`, `tests`, and `followup` for 11 repetitions. The existing
cell enumerator produces 242 fixed cells: 121 per model.

Pinned inputs:

| Input | SHA-256 |
| --- | --- |
| `results/phase-2/control-freeze-recheck.json` | `7f969a9c861ad8e85a8103e3b421c78d3a1f2ddb8a37b3d2316e0e8c80bbcc56` |
| `src/cairn/eval/recoverybench.py` | `86819b8938cd803ad2ddb1acc260fd85d1dc25d74d59f275bc5c3207687772c6` |
| `src/cairn/eval/phase2.py` | `91a66602810f1a2caecfab4e60964bf7c9c0c7b62813643f44fe8f10746f0a32` |
| `benchmarks/phase2_matrix.py` | `b5e5f27c217be08bf4c79d7435bbef70f6e36fd893ea6f4f6d4b5db37171fc6f` |
| `benchmarks/phase2_acquisition_continuity.py` | `89379ea13c8910d3d367d28cc93f04ca4d0fdff6fddace4206a0d44cc45fbe06` |

## Power basis

The prior checkpoint-ready v0.6 control produced 99 complete triplets in 176 attempts. Its
one-sided 95% Wilson lower bound is 0.500507. At that lower-bound rate, 242 pre-registered attempts
have probability 0.997334 of producing at least 100 complete triplets under the repeated-cell
model. This calculation chooses sample size only; it does not change scoring, prompts, fixtures,
or thresholds.

## Execution and evidence flow

1. Write a hash-pinned v0.12 protocol before any model call.
2. Validate its 242-cell enumeration and every pinned input offline.
3. Run Opus and Sonnet independently with resume-safe, append-only cell evidence.
4. Select one terminal record per registered cell using the existing deterministic selector.
5. Report acquisition eligibility separately from conditional R/C continuity.
6. Replay every eligible divergence with the recorded successful U or R actions through C.
7. Recheck the frozen Phase 1 controls and full test suite.
8. Consume the already pinned `phase2_holdout` only if every live entry gate passes.

Interrupted primary records are preserved; at most one explicit `.retry.json` may complete a cell.
Missing, malformed, or incomplete cells fail the matrix-completeness gate.

## Live exit gate

All conditions are mandatory:

- 242 registered cells have a terminal selected record with no missing or incomplete cells.
- At least 100 U-eligible checkpoints exist.
- At least 100 conditional R successes exist.
- At least 100 conditional C successes exist.
- At least 100 complete U/R/C triplets exist.
- Every eligible R/C divergence has a preserved counterfactual replay result.
- No replay establishes a causal ContinuationState, compaction, or RGR defect.
- The Phase 1 control-freeze recheck is byte-identical and the repository test suite passes.

Failure of any condition leaves the holdout sealed and Continuation Contract v0 unpublished.

## Holdout boundary

The existing `phase2_holdout` source hashes remain pinned and its task content is not used for
calibration. Its execution protocol and acceptance threshold must be frozen before first use. The
holdout may run only after the live exit gate passes. A holdout failure invalidates publication;
it cannot trigger prompt, fixture, schema, or threshold tuning followed by reuse of the same
holdout.

## Explicitly out of scope

- Extending or rescuing v0.11
- Live-prefix acquisition improvements
- Prompt optimization or fixture edits
- ContinuationState schema expansion or RGR behavior changes without causal replay evidence
- Framework integrations, external-effect semantics, crash-in-place reconciliation, or
  OpenTelemetry
- Lowering, averaging, or retrospectively redefining any gate

## Deliverables

- `matrix-protocol-v12-powered-control-prefix.json`
- Raw 242-cell matrix with transcripts and preserved failures
- Deterministic acquisition/continuity analysis
- Causal replay evidence for every eligible divergence
- Phase 1 parity recheck and test evidence
- A separately frozen holdout protocol and result, only after live admission
- Continuation Contract v0, only if both live and holdout gates pass
