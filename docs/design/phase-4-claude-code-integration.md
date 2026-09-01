# Phase 4 — Claude Code Integration Proof

**Status:** admitted, narrowly. V5 establishes the reference/effect control and V6 closes its two
post-review gaps: a native-compaction causal negative and a separately sealed generic-RGR/native-
compaction holdout. The cumulative [V6 verdict](../../results/phase-4/reconstitution-v6/verdict.json)
is the admission evidence; neither control adds a Cairn runtime, adapter API, scheduler, planner, or
memory system.

## Boundary

Claude Code 2.1.250 retained control of its model, session, planner, native `Read`/`Write`/`Bash`
tools, and workspace execution. The reference requested `--model sonnet`, `--safe-mode`, and
`--setting-sources project`. Cairn's boundary was durable workspace evidence only:

- `.cairn-continuation.json` is the admitted Continuation Contract v0 projection.
- Effect intent, provider observation, receipt, resolution, and ledger are the admitted
  Receipt/Reconciliation Contract v0 evidence.
- `.cairn-action-map.json` is a **fixture-local task mapping**, not a Cairn contract or public API.
  It lets the host interpret `next_action` without the recovery prompt supplying a task command.

## Evidence

The V5/V6 verdicts derive solely from Claude Code stream records and copied workspace/provider snapshots.
V5's
[pre-run freeze](../../results/phase-4/reconstitution-v5/pre-run-freeze.json) pins the harness,
verifier, public workload, and sealed holdout before the first host invocation. The
[evidence manifest](../../results/phase-4/reconstitution-v5/evidence-manifest.json) hashes all
post-run raw evidence; V6 has its own [pre-run freeze](../../results/phase-4/reconstitution-v6/pre-run-freeze.json)
and [evidence manifest](../../results/phase-4/reconstitution-v6/evidence-manifest.json).

The reference proves:

1. An uninterrupted host creates a verified continuation and the harness forks that exact durable
   checkpoint into U/R/C branches before stage two.
2. In R, a host re-observes the checkpoint and is killed at a durable marker. A distinct fresh
   process uses `--no-session-persistence`, receives no original session or transcript, re-observes,
   completes only the action authorized by durable continuation/action state, and passes verification.
3. In C, Claude Code crosses a recorded manual `/compact` boundary: 36,662 pre-compaction tokens,
   3,782 post-compaction tokens, and 32,880 dropped tokens. The same host session resumes,
   re-observes, and completes the durable mapped action. This native-host path is not transcript-free.
4. U, R, and C have byte-equivalent coding and final-stage artifacts. V5's fresh-process negative changes
   only `next_action` to an unmapped value; the fresh host escalates and does not create the stage-two
   artifact. The recovery action is therefore state-authorized, not supplied by the recovery prompt.
5. V6 changes only `next_action` **after** a real native compact boundary in the same persisted host
   session. The resumed host escalates and does not create the stage-two artifact, so C cannot be
   credited merely for retaining its pre-compaction task transcript.
6. V6's independently authored coding workload uses a different task and action commands. Its U/R/C
   branches pass generic transcript-free fresh recovery, native host compaction, artifact equivalence,
   re-observation, and final verification.
7. At the Phase 3 ambiguity boundary, a distinct fresh host observes before acting, finds the one
   matching create-once resource, skips a duplicate create, writes a receipt from re-observation, and
   closes the ledger. The sealed holdout repeats the combined coding/effect recovery control.

## Scope limits and next gate

This does not establish exactly-once delivery, a general Claude Code adapter, a general action-map schema,
independent-provider validation, multi-host interoperability, or an ecosystem standard. The next evidence
gate is an independent host implementation consuming the admitted contracts through its own thin boundary.

V4 is excluded from admission because it supplied the post-restart action in its recovery prompt and
simulated, rather than observed, host compaction.
