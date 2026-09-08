# Cairn Recovery Conformance Kit v2

This is the current verifier-owned Stage 6A reference protocol. It tests an
external host command without importing Cairn or prescribing the host's agent
loop, runtime, model, memory, scheduler, or internal state representation.

Kit v1 remains published for reproducibility but is not admissible for a new
Stage 6A claim. A failed independent run showed that v1 disclosed its case
label, negative flag, recovery continuation, task digest, and expected effect
decision to the host. A cell-labelled answer table could therefore satisfy the
runtime witness without performing semantic recovery. v2 removes those answer
channels rather than repairing that candidate.

## Run

```powershell
python witness.py --output results --host python host.py
```

The witness executes ten internal cases three times. Case names remain in the
verifier's evidence but are never present in a host request or workspace path.
Each invocation is nonce-bound and each recovery runs in a fresh process and a
new directory.

## Host command

The witness invokes:

```text
<host...> <execute|prepare|recover> <request-json>
```

`execute` and `prepare` receive an initial request with `run_nonce`, `workspace`,
and a `task` containing:

- a verifier-generated digest;
- the eight continuation obligations listed in `vectors.json`, with values
  randomized independently from the run nonce;
- `checkpoint_mode` (`full` or `compact`);
- an optional effect intent containing an unpredictable fingerprint and one of
  the admitted tool classes;
- verifier-generated volatile context used to measure real compaction.

The request never contains `cell`, `repetition`, `negative`, an expected
status, or a decision.

`prepare` must durably write `checkpoint.json` with `run_nonce`, `task_digest`,
`continuation`, `effect_intent`, and `volatile_context`. For compact mode it
must also write `compacted-checkpoint.json` preserving the first four values,
removing volatile context, and reducing the actual byte size. Effectful work
must durably write `intent.json` with the nonce, fingerprint, and tool class.
Only then may it write `ready.json` and remain alive for verifier-owned death.

The witness kills that process and copies only the selected checkpoint into a
fresh recovery directory. `recover` receives only `protocol`, `workspace`, and
`run_nonce`; it does not receive the task, continuation, effect intent, case,
or expected answer. Its first observable operation must be writing
`observation-request.json`.

The verifier then writes one of:

- a world observation containing the independently hashed checkpoint and
  whether it matches the declared recovery boundary; or
- provider facts containing only `observation` and an observed resource
  fingerprint (or `null` when no resource can be identified).

The provider response deliberately contains neither a decision nor a matching
conclusion. The host must recover the intent fingerprint and effect tool class
from durable state, compare the observed resource itself, and apply the rules
in `vectors.json`.
It writes `result.json` with the recovered continuation, response token,
status, and, for effects, the observed provider facts and computed decision.
It writes `artifact.txt` as exact bytes `artifact:<recovered-task-digest>` only
for completed/resolved outcomes.

## Verifier-owned evidence

The witness owns process creation and death, fresh directories, nonces,
provider/world observations, timestamps, file inspection, artifact hashes,
checkpoint hashes, and the final verdict. It rejects output before
re-observation, replayed tokens, fixed artifacts, nonce-derived or lost
continuation state, non-reducing compaction, missing durable intent, and
incorrect reconciliation.

No local protocol can prove the private reasoning of a fully privileged
program. Source authorship, dependency independence, prohibited imports,
evaluator-aware branches, and attempts to inspect the verifier remain subject
to a separate pre-freeze source/provenance audit. Runtime evidence and source
audit are both mandatory; neither substitutes for the other.

## Claim boundary

A 30/30 v2 reference result is only Stage 6A evidence. Phase 6 remains
unadmitted until a different sealer authors a post-freeze holdout and an
uninvolved reproducer obtains the same verdict. Do not claim a standard,
universal compatibility, native Cairn support, or exactly-once effects.
