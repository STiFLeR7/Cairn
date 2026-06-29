---
title: Research Claims Registry
status: active
last_updated: 2026-06-29
owner: maintainers
related_aps: [AP-0011, AP-0040, AP-0041, AP-0043, AP-0044, AP-0045, AP-0046]
related_adrs: [ADR-0001, ADR-0009]
---

# Research Claims Registry

The falsifiable claims Cairn commits to defending. Registering claims *before* building keeps the work
honest: every later phase either supports, refines, or refutes a registered claim, and negative results
are recorded rather than buried.

## Claim schema

Each claim has:

- **ID** — `C<n>`, monotonic, never reused.
- **Statement** — a single falsifiable proposition.
- **Rationale** — why we expect it to hold.
- **Evaluated by** — the fidelity axis/axes ([recovery-fidelity.md](../concepts/recovery-fidelity.md)),
  baseline comparison, and the Phase 5 AP that tests it.
- **Status** — `registered` → `supported` | `refined` | `refuted` (set by evidence, with a dated note).

## Freeze policy

A claim is **immutable once registered**. Evidence updates only its **Status** (with a dated log line). To
change a claim's *statement*, register a **new** claim that supersedes the old one and mark the old one
`refined` (or `refuted`) — never edit a registered statement in place. This mirrors the ADR practice.

## Registered claims

### C1 — Re-grounding beats cold restart
- **Statement:** After a failure at step `k`, Re-grounding Recovery (RGR, B3) achieves higher recovery
  fidelity than cold restart (B0) on the same task and failure.
- **Rationale:** RGR preserves completed work, intent, and ruled-out dead-ends; cold restart discards all
  of it.
- **Evaluated by:** task success, solution quality, no-regression, recovery tax; B3 vs B0; `AP-0029`/`AP-0030`.
- **Status:** supported *(reference harness, 2026-06-15)*; **strongly suggestive but not strictly confirmed
  live** *(powered live-LLM study M3, 2026-06-29 — 28 fired cells on `gpt-oss-120b`: RGR roughly **halves**
  recovery tax with no overlap and regresses less, but the strict every-repeat verdict is NOT SHOWN because
  real free models fail the task itself unpredictably; a paid/reliable tier is still needed)* — see status log.

### C2 — Unified distillation does not degrade checkpoint fidelity
- **Statement:** A Continuation State produced by the **unified** distillation mechanism (durable core +
  elastic tail, shared with compaction) yields recovery fidelity no worse than a checkpoint-only baseline
  that distills solely for recovery.
- **Rationale:** the durable core is exactly the state both compaction and checkpointing require; the
  elastic tail is frozen at checkpoint time, so unification should not cost fidelity. This is the testable
  heart of *Checkpoints Are Compactions*.
- **Evaluated by:** all five axes; unified vs checkpoint-only ablation; `AP-0031`.
- **Status:** evidenced *(reference harness, 2026-06-15)* — see status log.

### C3 — Effect-safety WAL eliminates duplicate effects
- **Statement:** With the write-ahead effect ledger, resume produces **zero** duplicated irreversible
  effects for `check-before-retry` tools.
- **Rationale:** `INTENT`-without-`COMPLETE` detection + idempotency-key/query gating closes the danger
  window for queryable effects.
- **Evaluated by:** effect-safety axis (hard gate); with-WAL vs without-WAL; `AP-0026`/`AP-0030`.
- **Scope note:** does **not** claim coverage of `never-retry` tools (acknowledged limit — see
  [tool-effect-taxonomy.md](../concepts/tool-effect-taxonomy.md)).
- **Status:** supported *(reference harness, 2026-06-15)* — see status log.

### C4 — Re-grounding is robust to cross-version resume
- **Statement:** RGR retains recovery fidelity when the model/version that resumes differs from the one
  that checkpointed, in cases where log-replay (B1) fails.
- **Rationale:** re-grounding re-derives from intent and observed world rather than reproducing tokens, so
  it does not depend on the original model's exact behavior.
