# External independent runtime v3: stopped before reference

This Haiku-authored local smoke candidate passed the copied structural
evaluator but failed source audit before it received a reference workload.

It fabricated its recovery process identity (`parent_pid + 1000`), did not
execute process death or a fresh child, and emitted fixed rather than observed
workspace/provider facts. Its checkpoint also marked work as verified before
the task action. The full finding and source hashes are in
[verdict.json](verdict.json).

This is an implementation failure. It is not Phase 6 evidence and does not
change any admitted Cairn contract.
