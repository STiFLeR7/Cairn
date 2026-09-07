# P6.2 Pydantic AI/DBOS capability acquisition

State: `TARGET_STOPPED`.

The selected Pydantic AI/DBOS target was probed in a disposable Python 3.12.4
environment. DBOS 2.31.0 launched and completed a SQLite-backed workflow, but
the only credential-free deterministic Pydantic model, `TestModel`, directly
raised `NotImplementedError` for `compact_messages`. Enabling Pydantic AI's
OpenAI optional dependency made `OpenAICompaction` importable, but this
environment has no `OPENAI_API_KEY`; therefore a provider-native completion
event and changed active-context boundary cannot be directly observed.

This is a configuration/environment capability stop, not evidence that Pydantic
AI or DBOS lack durable execution. It prevents this target from serving as the
Phase 6 proof host because native compaction is a non-negotiable conformance
requirement. No mock model, summary, polling loop, transcript scrape, or
synthetic compaction boundary was substituted.

`raw/` contains the direct command outcomes. `observations.json` intentionally
marks every unproven condition false; it is an admission gate, not a statement
that each unrun condition is impossible. The first causal blocker is
`compaction_completed`, which also makes `active_context_changed` unprovable.

The next permitted action is a separately recorded probe of the approved
LangGraph/Deep Agents fallback under the same seven direct-observation
requirements. Cairn contracts and core are unchanged.
