# Independent runner protocol

This protocol is required for a Phase 6 **independent conformance** claim. It
is intentionally separate from the evaluator: `evaluate.py` checks an
evidence envelope; it cannot prove who authored a host or when a workload was
seen.

## Roles

Three people or organizations must be distinct:

| Role | May do | Must not do |
| --- | --- | --- |
| Implementer | Build and run a host using this four-file kit. | Read Cairn runtime/adapters, author a holdout, or change a sealed workload. |
| Sealer | Author and seal the public workload and holdout. | Author, patch, or coach the host implementation. |
| Reproducer | Re-run the unchanged implementation against sealed inputs. | Patch the implementation, evaluator, or workload. |

Cairn maintainers may publish the kit and evaluate submitted evidence, but may
not implement, repair, or tune the submitted host. A candidate failing an
audit is stopped; it is not repaired against a reference or holdout.

## Intake before reference disclosure

The implementer supplies a source archive or immutable repository revision
with a SHA-256 digest and a short declaration that it does not import Cairn
runtime code or Cairn-maintained host drivers. The implementer also supplies
an execution command accepting only workload root, source/workspace root, and
output root. It must fail closed when any required input is absent.

The sealer records, before execution:

- public task, verifier, and seal file digests;
- implementation revision and archive digest;
- copied-kit digest;
- exact host/runtime/model configuration;
- the 30-cell matrix and three-repetition requirement.

The public package may then be released to the implementer. The holdout stays
with the sealer.

## Required execution evidence

For each run, preserve the raw material needed to audit these facts, in
addition to the envelope required by `evidence.schema.json`:

- pre-crash and fresh-process identities plus actual termination status;
- durable checkpoint and, for C/C_NEG, durable before/after active-context
  artifacts consumed by the fresh process;
- workspace state and verifier output before and after recovery;
- provider observation, resource, receipt, and ledger artifacts for effects;
- linked evidence file hashes and the final evaluator verdict.

The implementer runs the public matrix unmodified. A failing run is a failure
classification, not a prompt, fixture, schema, or threshold tuning opportunity.

## Sealed holdout and reproduction

After the public run is frozen, the sealer independently creates and hashes a
new workload/verifier/seal package. The implementer receives it only after
the package is sealed. The reproducer receives the immutable implementation,
the copied kit, and the sealed package, then runs the same command without
changing any input. The reproducer publishes its command, environment,
manifest, raw evidence, and evaluator verdict.

Admission requires a passing public matrix, a passing sealed holdout, and a
matching uninvolved reproduction. Evaluator acceptance alone is insufficient:
the raw host records must support the claimed recovery boundaries.

## Stop conditions

Stop the candidate immediately if any of these occur:

- a claimed fresh process is synthetic or no abrupt crash is evidenced;
- recovery does not load/re-observe durable state before action;
- compaction is an event label rather than persisted state consumed by recovery;
- effect facts are derived from a fixture/cell label rather than provider state;
- a workload or implementation changes after sealing;
- the copied evaluator rejects the submission.

None of these conditions authorizes changing an admitted Cairn contract.
