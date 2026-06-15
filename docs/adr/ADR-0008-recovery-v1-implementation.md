---
title: ADR-0008 — Recovery v1 implementation decisions
status: frozen
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0023, AP-0024, AP-0025, AP-0026, AP-0027]
related_adrs: [ADR-0004, ADR-0005, ADR-0006]
---

# ADR-0008 — Recovery v1 implementation decisions

- **Status:** Accepted
- **Date:** 2026-06-15

## Context

Phase 4 turns the Phase 3 substrate into a recoverable agent by *implementing* the already-accepted
recovery designs: re-grounding resume (ADR-0004), unified distillation (ADR-0005), and effect-safety
(ADR-0006). Implementation forces several concrete choices the design docs intentionally left open. This
ADR records them so they are visible and stable; it changes none of the prior decisions.

## Decision

1. **Snapshot ids continue-from-highest (durability fix).** `WorkspaceManager` numbers snapshots by
   scanning existing `snap_N` directories and continuing from the highest — mirroring `CheckpointStore`.
   A freshly-constructed runtime (the resume case) therefore never re-mints `snap_0` and overwrites a
   snapshot an existing checkpoint references. This is required for boundary-contract invariant **I4**
   (mutual consistency) to hold across a process restart, not just within one process.

2. **World digest is the torn-write detector.** `distill` records `world.digest` = `{relpath: sha256}` of
   the workspace at checkpoint time. On resume, `reconcile` recomputes the digest of the restored
   workspace and flags mismatches as torn/divergent writes. Hashing (not byte-diffing) keeps the cairn
   small and the check `O(files)`.

3. **`distill(mode=...)` selects the tail policy, not the core.** One function builds the durable core
   identically for both write paths; `mode="compact"` prunes the elastic tail and `mode="checkpoint"`
   freezes the last *N* steps verbatim. The deterministic, rule-based salience policy (failed step →
   `ruled_out` decision; plan derived from executed steps) stands in for LLM summarization in v1.

4. **Resume is `load → re-observe → reconcile → re-plan → continue`, driven by `CodeHarness.resume`.**
   `observe_world` and `reconcile` are pure functions over `(state, runtime)`; `resume` re-uses the same
   continue-loop as `run` after re-grounding. Re-planning is delegated to the injected `ModelProvider` —
   a *different valid path* is acceptable (outcome equivalence, not replay).

5. **Effects are injected callables in v1.** An `EffectfulTool` carries a tool class and an optional
   `verify` hook; `perform_effect` does write-ahead INTENT → run → COMPLETE; `resolve_danger_window`
   applies the per-class policy (redo / verify-then-redo-or-skip / escalate). Using injected `run`/`verify`
   callables keeps effects deterministic and testable while honoring the no-hardcoded-harness rule —
   no real network/email client is assumed.

6. **Failure injection is a generic lifecycle hook.** The agent loop exposes an optional
   `step_hook(step)` callback; tests/utilities wire it to raise `InjectedFailure` after step *k*. No
   test-specific "crash" flag is baked into the harness; the hook is a legitimate, general lifecycle seam.

## Consequences

- Resume works across a real process restart (fresh runtime over the same `base_dir`), which the Phase 5
  failure-injection harness depends on.
- Recovery quality is a by-product of the same `distill` exercised during compaction (ADR-0005 / claim C2),
  and effect-safety is enforced exactly at the danger window (ADR-0006 / claim C3).
- The deterministic v1 salience and injected-callable effects trade realism for testability; richer
  summarization and real tool adapters are deferred to later phases, behind the same seams.

## Supersedes / superseded by

None. Records implementation decisions under ADR-0004/0005/0006; supersedes nothing.
