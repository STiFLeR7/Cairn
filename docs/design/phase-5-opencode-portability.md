# Phase 5 — OpenCode portability proof

**Status: blocked at P5.1. No portability claim is admitted.**

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

This is an evidence-profile validator, not a new Cairn contract or adapter API. It can judge
facts produced by either Claude Code or OpenCode without naming either host in its input schema.

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
its Docker engine is not running, so no OpenHands conformance workload, adapter, or Cairn change has
begun.

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
