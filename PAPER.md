# Checkpoints Are Compactions: Re-grounding Recovery for Long-Horizon Agents

*Cairn — a framework-agnostic reference implementation and benchmark for recoverable long-horizon AI
agents. Draft (v1), 2026-06-15; §9 live-run history and availability maintained through Milestone M4
(2026-07-02). This is the Markdown working draft (AP-0034); a typeset version is later work.*

> **Honest-scope notice.** All empirical results in this draft come from a **deterministic reference
> harness with a scripted mock model** (see [ADR-0009](docs/adr/ADR-0009-evaluation-framework.md)). They
> establish that the *mechanisms* behave as designed and are reproducible; they are **not** a live-LLM
> study. Where a claim needs non-determinism or a real model to be fully tested, we say so and mark it
> future work rather than overclaim.

---

## Abstract

When an autonomous agent fails partway through a long task, today it usually starts over. We argue this is
unnecessary, and that the machinery to avoid it already exists inside every long-horizon agent — in its
**context compaction**. Our thesis, **"Checkpoints Are Compactions,"** is that crash-recovery
checkpointing and online context compaction are the *same operation*: both distill an unbounded history
into a compact state sufficient to keep going. We make recovery a first-class, *measurable* property via
three pillars: a typed, durable **Continuation State** (a "cairn") that doubles as working memory and
recovery checkpoint; **Re-grounding Recovery (RGR)**, which restores situational awareness from the cairn
and the re-observed world rather than replaying a non-deterministic trajectory; and an **effect-safety
write-ahead ledger** that prevents a resumed agent from re-firing irreversible actions. We define
**recovery fidelity** as outcome equivalence to the uninterrupted run across five axes and build a
failure-injection benchmark against four baselines. In the reference harness, RGR beats cold restart on
recovery tax and no-regression, the write-ahead ledger eliminates duplicate effects for queryable tools,
and an ablation identifies the minimal sufficient state. We position this as a reference implementation
and benchmark that complements agent frameworks rather than replacing them.

## 1. Introduction

Long-horizon agents — those that plan, act, observe, and iterate over many steps — fail. Processes crash,
contexts overflow, tools time out. The dominant recovery strategy is **cold restart**: discard everything
and begin again. This wastes completed work, re-incurs cost, and — worse — can **re-execute irreversible
side effects** (re-send an email, re-open a pull request, re-charge a card).

Classical systems recover by restoring exact state and deterministically replaying. Agents cannot:
their execution is **non-deterministic** (Assumption-2 in
[problem-formalization.md](docs/concepts/problem-formalization.md)), so a faithful replay is neither
possible nor the right target. A correctly resumed agent will generally take a *different* path to an
equivalent outcome.

The key observation is that long-horizon agents *already* recover from information loss continuously:
every time they compact an overflowing context window, they distill what matters and drop the rest. A
crash-recovery checkpoint is just a compaction you can roll back to. If one mechanism serves both, then
recovery quality becomes a by-product of normal operation — continuously exercised and tuned — rather than
a separate, rarely-used code path. That is the thesis: **Checkpoints Are Compactions.**

**Contributions.**
1. A two-layer model (Code Harness / Runtime) that makes the recovery interface explicit (§3).
2. The **Continuation State** ("cairn"): a typed durable core (a sufficient statistic) plus a prunable
   elastic tail (§4).
3. **Re-grounding Recovery (RGR)**: load → re-observe → reconcile → re-plan → continue (§5).
4. An **effect-safety** write-ahead protocol that eliminates duplicate effects for queryable tools (§6).
5. **Unified distillation**: one mechanism for compaction and checkpointing (§7).
6. **Recovery fidelity** (five axes) and a **failure-injection benchmark** with four baselines, plus
   results, an ablation, and a cross-version experiment, all honestly scoped (§8–§9).

## 2. Related work and positioning

Cairn sits between three bodies of work — classical checkpoint/restart, agent frameworks, and context
management — and belongs to none of them exclusively (see
[related-work.md](docs/research/related-work.md)). Classical checkpoint/restart assumes determinism and
restores exact state; agents violate that assumption. Agent frameworks (e.g. orchestration libraries and
harnesses) provide execution and memory but treat recovery as ad-hoc. Context-management work studies
compaction for *staying within a window*, not for *crash recovery*. Cairn's novelty is to **unify**
compaction and checkpointing and to make recovery a measurable property.

> **Cairn is** a specification (Continuation State + boundary contract), a minimal reference
> implementation, and a failure-injection benchmark. **Cairn is not** a production agent framework, a
> model, or a general workflow orchestrator. It **complements** existing frameworks.

## 3. The two-layer model

