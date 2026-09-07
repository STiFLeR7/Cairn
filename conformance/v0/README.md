# Cairn Recovery Conformance Kit v0

This kit evaluates observations from an implementation of Cairn's admitted
recovery semantics. It does not provide a runtime, adapter, state format,
memory system, workflow engine, receipt store, or host integration.

An implementation remains responsible for its own runtime, agent loop, model
and session handling, tools, persistence, scheduling, and raw evidence.

## Scope

The v0 profile checks the following contract obligations:

| Obligation | Required observation |
| --- | --- |
| Continuation | A durable checkpoint identifies task intent, active subgoal, accepted decisions, verified work, verification state, world identity, stop conditions, and next-action boundary. The host may represent these however it chooses. |
| Fresh recovery | A new process resumes with the original transcript unavailable, re-observes the world before any action, preserves verified work, and terminates safely. |
| Compaction continuity | Native compaction has a directly observed completion event and changed active context. The compacted continuation preserves the required semantics; its negative control terminates safely without an unauthorized action. |
| Effect reconciliation | Before dispatch, intent is durable. After an ambiguous crash, a fresh process observes the provider before resolving: absent safe-to-retry or proven-idempotent intent retries; matching present intent skips; unknown, mismatch, and never-retry cases escalate. A retry or skip closes a durable receipt and ledger only after one-provider-commit convergence. |

This profile does not claim exactly-once delivery. It checks safe reconciliation
of one create-once effect.

## Required matrix

Submit every cell three times, for 30 runs total. `U`, `R`, and `C` in each
repetition share a checkpoint and must have equivalent final artifact and
outcome digests.

| Cell | Meaning |
| --- | --- |
| `U` | Uninterrupted reference. |
| `R` | Fresh-process recovery after checkpoint and process death. |
| `R_NEG` | Fresh recovery that must safely terminate rather than perform an unauthorized action. |
| `C` | Native compaction followed by transcript-unavailable continuation. |
| `C_NEG` | Native compaction negative control that must safely terminate. |
| `E_MATCH` | Provider observes a matching committed effect; skip. |
| `E_ABSENT` | Provider observes an absent safe-to-retry or proven-idempotent effect; retry only after observation. |
| `E_ESC_UNKNOWN` | Provider state is unknown; escalate without retry. |
| `E_ESC_MISMATCH` | Provider observes a mismatching effect; escalate without retry. |
| `E_ESC_NEVER` | Intent is never-retry; escalate without retry. |

Every post-recovery operation must be linked to raw evidence. Recovery and
effect runs must expose distinct pre-crash and fresh-process identities. The
first post-restart operation is `reobserve` for continuation recovery and
`provider_observation` for effect recovery.

## Submission

Create an evidence document conforming to
[`evidence.schema.json`](evidence.schema.json). Include hashes and byte counts
for every raw evidence file it references. The evaluator validates those files
before trusting their event references.

Seal the public task, verifier, and holdout before execution. Do not alter a
prompt, workload, schema, threshold, or verifier after sealing. A full
independent-conformance claim additionally requires a non-Cairn implementer
and a holdout author/sealer distinct from that implementer. A Cairn-authored
run is a technical rehearsal, not independent conformance.

Run the copied kit from outside the Cairn repository:

```text
python evaluate.py submission/evidence.json --output submission/verdict.json
```

The kit consists only of this profile, `evidence.schema.json`, `vectors.json`,
and `evaluate.py`. Copy those four files unchanged. The submission's kit hash
must match that copy.

## Verdict and limits

`evaluate.py` is standard-library-only and evaluates linked semantic facts; it
does not import, start, drive, or inspect a host runtime. It rejects missing
raw evidence, stale process identity, recovery before re-observation, invalid
compaction observation, unsafe effect resolution, duplicate provider commits,
lost verified work, and U/R/C artifact or outcome divergence.

Passing means one independently implemented host satisfied this v0 profile for
the sealed workload matrix. It does not establish universal framework
compatibility, native Cairn support, a formal ecosystem standard, or
exactly-once effects. Human audit remains necessary to assess whether raw host
records faithfully support the submitted observations.

The contract sources are the admitted Recovery Contract, Continuation Contract
v0, and Receipt/Reconciliation Contract v0. Phase 6's independent-authorship
and sealed-holdout rules govern how this kit may support an interoperability
claim.
