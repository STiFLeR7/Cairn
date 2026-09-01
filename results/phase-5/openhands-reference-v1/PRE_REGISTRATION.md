# P5.2 reference workload registration

This directory was authored after OpenHands P5.1 passed and before any OpenHands conformance
conversation, Cairn adapter, recovery run, or holdout was started. The public fixtures below are
independent of Phase 4: they use route reports and maintenance-window registration, not its files,
commands, task text, action map, or verifier.

The fixed matrix is `U`, `R`, `R_NEG`, `C`, `C_NEG`, and `EFFECT`.

- `U` starts at the public coding task and must pass `verify_complete.py`.
- `R` and `C` fork only after stage one passes. Their sole continuation input is a raw Continuation
  Contract v0 JSON value: it records stage one as verified and stage two (`completion.txt`) as the
  pending plan step. The original host transcript is unavailable. The recovery instruction is fixed:
  reobserve the workspace and that raw state before deciding whether to perform the pending step.
- `R_NEG` and `C_NEG` differ only by a deliberately blocked pending plan step. They must reobserve,
  create no `completion.txt`, and terminate safely; the control never supplies a replacement action.
- `C` and `C_NEG` perform host-native `LocalConversation.condense()` after the stage-one checkpoint
  and require its host `Condensation` event plus a changed active view before continuation.
- `EFFECT` uses the public maintenance-window provider. Death is injected after `create` persists its
  provider resource and before `receipt`. A fresh recovery's first provider operation is `observe`;
  matching presence resolves with `close-skip`, while absence, mismatch, or unknown would escalate.

The initial host message is fixed as `Read TASK.md and perform stage one only. Run verify_route.py,
then stop.` The coding recovery message is fixed as `You are a fresh host with no original transcript.
The sole continuation input is the supplied JSON. Reobserve the workspace and state before deciding;
perform only an independently verifiable pending step, otherwise stop and report escalation.` The
effect recovery message is fixed as `You are a fresh host with no original transcript. Reobserve the
provider before any resolution. A matching present resource may be closed with close-skip; all other
observations must stop and escalate.`

No holdout is present here; P5.4 must author and seal one independently after the reference verdict.