We separate concerns by **altitude**, not by feature. A **Code Harness** *decides* (reasoning, planning,
code-as-action); a **Runtime** *sustains* (workspace, durable storage, execution, the recovery
mechanism). The rule is *one concern, two altitudes*: shared concerns are split by scope, with the Code
Harness logically above and physically inside the Runtime
([code-harness-and-runtime.md](docs/concepts/code-harness-and-runtime.md)).

Recovery forces the interface between them to become explicit. The **boundary contract**
([boundary-contract.md](docs/design/boundary-contract.md)) is a small operation set:

- **Runtime (mechanism, faithful):** `snapshot_workspace`, `checkpoint`, `load_latest`,
  `restore_workspace`, `append_effect`/`complete_effect`, `list_effects_since`.
- **Code Harness (semantics, lossy):** `distill`, `reconcile`.

Five invariants make it sound: **I1** write-ahead effects, **I2** atomic checkpoints, **I3** monotonic
effect offsets, **I4** mutual consistency (a checkpoint references a real, restorable snapshot and a valid
offset), **I5** latest-before-failure.

## 4. The Continuation State (the cairn)

The cairn is a typed object with two parts
([continuation-state-schema.md](docs/design/continuation-state-schema.md)):

- **Durable core** — the *sufficient statistic* `S`, never pruned: intent (root goal + active subgoal),
  plan with per-step status, decisions including **ruled-out dead-ends**, an effects pointer (ledger
  offset), a world reference (snapshot id + a per-file content **digest**), verification state, and
  provenance (model/harness versions).
- **Elastic tail** — recent raw detail, prunable.

The durable core is exactly what an agent needs to *keep going* and what a checkpoint needs to
*reconstruct*. That identity is the crux of the thesis. A five-layer state taxonomy
([state-taxonomy.md](docs/concepts/state-taxonomy.md)) classifies what is durable-external, irreversible,
working memory (the crux), plan-intent, and ephemeral runtime handles.

## 5. Re-grounding Recovery (RGR)

RGR resumes in five steps ([resume-protocol.md](docs/design/resume-protocol.md)):

1. **Load** *(Runtime)* — `load_latest()` returns the most recent fully-durable checkpoint (I5); restore
   the workspace to its snapshot; fetch effects since the checkpoint offset.
2. **Re-observe** *(Code Harness)* — read the *actual* world (workspace + effect ledger) before acting.
   "Re-observe before re-act" is what separates re-grounding from "restore bytes and charge ahead."
3. **Reconcile** — compare the cairn against reality: the effect **danger window**
   (`INTENT`-without-`COMPLETE`) and plan status.
4. **Re-plan** — from intent + reconciled plan + decisions (including dead-ends, so failed paths are not
   re-explored), choose the next action. A *different but valid* path is acceptable.
5. **Continue** — resume normal operation; checkpoint again at the next step boundary.

The bar is **outcome equivalence**, not trajectory equivalence — which is why RGR survives
non-determinism where replay does not, and why it can resume under a *different model version* (§8, C4):
provenance records both versions, and re-grounding re-derives from intent and the observed world rather
than reproducing tokens.

**Implementation note (restore-first), honestly recorded.** The reference harness restores the workspace
*before* reconciling (step 1 before step 3). Consequently the restored world matches the cairn's digest by
construction, and the torn-write/plan-drift branch of `reconcile` is a **no-op in this flow** — a
post-checkpoint divergence is simply discarded by the restore and the affected step is redone from the
clean checkpoint (still outcome-equivalent). The detection logic is implemented and unit-tested but its
active role is reserved for a future restore-less *crash-in-place* mode; in v1 reconcile's load-bearing
jobs are effect danger-window resolution and plan re-grounding (see
[ADR-0008 §7](docs/adr/ADR-0008-recovery-v1-implementation.md)). We record this rather than paper over it.

## 6. Effect-safety

Irreversible effects (taxonomy layer 2) use a **write-ahead ledger**
([effect-safety-protocol.md](docs/design/effect-safety-protocol.md)): `INTENT` is made durable *before*
the effect runs (I1); `COMPLETE` follows success. A crash can therefore never leave an executed effect
unrecorded; the only ambiguity is the recoverable one — an `INTENT` with no `COMPLETE`. On resume, that
set is the **danger window**, resolved per the tool's class
([tool-effect-taxonomy.md](docs/concepts/tool-effect-taxonomy.md)):

| Tool class | Resume policy |
|---|---|
| `safe-to-retry` | **Redo** — idempotent/pure. |
| `check-before-retry` | **Verify, then redo-or-skip** — query the world / idempotency key; if it already happened, skip and write COMPLETE; else redo. |
| `never-retry` | **Escalate** — do not auto-retry; the effect may or may not have happened and repeating it is harmful. |

