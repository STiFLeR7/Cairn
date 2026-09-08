# External independent runtime v1 — stopped verdict

**Status: FAIL; not admitted.** This record preserves a genuine independent
implementation attempt without converting its public-reference success into an
interoperability claim.

The candidate repository `D:/phase6-independent-runtime-v1` at
`7b7ae26919992bae732776ff0132940513cf98ac` did not import Cairn runtime code.
It passed the copied evaluator's public-reference matrix (30/30), and a
controller replayed the sealed reference verifier against all 30 retained
snapshot/checkpoint/provider triples. Those are useful reference controls,
not Phase 6 admission evidence.

An uninvolved Haiku-only author then sealed holdout v2 at
`e64c1e1908d1f20cede6810107ebbff91fba3f50`. Its task, baseline manifest, and
verifier hashes are in [verdict.json](verdict.json). A separate Haiku-only
reproducer at `de6fcde0a2d97e197bf9c9363e9b175a3456b1db` inspected only the
frozen candidate, copied kit, sealed holdout, and source mirror.

The reproducer found no documented way to pass a sealed workload into the
candidate. `run_conformance.py` hard-codes
`D:/phase6-public-reference-v1` for its manifest and verifier. Running the
holdout would therefore have required prohibited source edits, path
substitution, or a post-seal adapter. No such workaround was used and no
holdout matrix was claimed.

The causal classification is **independent implementation boundary defect**:
this candidate is a fixed public-workload runner, not a consumer of a sealed
workload. The result does **not** alter Recovery Contract, Continuation
Contract v0, or Receipt/Reconciliation Contract v0, and does not by itself
establish a kit/evaluator defect. It leaves Phase 6 `KIT_READY, not admitted`.

`D:/imgshape` remained clean at
`36346b42fb502146c5907fccf7566119a0ea3589`; raw external evidence and their
SHA-256 provenance are retained in [verdict.json](verdict.json).
