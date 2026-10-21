# Cairn v1.0.0 — release notes

Released 2026-10-21 (owner approval: AP-0036). Cairn is a framework-agnostic reference implementation and
benchmark for recoverable long-horizon AI agents, built around the thesis **"Checkpoints Are Compactions."**
v1.0.0 follows the pre-registered live recovery gate (M5), which returned **GO**.

## Highlights

- **BYOM recovery library (M4):** the Re-grounding Recovery (RGR) protocol as public functions over `World`,
  `CheckpointStore` and `EffectLedger` seams, plus an opt-in `Agent` loop and reference implementations. You
  bring your own agent loop, model and keys.
- **P1–P6 proof ladder:** P1 crash/restart; P2 compaction continuity (Continuation Contract v0); P3 external
  effects (Receipt/Reconciliation Contract v0); P4 Claude Code host integration; P5 two-host portability
  (Claude Code and OpenHands SDK 1.42.1); **P6 independent conformance, admitted 2026-10-19** (Haiku-only
  clean-room candidate 10: Stage 6A 30/30, sealed holdout 30/30, uninvolved reproducer 30/30).
- **M5 v1.0 gate: GO** (pre-registered before any live call; commit `e1b4280`;
  [`gate-verdict.json`](../../results/m5/gate-verdict.json): "C1 (capability-matched) and C3 supported on both
  models"). Per model, Claude `claude-sonnet-5-5` and Codex `gpt-6-sol` returned identical numbers:
  - calibration 10/10; 32/32 planned cells fired (B0 16, B3 16), 0 skipped, 0 lost; 520 calls, 0 errors;
  - C1 (capability-matched): B3 success 1.00 vs B0 1.00; recovery tax B3 mean 4.50 ± 0.50 (max 5.00) vs B0
    8.00 ± 0.00 (min 8.00); no-regression B3 0.42 vs B0 0.00;
  - C3: 0 duplicate effects with B3 vs 16 with B0.

## Scope and limitations

Honest scope of the M5 result (claims registry, 2026-10-21):

1. Both models were fully competent on the task, so the capability-matched rule was never stressed.
2. The chain task's oracle advances one step per call, so recovery cost in work units is determined by task
   structure for a competent model. The evidence shows RGR's recovery mechanism cuts recovery tax (5 vs 8 work
   units at most/least) and preserves pre-crash work with near-zero variance; it is not a broad
   live-performance or model-robustness claim.
3. C3's torn effect is injected by the harness at the crash step, so C3-live is "effect safety under live
   control flow", not model-dependent evidence.
4. C2, C4 and C5 remain reference-harness only.
5. One task (chain n=6), crash steps 2 and 3, 8 repeats, two models.
6. Not an ecosystem standard; not exactly-once delivery.

P-ladder boundaries (README "Project status"):

- No exactly-once delivery of external effects; P3 admits only the decision semantics proven for its reference
  effect (absent → retry; matching present → skip; unknown, mismatch, never-retry → escalate).
- Not an ecosystem standard and not universal compatibility; P4 admits one host integration, P5 deterministic
  two-host portability, P6 one passing external chain.
- P2 requires a fresh process and a clean, verified checkpoint; neither v0 contract establishes broad
  live-model performance or a framework API.
- C2, C4 and C5 are reference-harness evidence only.

## Reproduce

- M5 evidence: [`results/m5/`](../../results/m5/) (`preregistration.json`, `protocol.json`, `claude.json`,
  `codex.json`, `gate-verdict.json`); design: the
  [M5 spec](../superpowers/specs/2026-10-19-m5-v1-gate-design.md); re-run with `python benchmarks/m5_study.py`
  (needs the `claude` and `codex` CLIs). The pre-registration pins code at `168a6e6`; verify the evidence at
  commit `e1b4280`.
- Reference harness: `python -m pytest -q`; see [`REPRODUCE.md`](../../REPRODUCE.md).

## Install / cite

- Apache-2.0. Python 3.12+, no third-party runtime dependencies.
- Cite via [`CITATION.cff`](../../CITATION.cff) (version 1.0.0, released 2026-10-21).
