# Phase 5 — second-host portability proof

**Status: admitted narrowly. OpenHands P5.1, P5.3, and independently sealed P5.4 passed; the P5.5 two-host verdict joins them to the already admitted Claude Code P4 evidence.**

Phase 5 asks whether a second, independently implemented coding-agent host can consume Cairn's
admitted recovery, continuation, and receipt/reconciliation semantics through a thin, host-owned
boundary. It does not broaden either v0 contract and does not add a Cairn runtime, memory system,
or OpenCode-specific core abstraction.

## P5.0 — host-neutral conformance profile

`benchmarks/p5_conformance.py` validates only host-observed semantic facts. It does not start a
host, translate a `ContinuationState`, read a transcript, or prescribe an adapter. A conforming
fact set identifies the host/version/model, sealed workload/verifier, checkpoint and artifact
identities, crash and fresh-process identities, recovery-input boundary, first operation, native
compaction event, effect observation/resolution, and final result.

The required matrix remains fixed: `U`, `R`, `R_NEG`, `C`, `C_NEG`, and `EFFECT`. Positive coding
cells require verified artifact equivalence; negative cells require safe termination with no
unauthorized action. Fresh recovery requires a distinct identity, no original transcript, and
`reobserve` as its first operation. Compaction requires both a host-native operation and a directly
observed completion event. Effect recovery requires provider observation before resolution.

This is an evidence-profile validator, not a new Cairn contract or adapter API. It judges facts
without naming a host in its input schema.

## P5.1 — direct capability acquisition

The local OpenCode 1.18.20 server was started at `127.0.0.1:4095`. Its live OpenAPI document exposed
session creation/prompting, durable session SSE, `/api/session/{id}/compact`, active-context
inspection, and session events. A non-mutating `opencode/big-pickle` probe created a session,
admitted a prompt, completed without tools or file changes, and emitted ordered durable events
through sequence 8. The raw trace is preserved in
[`results/phase-5/capability-acquisition/`](../../results/phase-5/capability-acquisition/).

The required native-compaction proof failed before any workload was authored:

```text
POST /api/session/{sessionID}/compact
→ 503 ServiceUnavailableError: Session compact is not available yet
```

No `session.compacted` event or post-compaction active-context change was observable. An advertised
route is not evidence that the host can perform the required behavior. Under Phase 5's governing
rules, this is a **host limitation**, not a Cairn defect and not a reason to simulate compaction or
substitute transcript handling.

The installed host was then updated to the latest available npm release, OpenCode 1.18.25, and the
same direct probe was repeated in a fresh server/session. It reproduced the same `503` response; the
active context remained at two messages and no completion event appeared. The raw retest is preserved
in [`results/phase-5/capability-acquisition-retest-1.18.25/`](../../results/phase-5/capability-acquisition-retest-1.18.25/).
### Reassessment and target decision — 2026-09-01

The initial classification was deliberately revisited before a target change. Current OpenCode
development UI source calls `session.compact` with a selected model, but the *live* OpenAPI documents
served by all tested host builds declare only `sessionID` and no request body. The selected
`opencode/big-pickle` model was active and advertised a 200000-token context limit. The beta and dev
probes additionally waited for the host's durable `session.next.step.ended` event before invoking
`compact`; both still returned the same `503`.

The reassessment rules out the API-body, selected-model-context-limit, and in-flight-step hypotheses.
OpenCode native compaction is unavailable through this boundary in every tested pinned build: stable
`1.18.25`, beta `0.0.0-beta-202608110357`, and dev `0.0.0-dev-202609010712`. Full negative evidence
and its manifest are preserved in
[`results/phase-5/capability-acquisition-reassessment-2026-09-01/`](../../results/phase-5/capability-acquisition-reassessment-2026-09-01/).

**Decision:** stop the OpenCode P5 path. This is a host capability limitation, not an OpenCode
configuration/provider/model failure and not a Cairn contract deficiency. Do not retry this target
unless a future pinned build directly demonstrates the three unblocking facts below.

OpenHands is the approved fallback candidate, not an admitted replacement yet. Its public SDK has an
event-driven state model, emits a `Condensation` event from host-owned condensation, and documents
atomic interruptible agent steps. Those make a thin host-owned OpenHands driver capable in principle
of satisfying the same semantic profile. It must first pass a separate P5.1 capability acquisition:
direct condensation-completion event, changed host active view, fresh-process/session control,
durable-workspace observation, and event ordering. The current machine has no `openhands` command and
at that decision point its Docker engine was not running, so no OpenHands conformance workload,
adapter, or Cairn change had begun.

After that failure, Cairn did not inject a process death, test tool ordering, author a workload,
write an adapter, or execute a reference/holdout matrix. Those actions would not repair the missing
native capability and would contaminate the portability proof.

## Unblocking condition

Restart OpenCode P5.1 only with a future pinned OpenCode release/configuration in which the host directly produces:

1. a successful native `compact` request;
2. a durable host compaction-completed event; and
3. an active-context observation demonstrably after that boundary.

