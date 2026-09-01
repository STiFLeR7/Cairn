# Task

Implement `greet(name)` in `greeting.py`. It must return exactly `Hello, <name>!`.
Run `python verify.py`. Only after it passes, create `.cairn-action-map.json` with
this exact JSON object (keys may be reordered):

{"schema_version":"cairn.p4-action-map.v1","actions":{"wait_for_release_then_complete":{"required_file":".cairn-release-stage2","preflight":["python verify.py"],"commands":["python stage2.py","python verify_final.py"],"success_file":"stage2.txt"}}}

Then write `.cairn-continuation.json` with the Continuation Contract v0 fields:
`intent`, `active_subgoal`, `accepted_decisions`, `verified_work`,
`verification_state`, `world_digest`, `checkpoint_provenance`, `stop_condition`,
`next_action`, and `first_recovery_operation` set to `reobserve`. `next_action`
must be exactly `wait_for_release_then_complete`. Do not include a session ID or
transcript. Do not create `stage2.txt` before `.cairn-release-stage2` exists.

After the release file exists, use the action map to complete the action and its
verification, then stop.
