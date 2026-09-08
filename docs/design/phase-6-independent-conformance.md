# Phase 6: independent ecosystem conformance

Phase 6 tests whether an implementation outside Cairn can satisfy the admitted
recovery semantics without importing Cairn code, adapters, or runtime internals.
It is not a new Cairn runtime or integration program.

## Current state: BLOCKED / UNADMITTED

The [Conformance Kit v0](../../conformance/v0/README.md) is published and
copy-isolated. Its standard-library evaluator checks an evidence envelope for
the P1 recovery, P2 continuation/compaction, and P3 reconciliation invariants,
but does not define host state or run a host.

The P6 frozen baseline is [freeze.json](../../results/phase-6/freeze.json).
The kit validation is [kit-verdict.json](../../results/phase-6/kit-verdict.json):
14 focused checks passed for its then-current four-file kit, including
copied-kit execution outside the repository. The current handoff validation is
[external-authority-handoff-validation.json](../../results/phase-6/external-authority-handoff-validation.json):
15 focused checks passed against the current four-file kit.
The [external-authority handoff](../../conformance/v0/PHASE6-EXTERNAL-HANDOFF.md)
now defines the required separate IMPLEMENTER, SEALER, and REPRODUCER chain
for an immutable `D:/imgshape` workload snapshot. Until that external chain
completes, no Phase 6 conformance claim is permitted.

## Two-stage independent-conformance gate

### Stage 6A — independent implementation

An implementer may use only the published four-file kit, its public profile,
vectors, and evaluator interface to create a new runtime in a fresh repository.
It must independently demonstrate an actual abrupt process death, a distinct
fresh process, durable continuation/compaction state consumed by recovery,
provider-derived effect observation, and raw state-derived evidence. A Stage
6A pass requires the sealed 30-cell reference matrix and evaluator acceptance;
it does not admit Phase 6 or authorize a holdout claim.

The first Stage 6A Haiku-only candidate is a **FAIL before reference
execution**. Its source did not import Cairn and did not touch `D:/imgshape`,
but audit found a synthetic `parent_pid + 1` identity, fallback-generated
events/finals, fixed artifact hashes, and effect state selected from cell
labels. The external repository and raw trace are preserved at the path and
hashes recorded in
[stage-6a-haiku-candidate-1.json](../../results/phase-6/stage-6a-haiku-candidate-1.json).
It was stopped rather than repaired or evaluated.

### Stage 6B — independent sealing and reproduction

Stage 6B remains blocked until a separate Stage 6A implementation has passed
the reference matrix and been frozen. Only then may an independent SEALER
author the holdout and an uninvolved REPRODUCER execute it. Stage 6A alone is
not evidence of ecosystem portability or a Phase 6 admission.

Pydantic AI 2.40.0 plus DBOS 2.31.0 was the first capability target. It is
stopped for this environment, not rejected as an ecosystem: its deterministic
`TestModel` does not support `compact_messages`, and the provider-native
compaction route cannot be executed without an OpenAI credential. The direct
records and stopped verdict are under
[capability-acquisition](../../results/phase-6/capability-acquisition/). Cairn
did not simulate a compaction boundary to pass this gate.

The permitted Deep Agents/LangGraph fallback exposed native compaction and
SQLite-backed fresh-process state, but its bare-host effect negative control
completed after a provider-commit crash without provider re-observation or a
retry/skip/escalate decision. It is not promoted as a conformance target from
that result. The unsealed records are in
[deepagents-fallback](../../results/phase-6/deepagents-fallback/); they show
the semantic work an independent implementation must actually provide.

An external, Haiku-authored runtime then passed its public-reference control
but failed the sealed-holdout/reproducer gate. Its frozen entrypoint had no
workload input and hard-coded the public reference path; the uninvolved
reproducer could not target the sealed holdout without prohibited adaptation.
The [stopped verdict](../../results/phase-6/external-independent-runtime-v1/)
preserves the candidate, holdout, and reproducer provenance. This is an
implementation-boundary failure, not a change to any admitted contract or a
Phase 6 admission.

A second Haiku-authored candidate was stopped earlier, before any public
reference workload was disclosed. Although its local smoke envelope satisfied
the former evaluator, source review showed that it generated evaluator-shaped
facts rather than recovering durable operational state: its checkpoint omitted
the required continuation semantics, its compaction hashes were unrelated to
persisted context, its fresh process did not re-observe the workspace, and its
effect facts were parent-synthesized. It also used all-zero verifier and seal
digests. The raw record is under
[external-independent-runtime-v2](../../results/phase-6/external-independent-runtime-v2/).
The copied kit now rejects placeholder workload digests. This remains a
candidate and evaluator-provenance finding; no Cairn contract changed and P6
is still not admitted.

A third Haiku-authored local-smoke candidate was also stopped before reference
disclosure. It had a non-placeholder sealed smoke envelope and passed the
structural evaluator, but source audit found a fabricated `parent_pid + 1000`
child, no `os._exit(137)` or subprocess recovery, no actual workspace
re-observation, pre-claimed verified work, and fixed provider facts. The
[v3 stopped record](../../results/phase-6/external-independent-runtime-v3/)
is a second reminder that evaluator acceptance is necessary but insufficient:
the implementation and its raw host records must survive independent audit.
P6 remains not admitted.

A fourth clean-room, Haiku-authored candidate added real subprocess PIDs but
was stopped before reference disclosure as well. Its generated 30-run
submission fails the copied evaluator because event evidence references are
not inventoried, and its `E_ESC_NEVER` record violates the published vector.
Source review independently found that compaction was never consumed by phase
2, effect facts were derived from cell names, and the declared author was on
the Cairn side. The [v4 stopped record](../../results/phase-6/external-independent-runtime-v4/)
preserves the exact revision and failures. It does not change any contract or
admit P6.

## Admission gate

Phase 6 can be admitted only when all of the following exist:

1. A non-Cairn implementation uses only the copied kit.
2. Its author and repository provenance prove it does not import Cairn runtime
   code or copied Cairn host drivers.
3. It passes the complete 30-cell public reference matrix, with linked raw host
   evidence audited against the envelope.
4. A different holdout author seals and runs an unchanged 30-cell holdout.
5. An uninvolved reproducer obtains the same verdict from the sealed inputs.

Until then, the only allowed claim is that Cairn has a published, executable
conformance kit. It is not an interoperability standard, universal framework
compatibility claim, native-host feature, or exactly-once guarantee.

## Smallest next action

An independent implementer should choose a host that can directly expose a
fresh process, durable workspace and journal, native compaction completion plus
changed active context, ordered effect events, and an ambiguous effect window.
They then submit the sealed evidence envelope to the copied evaluator. Cairn
maintainers do not author or patch that host implementation.