Until then, the smallest next implementation state is **OpenHands P5.1 capability acquisition**. It
must prove the same three native facts plus the existing host-control prerequisites before any P5.2
workload is authored. Do not reuse an OpenCode probe as a workload, modify an admitted Cairn contract,
or treat an endpoint declaration as a substitute for the three observations above.

## Scope

This blocked result says nothing about OpenCode's general quality, Claude Code conformance, or the
portability of Cairn's contracts. It admits no framework compatibility, standard, exactly-once
delivery, or native Cairn support by OpenCode.

## OpenHands P5.1 — direct capability acquisition

The approved fallback has passed its host-capability gate using the released OpenHands SDK 1.42.1 and
matching terminal tools 1.42.1. A direct `LocalConversation.condense()` call appended the host's
`Condensation` event and changed the active view from 17 to 6 events. A separate Python process then
reopened the same persisted conversation and retained that event/view. A second control drove the
host-owned terminal tool: the event log recorded `ActionEvent` before `ObservationEvent`, and the tool
wrote a marker into the OpenHands workspace. Finally, a process holding a durable conversation was
force-terminated; a distinct fresh process reopened the persisted event state.

The complete raw evidence, persisted host event log, workspace marker, probe, and manifest are in
[`results/phase-5/openhands-capability-acquisition/`](../../results/phase-5/openhands-capability-acquisition/).
The deterministic `TestLLM` controls prove host boundary availability only. They are not a real-model
conformance result and do not authorize a portability claim.

## OpenHands P5.2 — independently sealed reference workload

The public reference coding and provider-like effect fixtures were authored after P5.1 and frozen
before any OpenHands conformance host process was started. They use a route-report code task and a
maintenance-window provider, rather than a Phase 4 fixture, action map, prompt, command, or verifier.
Their pre-registered matrix, fixed host inputs, and scope are in
[`results/phase-5/openhands-reference-v1/PRE_REGISTRATION.md`](../../results/phase-5/openhands-reference-v1/PRE_REGISTRATION.md);
the workload hash manifest is
[`results/phase-5/openhands-reference-v1/workload-manifest.json`](../../results/phase-5/openhands-reference-v1/workload-manifest.json).

The coding fixture correctly fails before host execution at its explicit `NotImplementedError`; the
provider verifier passes in an isolated temporary directory. Those are fixture controls, not host
results.

## OpenHands P5.3 — sealed reference conformance

The thin driver in [`benchmarks/p5_openhands_protocol.py`](../../benchmarks/p5_openhands_protocol.py)
uses OpenHands `LocalConversation`, its terminal tool, and a deterministic `TestLLM` only at the host
boundary. It neither imports Cairn's runtime nor transfers host sessions or transcripts into the raw
Continuation Contract input. The fully sealed reference matrix passed in
[`reference-run-11`](../../results/phase-5/openhands-reference-v1/reference-run-11/): uninterrupted
U, fresh-process R/R_NEG, native-condensation C/C_NEG, and the provider-commit-before-receipt EFFECT
cell. Fresh coding recovery re-observed before action; native condensation emitted a host
`Condensation` event and changed the active view; the effect recovery observed the one matching
resource before `skip`, with verified provider parity. The raw records are frozen by its
[`evidence manifest`](../../results/phase-5/openhands-reference-v1/reference-run-11/evidence-manifest.json).

This is a host-capability and deterministic-control result, not a real-model score or a portability
admission.

## OpenHands P5.4 — independently sealed holdout

The holdout was authored after P5.3's raw evidence was committed. Its ledger-digest coding task and
archive-job provider have distinct task text, source names, completion artifact, verifier assumptions,
intent fingerprint, and terminal actions. The public registration and workload hashes are in
[`results/phase-5/openhands-holdout-v1/`](../../results/phase-5/openhands-holdout-v1/). Its starter
coding verifier fails at the declared `NotImplementedError`; its isolated provider verifier passes.
Its completed [`holdout-run-1`](../../results/phase-5/openhands-holdout-v1/holdout-run-1/) passed all
six cells with a matching raw-evidence manifest: verified U/R/C artifacts, safe negative termination,
native `Condensation` plus active-view change, and fresh matching-present archive observation before
`skip`.

## P5.5 — two-host portability verdict

[`two-host-portability-verdict.json`](../../results/phase-5/two-host-portability-verdict.json) is PASS.
It evaluates the admitted Claude Code P4 V5/V6 verdict facts alongside the OpenHands P5 reference and
independent holdout using the same recovery, continuation, compaction, safe-termination, and
re-observe-before-effect-resolution obligations. Both hosts retain their own execution boundary;
Cairn supplies neither host's loop, planner, scheduler, memory, or runtime.

During this check, the P4 evidence manifests were found to list ignored regenerable `__pycache__` files
that were absent from the published repository. The manifest helper now excludes that transient bytecode
both when writing and validating, and the V5/V6 manifests were repacked against their unchanged raw
records. This repairs evidence packaging only; it does not alter P4's workload, verifier, contract,
host execution, or admission verdict.

The admission is deliberately bounded: it proves deterministic two-host consumption of the existing
contracts, not universal framework compatibility, host-native Cairn support, exactly-once delivery,
or a general adapter API or ecosystem-standard candidate.
