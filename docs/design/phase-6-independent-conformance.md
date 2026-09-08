# Phase 6: independent ecosystem conformance

Phase 6 tests whether an implementation outside Cairn can satisfy the admitted
recovery semantics without importing Cairn code, adapters, or runtime internals.
It is not a new Cairn runtime or integration program.

## Current state: KIT_READY, not admitted

The [Conformance Kit v0](../../conformance/v0/README.md) is published and
copy-isolated. Its standard-library evaluator checks an evidence envelope for
the P1 recovery, P2 continuation/compaction, and P3 reconciliation invariants,
but does not define host state or run a host.

The P6 frozen baseline is [freeze.json](../../results/phase-6/freeze.json).
The kit validation is [kit-verdict.json](../../results/phase-6/kit-verdict.json):
14 focused checks passed, including copied-kit execution outside the repository.

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
