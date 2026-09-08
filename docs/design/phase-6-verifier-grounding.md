# Phase 6 verifier-grounded conformance

## Decision

Conformance Kit v0 is a historical **structural evidence-envelope** evaluator. It
checks that a submitter's referenced files hash to the values that the same
submitter supplied. It does not establish that those files came from a host
process, a process death, a fresh recovery process, a real workspace, native
compaction, or an external provider. A v0 pass is therefore not admissible as
Phase 6 independent-conformance evidence.

Conformance Kit v1 added a host-neutral verifier-owned witness, but it exposed
its case label, negative flag, continuation/task values again at recovery, and
the expected provider decision. Candidate 5 used those fields to construct a
reference-answer table. The pre-freeze source audit stopped the candidate, but
the v1 runtime witness alone could not distinguish that table from semantic
reconciliation.

Conformance Kit v2 keeps verifier-owned child death, fresh recovery workspaces,
nonces, filesystem hashes, and provider/world mailboxes while removing those
answer channels. Recovery receives only a workspace and nonce, case names are
absent from host-visible paths and requests, and provider responses contain an
observation/resource fingerprint but no matching conclusion or decision. The
host must recover continuation, task digest, and effect intent from the selected
checkpoint. v2 does not import Cairn or dictate a host runtime, agent loop,
model, memory, tools, persistence, or scheduler.

## Trust-boundary evolution

| Claimed fact | v0 | v1 limitation | v2 treatment |
| --- | --- | --- | --- |
| Process identity and death | Self-attested IDs/events | Verifier-owned | Verifier records child PID, timestamps, kill, and exit. |
| Fresh process / unavailable transcript | Self-attested | Fresh directory, but recovery request repeated task state | Fresh directory contains only selected checkpoint plus a request with workspace and nonce. |
| Checkpoint / continuation contents | Reported digests | Verifier-read, but recovery could copy repeated request values | Verifier validates checkpoint state and withholds it from recovery input. |
| Artifact and verified work | Reported fixed digests | Verifier-owned | Verifier hashes actual bytes bound to checkpoint-recovered task state. |
| Compaction | Reported events/hashes | Distinct bytes only | Verifier requires removal of random volatile context, fewer bytes, and recovery from only compacted state. |
| Provider reconciliation | Cell-labelled facts | Host saw cell and expected decision | Host compares a post-restart resource fingerprint with checkpoint-recovered intent, then applies the recovered tool class. |
| Evidence provenance | Submitter inventory | Verifier-owned | Verifier writes timestamps, process facts, mailboxes, hashes, records, and verdict. |
| Implementation provenance / private reasoning | Self-attested | Separate audit required | Separate source/dependency/provenance audit remains required. |

The v0 test fixture intentionally demonstrates the weakness: it constructs
all thirty entries from synthetic IDs, fixed digests, label-selected provider
facts, and small JSON files, then v0 accepts it. That is a specification
finding, not evidence of runtime recovery.

## What v2 proves and does not prove

v2 proves that a host command performed verifier-observable process,
filesystem, checkpoint, fresh-workspace, observation, and effect-provider
protocol actions for each evaluated cell. It additionally proves that recovered
task/continuation/effect inputs came from the selected checkpoint rather than a
repeated recovery request, and that the host produced a decision without being
given the expected answer. The verifier derives its own records and outcome.

No local evaluator can cryptographically prove an arbitrary program's private
reasoning or prevent a fully privileged hostile program from inspecting its
parent or verifier. v2 therefore still requires an independent source and
dependency audit. The runtime protocol removes the ordinary static-table path;
evaluator-aware inspection remains a provenance failure, not a cryptographically
solvable local property.

## Required adversarial controls

| Attack | Mechanical v2 rejection |
| --- | --- |
| Fabricated PID/process event | PID and termination status come from `subprocess.Popen`, not the host. |
| Fixed artifact hash | Witness recomputes artifact bytes and checks their nonce/task binding. |
| Hard-coded PASS/reference vector | Artifact/state values are random and verifier-bound; recovery is not given them again. |
| Cell-label-derived provider output | No cell label appears in host requests or workspace paths. |
| Copy matching/decision conclusions | Provider response has observation/resource identity but no matching boolean or decision. |
| Replayed evidence | Every checkpoint, mailbox, result, and manifest is nonce-bound; prior-run values are rejected. |
| Skipped recovery | A ready pre-crash child must be alive when verifier kills it; recovery runs under another observed PID in a fresh directory. |
| Semantically plausible, wrong state | Witness validates all required continuation values and final artifact binding against the declared checkpoint. |
| Claimed-but-not-performed compaction | Witness requires volatile-context removal, actual byte reduction, and recovery from only compacted state. |
| Claimed effect reconciliation without provider observation | Witness requires a nonce-bound mailbox request before accepting a decision. |

## Stage 6 status

v2 is a Stage 6A reference-vector protocol only. A v2 pass does not admit
Phase 6, create a sealed holdout, or replace the independent SEALER and
REPRODUCER required for Stage 6B.
