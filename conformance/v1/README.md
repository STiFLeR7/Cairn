# Cairn Recovery Conformance Kit v1

This is a verifier-owned, host-neutral reference conformance protocol. It is
not a Cairn runtime, adapter, agent loop, state schema, memory system, or
workflow engine. A host supplies one command; the witness drives its boundary
and writes all admissible evidence.

## Run

```powershell
python witness.py --output results --host python host.py
```

The witness runs the ten cells (`U`, `R`, `R_NEG`, `C`, `C_NEG`, and five
effect cells) three times. It exits nonzero on a rejected cell and writes
`manifest.json` plus one verifier-derived record per run.

## Host command protocol

The witness invokes the supplied command as:

```text
<host...> <phase> <request-json>
```

`phase` is `execute`, `prepare`, or `recover`. The request JSON names only a
workspace owned for that invocation and includes a verifier-generated
`run_nonce`. A host must not require a transcript, conversation, or prior
process memory.

- `execute` (`U`) writes `artifact.txt` and `result.json` in the supplied
  workspace.
- `prepare` writes `checkpoint.json` with every name in
  `vectors.json.continuation_required`, then writes `ready.json` and remains
  alive. For `C`/`C_NEG`, it also writes a distinct
  `compacted-checkpoint.json` preserving those values. For effect cells it
  writes `intent.json` before readiness.
- The witness reads state, then kills the live `prepare` child. It creates a
  wholly new recovery workspace containing only `checkpoint.json` (or only
  `compacted-checkpoint.json` for compaction). It then invokes `recover`.
- `recover` must first write `observation-request.json`. The witness responds
  with a unique `observation-response.json`; for effect cells this is the
  provider observation. The host then writes `artifact.txt` where allowed and
`result.json` containing the recovered `continuation`, observed response token,
  requested decision (`retry`, `skip`, or `escalate` for effect cells), and
  `status`.

The required continuation values are fixed by the `prepare` checkpoint and
must survive compaction/recovery unchanged. `artifact.txt` must exactly equal
`artifact:<task_digest>`. The task digest is verifier-generated and shared only
by the U/R/C triplet for the same repetition. Negative/escalation cells must not write
an artifact. The witness never accepts host-reported hashes, PIDs, events,
provider state, or verdicts.

## Evidence and limits

The witness records OS-observed child PIDs and termination status, actual file
hashes, fresh-workspace paths, mailbox hashes, action/observation tokens,
provider responses, and a nonce-bound manifest. This rejects ordinary
synthetic/replayed evidence. Implementation authorship, source independence,
and an arbitrary program's internal reasoning cannot be established by a
local execution protocol; supply a separate provenance and dependency audit.

Kit v1 is only Stage 6A reference evidence. It is not Phase 6 admission and
does not replace independently sealed holdout/reproduction in Stage 6B.
