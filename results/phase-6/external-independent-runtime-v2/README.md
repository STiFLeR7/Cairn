# External independent runtime v2: stopped before reference

This Haiku-authored candidate was a local smoke rehearsal only. Its copied-kit
evaluator result was `passed: true`, but a source audit rejected it before any
reference or holdout workload was exposed.

The raw paths and immutable hashes are in [verdict.json](verdict.json). The
candidate had no usable durable continuation state, no actual active-context
compaction consumed by fresh recovery, no workspace re-observation, and no
provider-derived effect facts. It also supplied placeholder all-zero verifier
and seal digests.

This is a candidate implementation failure and a workload-provenance weakness
in the former evaluator. It is not P6 admission evidence, a contract failure,
or a reason to alter an admitted contract.
