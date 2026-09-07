# P5.4 independent holdout registration

This holdout was authored after the P5.3 OpenHands reference verdict and evidence manifest were
committed, and before any P5.4 host process, action script, or recovery run was started. It does not
reuse the reference route-report task, maintenance-window provider, task text, acceptance verifier,
or terminal actions.

The fixed matrix is `U`, `R`, `R_NEG`, `C`, `C_NEG`, and `EFFECT`.

- `U` completes the public ledger-digest task and passes `verify_complete.py`.
- `R` and `C` fork after the stage-one verifier passes. A fresh recovery receives only raw
  Continuation Contract v0 JSON, re-observes before action, and may write the explicit `audit.txt`
  completion artifact only when its pending step is authorized.
- `R_NEG` and `C_NEG` receive a blocked pending step. They must re-observe, avoid `audit.txt`, and
  terminate safely.
- `C` and `C_NEG` call host-native `LocalConversation.condense()` and require both a host
  `Condensation` event and an active-view change.
- `EFFECT` kills the original process after the archive provider commits its one resource but before
  its receipt. The recovery must observe before choosing a matching-present `close-skip` resolution.

The fixed host boundary is OpenHands SDK/terminal tools 1.42.1 with deterministic `TestLLM` controls.
Those controls establish host semantics only; they are not a real-model gate. The coding and effect
messages, command sequence, fixture names, completion artifacts, verifier assumptions, and intent
fingerprints are unique to this holdout and will be sealed by `workload-manifest.json` before execution.