- **Evaluated by:** task success, solution quality; checkpoint-on-A / resume-on-B; `AP-0032`.
- **Status:** partially evidenced *(mechanism only, 2026-06-15)* — see status log.

### C5 — A minimal sufficient Continuation State is empirically identifiable
- **Statement:** Ablating components of the Continuation State reveals a minimal subset below which
  fidelity sharply degrades — i.e. continuation sufficiency is measurable, not merely asserted.
- **Rationale:** fidelity provides the constraint; ablation provides the search over `S`.
- **Evaluated by:** all axes under component ablation; `AP-0031`.
- **Status:** supported *(reference harness, 2026-06-15)* — see status log.

## Status log

- 2026-06-15 — C1–C5 registered (Phase 1, `AP-0011`).
- 2026-06-15 — Phase 5 evidence (deterministic **reference harness** with a scripted mock model; **not** a
  live-LLM study — see [ADR-0009](../adr/ADR-0009-evaluation-framework.md)):
  - **C1 → supported.** Over failures at k=1..4 (`benchmarks/recovery_matrix.py`), RGR (B3) imposed lower
    recovery tax than cold restart (B0) (mean 1.5 vs 5.0 steps) and preserved all pre-failure work
    (no-regression 1.0 vs 0.0). Test: `tests/test_eval_matrix.py`.
  - **C3 → supported.** On a torn `check-before-retry` effect, B3 produced **0** duplicate effects (gate
    PASS) while B0 (no WAL) produced **1** (gate FAIL). Test: `tests/test_eval_effect_safety.py`. Scope
    limit unchanged: `never-retry` tools are escalated, not covered.
  - **C5 → supported.** Ablation (`benchmarks/ablation_study.py`) shows dropping `plan` collapses fidelity
    (tax 2→5, no-regression 1.0→0.0) while dropping `decisions`/`ruled_out`/`world_digest`/`verification`
    does not — a minimal sufficient state is empirically identifiable *in this harness*. The located cliff
    is harness-specific (a deterministic mock under-exercises decisions/dead-ends a real model would use).
  - **C2 → evidenced (not yet strongly).** The unified `distill` produces an identical durable core for the
    compaction and checkpoint paths (`tests/test_distill.py`) and the full cairn recovers at full fidelity;
    no checkpoint-only degradation was observed. A dedicated unified-vs-checkpoint-only contrast under a
    real model remains future work.
  - **C4 → partially evidenced (mechanism only).** Cross-version resume (checkpoint under A, resume under B)
    completes and `provenance` records both versions (`tests/test_eval_cross_version.py`). The
    distinguishing claim — that RGR holds where log-replay *fails* under non-determinism — cannot be forced
    with a deterministic mock and is deferred to the live-LLM study.
- 2026-06-15 — **Open scope:** all Phase 5 evidence is from the deterministic reference harness. A live-LLM
  empirical study with statistical testing (and faithfully-realized non-crash failure types) is future
  work; negative/insufficient results will be recorded here rather than buried.
- 2026-06-16 — **First live-LLM run (Milestone M1, AP-0040/0041)** — via OpenRouter `openrouter/owl-alpha`
  (a free model) through the live pipeline (`cairn.model_live` + `cairn.live_controls`). Recorded honestly:
  - **Pipeline validated.** A real model drove the harness end-to-end; every prompt/reply was captured to a
    replayable transcript (`benchmarks/transcripts/openrouter_owl-alpha-recovery-study.jsonl`). The live path
    (provider → parse → harness → matrix → metrics) works.
  - **C1 NOT validated live — evidence invalid/insufficient (not supporting).** The Phase-5 multi-file task
    and its recovery metrics assume the scripted mock's **one-action-per-step** cadence. The live model
    **batched all files into a single action** and finished *before* the injected crash (k=2) could fire, so
    the scenario never exercised recovery; across two repetitions the per-baseline `task_success`/`recovery_tax`
    flipped (genuine non-determinism). A naive C1 check in the runner spuriously printed "SUPPORTED" on a run
    where B3 had `task_success=0` — corrected to require B3 success.
  - **Consequence — C1–C5 remain reference-harness-only.** Validating them live requires: (a) a task that
    forces **non-batchable sequential** steps so a crash genuinely interrupts partial work; (b) metrics robust
    to a real model's action granularity; (c) repetitions with seeds + statistics. This is the M1 outcome and
    the input to the next iteration; **v1.0 stays held** (AP-0042 → NO-GO).
  - **Incidental finding (fixed):** real models don't reliably emit markdown fences — `owl-alpha` mixed
    fenced, XML tool-call, and bare-code replies across steps. `parse_action` was generalized (tool-call
    extraction + a `compile()`-gated bare-code path) so the harness stays drivable; this is general, not
    model-specific.
