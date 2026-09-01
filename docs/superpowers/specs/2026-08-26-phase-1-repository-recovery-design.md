# Phase 1: Repository Crash/Restart Recovery Design

## Goal

Establish the first trustworthy Cairn proof: a terminal coding agent can resume
repository editing after a worker crash without losing verified work.

## Locked boundary

`TerminalWorld + reference coding-agent loop + clean checkpoint -> injected
process death -> fresh-process RGR -> hidden verifier`.

The reference harness, not an external framework, defines the semantics.

## Scope

- A repository-backed `TerminalWorld` that implements Cairn's existing World
  boundary: execute, snapshot, restore, digest, and observation.
- Four small pinned repository tasks, each with 3-5 sequential verified work
  units and a hidden final verifier.
- Failure injection only after a clean durable checkpoint, persisted as a
  `failure_fired` receipt before worker termination.
- A RecoveryBench v0.1 JSONL result schema with paired uninterrupted and
  recovered outcomes.
- Deterministic control and a two-model live pilot.

## Non-goals

- No framework integration, generic agent abstraction, queue, service,
  database, or agent orchestration.
- No compaction/Continuation Contract changes.
- No external effects, receipts, or exactly-once claims.
- No crash-in-place reconciliation: shell-command-to-checkpoint ambiguity is
  unsupported and reported as invalid in Phase 1.
- No OpenTelemetry work.

## Clean checkpoint

A checkpoint is valid only after a terminal action has completed, the
task-local progress oracle has verified the resulting repository state, a
workspace snapshot plus digest exists, and the checkpoint commit is durable.

## Experiment and evidence

Use four tasks, every non-terminal verified work boundary, an uninterrupted
baseline, and a fresh-process recovered arm. Deterministic cells run 10 times.
The live pilot must produce at least 40 valid fired paired recoveries across at
least two model configurations.

Each result records task/version, run/checkpoint IDs, injection ID and fired
status, model and harness provenance, before/after work-unit progress,
repository digests, verifier outputs, and the existing fidelity axes.

## Exit gate

1. Every valid deterministic cell passes the hidden verifier after recovery.
2. Deterministic no-regression and artifact equivalence are both 1.0.
3. Every recovery claim has a durable `failure_fired` receipt.
4. The live pilot reaches 40 valid fired paired recoveries across two models.
5. Recovered live success is no more than 10 percentage points below the paired
   uninterrupted baseline; no duplicate effects are present.
6. Tasks, verifier code, raw traces, raw results, and schema are published.
7. A custom terminal loop can adopt the adapter without adopting a framework.

## Direction-changing outcomes

The phase is invalid if faults do not fire, tasks finish in one opaque action,
or recovery succeeds by redoing pre-crash verified work. A live shortfall is
evidence about the continuation artifact; it does not justify loosening the
gate or adding integrations.
