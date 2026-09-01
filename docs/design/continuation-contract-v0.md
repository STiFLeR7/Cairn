# Cairn Continuation Contract v0

Status: externally validated reference contract.

## Scope

This contract applies to repository coding-agent continuation from a clean, verified checkpoint. It does not guarantee that a model can acquire that checkpoint, and it does not cover external-effect safety.

## Required preserved semantics

A recovered or compacted continuation MUST preserve equivalent task intent, active subgoal, accepted decisions, verified work, verification state, repository/world identity, stop conditions, and the next independently verifiable action boundary. Implementations MAY use any internal schema.

## Fresh-process requirements

Recovery and compaction MUST operate in a fresh process without the original in-memory transcript. The implementation MUST re-ground repository state before acting, MUST NOT treat unverified mutation as progress, and MUST retain enough provenance to identify the checkpoint and world digest.

## Conformance

An implementation conforms only when U, R, and C start from the same verified checkpoint; a harness-owned public verifier evaluates all branches; acquisition failures are reported separately; raw failures are preserved; and every eligible divergence receives identical-action counterfactual replay that verifies and reproduces its source digest.

## Evidence and limitations

The reference evidence is the passing v0.12.1 live gate in `results/phase-2/REPORT.md` and the independently authored, sealed P2.4 holdout in `results/phase-2/p24-analysis.json` and `results/phase-2/p24-verdict.json`. P2.4 executed 60 registered cells across Claude Code Opus and Sonnet. Forty cells acquired an eligible checkpoint and completed U/R/C with zero structural failures or divergences; the other twenty were preserved as pre-continuation Sonnet action-granularity failures.

This is not a framework API, a memory-library schema, a claim of universal model reliability, or an external-effect contract.
