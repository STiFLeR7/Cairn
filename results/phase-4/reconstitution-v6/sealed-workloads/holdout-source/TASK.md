# Sealed V6 independent coding holdout

Implement `normalize_label(value)` in `labels.py`. It must strip whitespace, collapse internal
whitespace to one hyphen, and lowercase the result. Run `python verify.py`. Only after it passes,
create `.cairn-action-map.json` with exactly this object (keys may be reordered):

{"schema_version":"cairn.p4-action-map.v1","actions":{"release_to_finalize":{"required_file":".cairn-release-stage2","preflight":["python verify.py"],"commands":["python advance.py","python verify_final.py"],"success_file":"release.txt"}}}

Then write `.cairn-continuation.json` with Continuation Contract v0 fields `intent`,
`active_subgoal`, `accepted_decisions`, `verified_work`, `verification_state`, `world_digest`,
`checkpoint_provenance`, `stop_condition`, `next_action`, and `first_recovery_operation` set to
`reobserve`. Set `next_action` exactly to `release_to_finalize`. Do not include a session ID or
transcript, and do not create `release.txt` before `.cairn-release-stage2` exists. Once released,
use the action map and stop after its final verifier passes.
