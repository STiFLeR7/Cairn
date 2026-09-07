# Deep Agents fallback reconnaissance

This is unsealed capability reconnaissance, not an independent conformance
submission or an admissible P6 result.

Deep Agents 0.7.13 with LangGraph 1.2.11 and SQLite checkpointing directly
emitted a native `_summarization_event` across a fresh process. Its event held
an offloaded-history path and a summary message, so the host exposed a changed
effective context boundary.

The effect negative control is decisive for scope: a process died after a local
provider committed and before the tool node completed. The fresh process then
completed without provider observation, retry, skip, or escalation. The
provider commit remained. This is not a defect in Cairn and does not mean Deep
Agents cannot host an independent implementation; it establishes that the bare
host does not itself supply Cairn's reconciliation semantics.

An eligible external implementation would need to durably record intent before
dispatch and make recovery re-observation explicit. Cairn must not provide or
patch that implementation. The fallback is therefore not promoted to
`TARGET_CAPABLE` from this reconnaissance alone.
