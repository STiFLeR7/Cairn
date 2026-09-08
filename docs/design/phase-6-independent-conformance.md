# Phase 6: independent ecosystem conformance

Phase 6 tests whether an implementation outside Cairn can satisfy the admitted
recovery semantics without importing Cairn code, adapters, or runtime internals.
It is not a new Cairn runtime or integration program.

## Current state: BLOCKED / UNADMITTED

The historical [Conformance Kit v0](../../conformance/v0/README.md) validates a
self-attested evidence envelope only. [Kit v1](../../conformance/v1/README.md)
added verifier-owned processes, workspaces, hashes, and mailboxes, but candidate
5 demonstrated that its host inputs still disclosed reference labels and
expected answers. Both remain published for reproduction but are not
admissible for a new Stage 6A run. The required
[Conformance Kit v2](../../conformance/v2/README.md) retains verifier ownership
while removing those answer channels. The full trust boundary and limits are
in the [verifier-grounding design](phase-6-verifier-grounding.md).

The P6 frozen baseline is [freeze.json](../../results/phase-6/freeze.json).
The published v2 validation is
[verifier-grounded-kit-v2.json](../../results/phase-6/verifier-grounded-kit-v2.json):
15 focused checks passed at commit
`214344b74ad3cedb143d8c57745679d04f47befc`. A later candidate exposed a
nonce-derived continuation shortcut before reference execution. The local
[nonce-independence hardening](../../results/phase-6/verifier-grounded-kit-v2-nonce-hardening.json)
adds a sixteenth adversarial check and independently randomizes continuation
values at commit `7e9bd81879fe48433d5e08e18fc36750791da1fe`.
That correction is published in the admissible public input
`0ec49cc140888ec96411c30deac540d66ed0294f`.
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

An implementer may use only the published v2 kit, its public profile, vectors,
and witness interface to create a new runtime in a fresh repository.
It must independently demonstrate an actual abrupt process death, a distinct
fresh process, durable continuation/compaction state consumed by recovery,
provider-derived effect observation, and raw state-derived evidence. A Stage
6A pass requires the sealed 30-cell reference matrix and evaluator acceptance;
it does not admit Phase 6 or authorize a holdout claim.

The first Stage 6A Haiku-only candidate is a **FAIL before reference
execution**. Its source did not import Cairn and did not touch `D:/imgshape`,
but audit found a synthetic `parent_pid + 1` identity, fallback-generated
events/finals, fixed artifact hashes, and effect state selected from cell
labels. This exposed a v0 conformance-kit weakness, so v0 was replaced by a
verifier-owned witness rather than repairing or evaluating the candidate. The
external repository and raw trace are preserved at the path and hashes recorded in
[stage-6a-haiku-candidate-1.json](../../results/phase-6/stage-6a-haiku-candidate-1.json).
It was stopped rather than repaired or evaluated.

Candidate 5 used the verifier-owned v1 witness and was also stopped before
reference execution. Its source imported no Cairn package and its accepted
source-producing traces contain only `claude-haiku-4-5-20251001`, but
`effects.py` embedded the five reference labels with their provider facts and
expected decisions. `prepare.py` selected intent facts from the label and
`recover.py` copied `provider.decision`. The frozen rejected commit, trace
hashes, and non-executed gates are recorded in
[stage-6a-haiku-candidate-5.json](../../results/phase-6/stage-6a-haiku-candidate-5.json).
This is both an implementation failure and a v1 protocol finding; it changes
no admitted Cairn contract. Kit v2 is the only route for a subsequent run.

Candidate 6 consumed the published v2 kit and was stopped before tests or the
reference matrix. Its uninterrupted path ignored `task.continuation` and
recreated the witness's then-predictable `<field>:<run_nonce>` values. All 504
recorded model messages used `claude-haiku-4-5-20251001`; no Cairn import,
`D:/imgshape` access, or out-of-scope tool access was found. The rejected source
commit, trace hashes, and non-executed gates are recorded in
[stage-6a-haiku-candidate-6.json](../../results/phase-6/stage-6a-haiku-candidate-6.json).
This is an implementation failure and a v2 challenge-generation finding, not a
Continuation Contract change. At that point another candidate could not receive
the kit until the nonce-independence hardening was published.

Candidate 7 is the first **Stage 6A PASS** against the corrected public input.
A Claude Code team whose 301 recorded model responses all identify
`claude-haiku-4-5-20251001` built a new implementation in a separate repository
from the public v2 kit. Its frozen commit `ca29b601454f83d0ab75433522c40930089bc5d3`
passed 23 local tests and the complete answer-free reference matrix 30/30.
The public evaluator accepted, and a separate audit recomputed continuation,
checkpoint/compaction, mailbox, effect-decision, artifact, and negative-action
facts with zero discrepancies. A verifier-owned exact-state exercise then
killed the checkpoint process and recovered all 115 Git-visible files in
`D:/imgshape` from a distinct fresh process with unchanged HEAD and worktree.
The frozen source bundle and sanitized records are in
[stage-6a-haiku-candidate-7](../../results/phase-6/stage-6a-haiku-candidate-7/).
This satisfies only Stage 6A; it is not a Phase 6 admission.

### Stage 6B — independent sealing and reproduction

The Stage 6A implementation is now frozen and reference-passing. Stage 6B
remains blocked on a genuinely separate SEALER authoring the post-freeze
holdout and an uninvolved REPRODUCER executing it. Stage 6A alone is not
evidence of ecosystem portability or a Phase 6 admission.

The executable actor boundary, frozen candidate identities, sealing rules, and
commands are published in the
[v2 Stage 6B handoff](../../conformance/v2/STAGE6B-HANDOFF.md). Cairn does not
provide either missing authority.

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
3. It passes the complete 30-cell public reference matrix through the v2
   witness, with verifier-derived raw process/workspace/mailbox evidence and
   an independent source/dependency audit.
4. A different holdout author seals and runs an unchanged 30-cell holdout.
5. An uninvolved reproducer obtains the same verdict from the sealed inputs.

Until then, the only allowed claim is that Cairn has a published, executable
conformance kit. It is not an interoperability standard, universal framework
compatibility claim, native-host feature, or exactly-once guarantee.

## Smallest next action

A separate SEALER receives the frozen candidate bundle and authors a new,
fully specified post-freeze holdout without modifying the implementation. An
uninvolved REPRODUCER then executes that sealed input in a fresh environment.
Any implementation change invalidates the Stage 6A freeze and requires a new
candidate identity.