For `check-before-retry` tools an authoritative check resolves every danger-window key before any
re-execution, so **no duplicate effect is produced**. The honest scope limit (C3): `never-retry` tools
(non-idempotent *and* unqueryable) cannot be made safe automatically and are escalated, not covered.

## 7. Unified distillation

A single Code-Harness operation, `distill(trajectory, mode)`, produces the cairn for both write paths
([unified-distillation.md](docs/design/unified-distillation.md)). The **durable core is computed
identically** regardless of path; only the tail differs: **compaction prunes** it (the live agent can
re-derive detail), a **checkpoint freezes** it (best-effort context for a cold resume). So a persisted
checkpoint is `durable core + frozen tail`; an online compaction is `durable core + pruned tail`. Same
distillation, fidelity-appropriate per path. Because everyday operation compacts constantly, the exact
distillation recovery depends on is continuously exercised — an agent that compacts well recovers well, by
construction.

## 8. Evaluation

### 8.1 Recovery fidelity

We define **recovery fidelity** as outcome equivalence to the *uninterrupted run* across five axes
([recovery-fidelity.md](docs/concepts/recovery-fidelity.md)): **task success**, **solution quality**,
**no-regression** (was pre-failure work preserved, not redone), **effect-safety** (duplicate/spurious
effects — a *hard gate*, never averaged into a scalar), and **recovery tax** (cost to return to
productive work). We compare against four baselines: **B0** cold restart, **B1** full-log replay, **B2**
snapshot-only (restore bytes, no semantic re-grounding), **B3** RGR.

### 8.2 Method

A failure-injection harness runs a multi-step task, injects a failure at step `k`, and recovers it through
each baseline, scoring every axis against the uninterrupted reference run. The model is a deterministic
scripted mock so results are reproducible (ADR-0009). Concrete tasks live in `benchmarks/`; the framework
(`cairn.eval`) hardcodes none of them.

### 8.3 Results (reference harness)

Multi-file task (n=5), failures at k=1..4:

| baseline | task_success | solution_quality | no_regression | recovery_tax |
|---|---|---|---|---|
| B0 cold restart | 1.00 | 1.00 | 0.00 | 5.00 |
| B3 RGR | 1.00 | 1.00 | 1.00 | 1.50 |

Effectful task, torn `check-before-retry` effect at k=2:

| baseline | effect_duplicates | gate |
|---|---|---|
| B0 (no WAL) | 1 | FAIL |
| B3 (WAL) | 0 | PASS |

- **C1 (RGR > cold restart): supported.** B3 imposes less recovery tax (1.5 vs 5.0 steps) and preserves
  all pre-failure work (no-regression 1.0 vs 0.0).
- **C3 (WAL eliminates duplicate effects): supported.** B3 produces 0 duplicates (gate PASS) vs 1 for B0
  (gate FAIL). Scope limit unchanged: `never-retry` is escalated, not covered.
- **C5 (a minimal sufficient state is identifiable): supported.** Ablating `plan` collapses fidelity
  (tax 2→5, no-regression 1.0→0.0); ablating `decisions`/`ruled_out`/`world_digest`/`verification` does
  not — locating a fidelity cliff *in this harness*.
- **C2 (unified distillation does not degrade fidelity): evidenced (not yet strongly).** The durable core
  is identical across compaction/checkpoint paths and full-cairn recovery is at full fidelity; a dedicated
  unified-vs-checkpoint-only contrast under a real model is future work.
- **C4 (robust to cross-version resume): partially evidenced (mechanism only).** Checkpoint-under-A /
  resume-under-B completes and provenance records both; the distinguishing claim — that RGR holds where
  replay *fails* under non-determinism — cannot be forced with a deterministic mock and is future work.

## 9. Limitations and future work

- **Deterministic reference harness, not a live-LLM study.** The headline numbers establish mechanism
  correctness and reproducibility, not real-model behavior. A live-LLM empirical study with statistical
  testing is the primary future work.
- **First live run (recorded honestly).** A pilot run through the live pipeline (a real model via
  OpenRouter, Milestone M1) validated that an LLM can drive the harness end-to-end, but did **not** validate
  C1–C5: the multi-file task is *batchable*, so the real model created all files in one action and **finished
  before the injected crash could fire** — recovery was never exercised. A systematic-debugging pass then
  found that the failure-injection harness was **silently scoring these non-failures as valid recoveries**
  (a deterministic probe showed a fabricated `task_success=True, recovery_tax=0`). This benchmark-integrity
  bug is now fixed (`run_until_failure` reports whether the failure fired; `run_matrix` skips and reports
  vacuous cells), so the live run honestly reports *"recovery not exercised"* rather than a misleading
  number. The concrete next step (M2): a task that forces **non-batchable sequential** steps, with metrics
  robust to a model's action granularity (see the claims registry, 2026-06-16).