- 2026-06-16 — **Root-cause correction (systematic-debugging pass).** The "unstable/ill-defined metrics"
  above were a *symptom*; the actual defect is a **benchmark-integrity bug**: `run_until_failure` never
  verified that the injected crash fired. When a model finishes a **batchable** task before step `k`, the
  crash never triggers, yet `run_matrix` scored the resulting *non-failure* as a valid recovery — a
  deterministic probe showed it reporting a **perfect** `task_success=True, recovery_tax=0` for a recovery
  that never happened (a **false-positive** risk, worse than noise). **Fixed at source** (test-first,
  `tests/test_eval_injection.py`): `run_until_failure` now returns an `Injection(fired, completed)`, and
  `run_matrix` **skips and reports** cells where the injection did not fire instead of scoring them. Re-run
  live, the study now correctly reports *"k=2 cells skipped — the model finished before the crash; recovery
  not exercised; C1 not evaluable on this task."* This **sharpens** the C1-not-validated-live verdict (the
  task is batchable, so the bench can't exercise recovery against a capable model) and is the concrete M2
  requirement: a **non-batchable sequential** task.
- 2026-06-23 — **Milestone M2 live-LLM run on the non-batchable task (AP-0043…AP-0046)** — model
  `nvidia/nemotron-3-super-120b-a12b:free` via OpenRouter, through the same live pipeline. This is the run
  M1 could not produce. Recorded honestly (manifest:
  `benchmarks/transcripts/nvidia_nemotron-3-super-120b-a12b_free-chain-study.manifest.json`):
  - **The injected crash actually fired (the M1 blocker is resolved).** On the non-batchable chain task
    (`cairn.eval.chain`, AP-0043), **fired cells = 4, skipped = 0** — the model could not one-shot the task,
    so the crash at `k=2` genuinely interrupted partial progress and recovery was exercised against a real
    model for the first time. The model drove the chain correctly (clean per-step `oracle.advance(...)`).
  - **C1 → suggestive, NOT confirmed live (n=2 repeats, work-unit metrics AP-0044, stats AP-0045).**
    **B3 (RGR):** task_success **1.00** (2/2), recovery_tax **1.0 ± 0.0**, no_regression 0.83 ± 0.17,
    solution_quality 1.0, 0 effect duplicates. **B0 (cold restart):** task_success **0.50** (1/2 — one
    cold restart the model failed to redo the task), recovery_tax 2.5 ± 2.5, no_regression 0.50 ± 0.50.
    RGR dominates cold restart on **every axis mean** and is far more **reliable** (a plausible mechanism:
    RGR's shorter recovery path gives a flaky model fewer steps to fail). But the **strict, no-overlap
    verdict is NOT SHOWN**: B0's failed repeat has recovery_tax 0 (a *non-recovery*, not a cheap recovery),
    which overlaps B3, and **n=2 is underpowered**. A naive "B3 mean < B0 mean" read would call this
    supported — we deliberately do not, per the consistency rule (`verdict_c1`).
  - **Honest limits (ADR-0009).** (a) **Underpowered:** n=2, a single crash point, one model. A larger run
    (more repeats, both crash points) **could not be completed** — the OpenRouter free tier returned a
    persistent **HTTP 429** after the first study. (b) **Transcript not persisted:** the raw prompt/reply
    transcript was lost to a record-truncation footgun when the rate-limited larger run wrapped a fresh
    recorder over it (footgun **fixed**: live runs now record to a `.partial` and finalize on success only);
    the **manifest** (aggregate stats + verdict) survived and is the citable artifact. (c) `nemotron-3-ultra-550b`
    was unusable (gateway 504); `owl-alpha` works but is format-unreliable.
  - **Net.** A real **step-forward over M1**: the benchmark is now recovery-faithful and produces real,
    statistically-summarized **live** evidence that *leans* in favor of C1 — but it is **not** a powered
    confirmation. C1 stays **supported (reference harness) + suggestive (live)**; **C2/C4/C5 remain
    reference-harness-only** and C3 (effect-safety) was not wired into this chain run. **v1.0 stays held**
    pending a powered live run; this is the input to the AP-0047 go/no-go.
- 2026-06-29 — **Milestone M3 powered live study (AP-0048…AP-0050)** — the chain study run with up to **8
  repetitions** and **both crash points** across four free-tier models on three providers (OpenRouter / Groq
  / ZenMux), with the success-conditioned tax (AP-0048) and per-repeat resilience. Manifests committed under
  `benchmarks/transcripts/*-chain-study.manifest.json`. The headline result is the first genuinely **powered**
  cell count:
  - **`openai/gpt-oss-120b` (Groq, 8 repeats): 28 fired cells, 0 errored.** **B3 (RGR):** success **0.73**,
    recovery_tax **3.64 ± 0.77** (min 2.0 / **max 5.0**), no_regression **0.44**. **B0 (cold restart):**
    success **0.46**, recovery_tax **6.33 ± 0.47** (**min 6.0** / max 7.0), no_regression **0.23**. RGR
    **roughly halves recovery tax with no overlap** (B3 max 5.0 < B0 min 6.0, success-conditioned), and has a
    **higher success rate** and **less regression** — directionally strong support for C1 on a powered run.
  - **`nvidia/nemotron-3-super-120b-a12b:free` (OpenRouter, 3 repeats): 4 fired, 2 repeats lost to HTTP 429.**
    **B3:** success 0.50, tax **3.0 ± 0.0**; **B0:** success 1.00, tax **6.5 ± 0.5**. Same tax pattern (RGR
    ≈ half), tiny n.
  - **`llama-3.3-70b-versatile` (Groq) and `openai/gpt-4o-mini` (ZenMux): 0 fired** — fully rate-limited
    (Groq daily quota exhausted) / payment-required (ZenMux 402). Recorded as honest negatives, not buried;
    the per-repeat resilience (AP-0050) turned these from study-aborting crashes into clean `errored`/`NOT
    SHOWN` manifests.
  - **Strict verdict: NOT SHOWN on every model.** Cause is **not** an RGR failure — it is that real free
    models fail the *task itself* unpredictably (`gpt-oss` ~27%, `nemotron` 50% at n=2), so B3 never succeeds
    in **every** repetition (`verdict_c1` requires `success.min == 1.0`). This exposes a **methodology gap**:
    the strict every-repeat gate conflates *model competence* (does the model complete the task at all) with
    *recovery quality* (given the model acts, does RGR recover cheaper). By a capability-matched read
    (success-rate delta + success-conditioned tax), `gpt-oss-120b` **supports C1**; the strict gate does not.
    We **do not** loosen the gate to manufacture a GO (ADR-0009) — instead this is the explicit input to the
    AP-0051 go/no-go and the next milestone's verdict design.
  - **Honest limits.** Free/credit-less tiers cannot sustain a powered run (2 of 4 models fully blocked;
    Nemotron lost 2/3 repeats to 429). A **paid / higher-rate-limit, instruction-reliable model** is required
    to remove the rate-limit and model-competence confounds. C3/C2/C4/C5 still not wired live. **v1.0 stays
    held** — strongest live signal yet, still not a clean confirmation. Input to AP-0051 (go/no-go take 3).
