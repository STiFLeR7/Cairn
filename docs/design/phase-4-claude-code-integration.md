# Phase 4 — Claude Code Integration Proof

**Status:** not admitted. The corrected sealed reconstitution in
[`results/phase-4/reconstitution-v2/`](../../results/phase-4/reconstitution-v2/) froze self-contained
reference and independently authored holdout workloads before any host process ran, but failed the
locked U/R/C artifact-equivalence gate.

## Claim and boundary

Claude Code retained control of its model, session, planner, native `Read`/`Write`/`Bash` tools, and
workspace execution. Cairn contributed no runtime, framework adapter, scheduler, memory store, or
provider abstraction. The thin boundary is durable workspace evidence:

- `.cairn-continuation.json` holds the existing Continuation Contract v0 semantic projection;
- `.cairn-effect-intent.json`, provider observation, receipt, resolution, and ledger hold the existing
  Receipt/Reconciliation Contract v0 evidence.

The reference host was Claude Code 2.1.250 with requested `--model sonnet`, `--safe-mode`,
`--setting-sources project`, and `--no-session-persistence`. The command requests project-only settings;
the proof relies only on recorded native operations and fresh process identity, not on a claim that this
host has an allowlisted tool surface or uses Sonnet exclusively for every internal helper call.

## Evidence and blocking finding

The reproducible [v2 verdict](../../results/phase-4/reconstitution-v2/verdict.json) derives from native
Claude Code stream records and self-contained `evidence-snapshot/` copies of artifacts and provider state.
It fails if the [pre-run control freeze](../../results/phase-4/reconstitution-v2/pre-run-freeze.json)
does not match the harness, contracts, tests, exact public workloads, or sealed holdout. The reference controls prove:

1. An uninterrupted terminal coding task produces a verified artifact and a continuation projection.
2. After the harness kills the Claude Code process after that projection, a distinct fresh process receives
   only the projection, re-observes, reruns the verifier, and terminates without changing verified work.
3. A separate transcript-unavailable compacted continuation repeats the same re-observation and verifier
   behavior.
4. After a native terminal command commits the deterministic create-once provider but before a receipt is
   durable, a distinct fresh process makes `python effect_tool.py observe` its first operation, finds the
   matching resource, chooses `skip`, writes a re-observed receipt, and closes the ledger. Provider evidence
   records one resource and one commit.
5. The independently authored and sealed holdout combines a different coding task with a distinct effect
   key and repeats the crash, continuation, re-observation, skip, receipt, verifier, and ledger checks.

For the coding control, the verdict requires the uninterrupted, crash/recovered, and compacted artifacts
to have identical SHA-256 values. This gate **failed**: uninterrupted and compacted runs produced the
same double-quoted f-string, while the crash/recovered run preserved a semantically equivalent
single-quoted f-string. The recovery process did not modify the crash artifact, so the evidence does not
establish a Continuation Contract defect; it establishes that this host/task combination does not meet the
locked byte-equivalence baseline gate. Cairn does not relax that gate after sealing.

The recovery input is recorded exactly, has no
original session/transcript payload, and each host command uses `--no-session-persistence` without
`--resume`. Raw records and snapshots live only in the reconstitution directory above; their post-run
hash inventory is [`evidence-manifest.json`](../../results/phase-4/reconstitution-v2/evidence-manifest.json).

## Non-claims and next gate

This is not an exactly-once result, a general Claude Code integration, an adapter API, a generic effects
layer, a framework integration, or an interoperability standard. The provider remains the Phase 3
deterministic create-once reference effect. An independent host implementation must pass the same admitted
contracts before Cairn can claim multi-host interoperability; multiple independent hosts and providers are
required before proposing a standard.

Earlier OpenCode acquisition experiments and the v1 Claude Code protocol
are retained in `results/phase-4/` as non-admission diagnostics. They are deliberately excluded from the
verdict.