- **Second live run on a non-batchable task (M2, recorded honestly).** Milestone M2 built a non-batchable
  **chain task** (a salted hash-chain whose oracle advances at most once per process, so the model cannot
  one-shot it), work-unit metrics (robust to action granularity), and a repetition+statistics harness. Run
  live against `nvidia/nemotron-3-super-120b-a12b:free` (2026-06-23), the injected crash **actually fired in
  every cell** — recovery was exercised against a real model for the first time. At n=2 repetitions, **RGR
  (B3) completed the task in 2/2 runs with a consistent recovery tax (1.0 ± 0.0)** while **cold restart (B0)
  completed only 1/2 with an erratic tax (2.5 ± 2.5)** — RGR dominates on every axis mean and is markedly more
  reliable (its shorter recovery path exposes a flaky model to fewer failure points). We nonetheless report
  **C1 as suggestive, not confirmed**: the strict no-overlap verdict is not met (B0's failed run has tax 0, a
  non-recovery), n=2 is underpowered, and a larger run was blocked by the free tier's rate limit (HTTP 429).
  This is a genuine step past M1 — the benchmark is now recovery-faithful and yields real live evidence — but
  a **powered** live study remains the gate for any C1-confirmed-live claim; **v1.0 stays held**.
- **Powered live study (M3, recorded honestly).** Milestone M3 added a success-conditioned recovery tax (a
  failed run can no longer register a cheap tax), multi-provider OpenAI-compatible transports (Groq, ZenMux —
  so the run is not hostage to one rate-limited free tier), and ran the study against `gpt-oss-120b`. Across
  **28 fired cells** the mechanism was at its strongest live: RGR **≈ halves recovery tax with no overlap**,
  with higher success and less regression than cold restart. Even so, the *strict* C1 verdict is **NOT
  SHOWN** — confounded by model competence and residual rate-limits — so the go/no-go was again **NO-GO** and
  the project **stays 0.x**. The remaining gate is a paid/reliable model with a capability-matched C1 verdict
  and C3 wired live (see the claims registry, 2026-06-29).
- **Availability as a BYOM library (M4).** Rather than block on paid-API access, the recovery mechanism is
  now packaged as a **bring-your-own-model library**: public `checkpoint`/`recover` primitives, an opt-in
  `Agent` loop, and a `World` abstraction that de-couples recovery from the filesystem. This makes C1
  **reproducible by any reader on their own model** — the mechanism ships independently of us proving it on a
  paid model. It changes distribution, not the evidence: the honest scope above is unchanged and v1.0 stays
  held (see `docs/guide/recovery-in-your-agent.md`).
- **Failure types.** Only `crash` is faithfully realized; context-overflow, tool-timeout, and model-error
  are modeled as a typed stop-at-`k`.
- **Restore-first resume.** Torn-write detection is reserved for a future crash-in-place mode (§5, ADR-0008 §7).
- **B1/B2 in determinism.** Log-replay and snapshot-only resemble cold restart on cost here; their
  distinguishing weakness is non-determinism, again future work.
- **Solution-quality proxy.** Measured by artifact-digest match; an LLM-judge grader plugs in behind the
  same seam.

## 10. Conclusion

Recovery for long-horizon agents need not mean starting over. By recognizing that **checkpoints are
compactions**, a single distillation mechanism can serve both staying-in-context and surviving-a-crash;
re-grounding (not replay) resumes correctly under non-determinism; and a write-ahead ledger keeps the
world safe from duplicated effects. Cairn packages these as a specification, a minimal reference
implementation, and a measurable benchmark — so that "the agent recovered" becomes a claim one can test,
not just assert.

## References (in-repo)

- Problem formalization — `docs/concepts/problem-formalization.md`
- Two-layer model — `docs/concepts/code-harness-and-runtime.md`
- Recovery in the two-layer model — `docs/concepts/recovery-in-the-two-layer-model.md`
- State taxonomy — `docs/concepts/state-taxonomy.md`
- Tool-effect taxonomy — `docs/concepts/tool-effect-taxonomy.md`
- Recovery fidelity — `docs/concepts/recovery-fidelity.md`
- Continuation State schema — `docs/design/continuation-state-schema.md`
- Boundary contract — `docs/design/boundary-contract.md`
- Resume protocol (RGR) — `docs/design/resume-protocol.md`
- Unified distillation — `docs/design/unified-distillation.md`
- Effect-safety protocol — `docs/design/effect-safety-protocol.md`
- Related work — `docs/research/related-work.md`
- Claims registry (C1–C5, with status) — `docs/research/claims-registry.md`
- Decision records — `docs/adr/` (ADR-0001 … ADR-0010)
