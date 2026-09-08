# Phase 6 verifier-grounded conformance

## Decision

Conformance Kit v0 is a historical **structural evidence-envelope** evaluator. It
checks that a submitter's referenced files hash to the values that the same
submitter supplied. It does not establish that those files came from a host
process, a process death, a fresh recovery process, a real workspace, native
compaction, or an external provider. A v0 pass is therefore not admissible as
Phase 6 independent-conformance evidence.

Conformance Kit v1 adds a host-neutral verifier-owned witness. The witness
launches and kills host child processes, creates the fresh recovery workspace,
generates a per-run nonce, hashes checkpoints and artifacts itself, and serves
the observation/provider mailbox only after fresh recovery begins. It does not
import Cairn or dictate a host runtime, state representation, agent loop,
model, tools, persistence, or scheduler.

## v0 trust audit

| Claimed fact | What v0 checks | Trust status | v1 treatment |
| --- | --- | --- | --- |
| Process identity and death | Submitter-provided IDs/events are distinct and ordered | Self-attested | Witness records child PID and forced exit status. |
| Fresh process / unavailable transcript | Submitter boolean and events | Self-attested | Witness kills one child and starts another in a new directory containing only the admitted checkpoint. |
| Checkpoint / continuation contents | Presence of reported digests | Self-attested | Witness reads and hashes the checkpoint; required continuation fields are validated. |
| Artifact and verified work | Reported fixed digests | Self-attested | Witness hashes actual artifact files and validates their deterministic contents. |
| Compaction | Reported events and two hashes | Self-attested | Witness reads two distinct state files and supplies only compacted state to recovery. |
| Provider observation / reconciliation | Cell-labelled reported fields/events | Self-attested | Witness creates the observation response after recovery starts and validates the action token and decision. |
| Evidence provenance | File hash equals submitter's inventory entry | Self-attested | Witness writes the complete run record, nonces, mailboxes, hashes, and verdict. |
| Implementation provenance / semantic intent | Repository strings and author declaration | Self-attested | Retained as declared metadata; source/dependency audit remains required. |

The v0 test fixture intentionally demonstrates the weakness: it constructs
all thirty entries from synthetic IDs, fixed digests, label-selected provider
facts, and small JSON files, then v0 accepts it. That is a specification
finding, not evidence of runtime recovery.

## What v1 proves and does not prove

v1 proves that a host command performed verifier-observable process,
filesystem, checkpoint, fresh-workspace, observation, and effect-provider
protocol actions for each evaluated cell. The verifier derives its own run
records and outcome from those observations.

No local evaluator can cryptographically prove an arbitrary program's private
reasoning or prevent a fully privileged hostile program from reading/verifying
its own files. v1 therefore labels author identity, source provenance, and
semantic intent as self-attested and requires an independent source/dependency
audit for Stage 6A. It deliberately makes ordinary fabricated evidence,
static cell tables, replayed manifests, synthetic PIDs, fixed hashes, skipped
recovery, fake compaction, and unobserved provider claims fail mechanically.

## Required adversarial controls

| Attack | Mechanical v1 rejection |
| --- | --- |
| Fabricated PID/process event | PID and termination status come from `subprocess.Popen`, not the host. |
| Fixed artifact hash | Witness recomputes artifact bytes and checks their nonce/task binding. |
| Hard-coded PASS/reference vector | Each run has a verifier-generated nonce/action token unavailable before recovery. |
| Cell-label-derived provider output | Witness-generated provider observation includes an unpredictable response token and is the sole decision input. |
| Replayed evidence | Every checkpoint, mailbox, result, and manifest is nonce-bound; prior-run values are rejected. |
| Skipped recovery | A ready pre-crash child must be alive when verifier kills it; recovery runs under another observed PID in a fresh directory. |
| Semantically plausible, wrong state | Witness validates all required continuation values and final artifact binding against the declared checkpoint. |
| Claimed-but-not-performed compaction | Witness validates a distinct compacted checkpoint and exposes only it to recovery. |
| Claimed effect reconciliation without provider observation | Witness requires a nonce-bound mailbox request before accepting a decision. |

## Stage 6 status

v1 is a Stage 6A reference-vector protocol only. A v1 pass does not admit
Phase 6, create a sealed holdout, or replace the independent SEALER and
REPRODUCER required for Stage 6B.
