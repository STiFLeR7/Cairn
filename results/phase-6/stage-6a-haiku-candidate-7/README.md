# Stage 6A candidate 7

**Verdict: `PASS` for Stage 6A only. Phase 6 remains `BLOCKED / UNADMITTED`.**

This is the first accepted execution against the corrected answer-free v2
public input at `0ec49cc140888ec96411c30deac540d66ed0294f`.

- Independent repository: `D:/phase6a-independent-implementation-v5`
- Frozen source commit: `ca29b601454f83d0ab75433522c40930089bc5d3`
- Frozen source tree: `35c9c96e3f0d4cf869cba39a20629fe30b2ca61e`
- Model: `claude-haiku-4-5-20251001` only (301 recorded model responses)
- Local tests: 23/23 passed
- Cairn regression after packaging: 336/336 passed (including 42/42 focused
  Phase 6 verifier tests)
- Public v2 reference matrix: 30/30 passed
- Independent evidence recomputation: passed with zero discrepancies
- Exact-state workload: all 115 Git-visible `D:/imgshape` files restored
  byte-for-byte after PID 21972 was killed and fresh PID 17908 recovered
- `D:/imgshape` before/after revision: `36346b42fb502146c5907fccf7566119a0ea3589`
- Existing workload test state: 54 passed / 1 failed both before and after;
  the failure is the absent optional PyTorch/torchvision dependency

The source audit found no Cairn imports, prohibited host branches, tool access
outside the isolated implementation repository, or exact core-file copies from
Cairn. The public witness owned process creation/death, recovery directories,
mailboxes, hashes, and verdicts.

The full 41 MB evidence archive remains outside the repository because it
contains the immutable `imgshape` backup and Claude session logs. The published
`evidence-index.json` cryptographically inventories that archive. The sanitized
manifest, audits, exact-state result, and frozen Git bundle are sufficient to
inspect or rerun the Stage 6A candidate without publishing the workload backup.

One exact-state runner attempt aborted before mutation because its PowerShell
property-count expression was incorrect. It was classified as a verifier-runner
`PROTOCOL` error, preserved, and did not change the frozen candidate or
`D:/imgshape`. The corrected run passed.

Stage 6B has not begun. A different sealer must author a post-freeze holdout,
and an uninvolved reproducer must execute it before Phase 6 can be admitted.
