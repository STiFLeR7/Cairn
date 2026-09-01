# OpenCode native-compaction reassessment — 2026-09-01

This directory preserves the direct capability probes performed after the original
1.18.20 and 1.18.25 empty-body probes.  No Cairn code, contract, workload, or
threshold changed.  Each probe used one fresh OpenCode session, the host's native
durable event stream to establish a terminal `session.next.step.ended` boundary,
and one documented `POST /api/session/{sessionID}/compact` call while idle.

The local OpenAPI documents for stable, beta, and dev all describe `compact` with
only `sessionID` as a path parameter and no request body.  That supersedes the
earlier hypothesis that the released API required the `model` body used by the
current development UI source.  Session model selection was instead supplied at
creation as `{ "providerID": "opencode", "id": "big-pickle" }`.

`big-pickle` was active with a catalog context limit of 200000 tokens.  The beta
and dev probes both received `503 ServiceUnavailableError: Session compact is not
available yet` after their own durable terminal event.  Therefore this is neither
a model-context-limit failure nor a compact-during-execution race.

The records are negative capability evidence only.  They do not claim a Cairn
defect, an OpenCode semantic failure beyond this required host boundary, or an
admitted portability result.
