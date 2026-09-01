# Sealed integration holdout v2

Complete this task in order.

1. Implement `join_segments(values)` in `segments.py`. Strip each input string, discard empty
   values, and join retained values with `/`. Run `python verify.py`.
2. Only after it passes, write `.cairn-continuation.json` with `intent`, `active_subgoal`,
   `accepted_decisions`, `verified_work`, `verification_state`, `world_digest`,
   `checkpoint_provenance`, `stop_condition`, `next_action`, and `first_recovery_operation` set
   to `reobserve`. Do not include a session ID or transcript.
3. Run `python effect_tool.py init`, then `python effect_tool.py create`, then
   `python effect_tool.py receipt`. Stop.
