# Cairn — Project Roadmap

> Canonical, always-visible view of the project spine. Phase internals are defined when a phase is
> entered (see [phase process](docs/governance/phase-process.md)). Live per-AP status lives in
> [`project/tracking/ap-index.md`](project/tracking/ap-index.md).

**Arc:** define → frame → design → build substrate → build recovery → evaluate → publish.

| Phase | Name | Goal | Status | Completion criteria |
|---|---|---|---|---|
| **0** | Project Definition | Establish identity + operating model | 🟢 Complete | Repo scaffolded with governance docs; vision/positioning/scope approved; AP + phase process live |
| **1** | Conceptual & Research Foundation | Formalize the problem; map the field | 🟢 Complete | Continuation-sufficiency & recovery-fidelity *defined*; related-work survey; claims registry; concept docs. **No code.** |
| **2** | Architecture & Protocol Design | Specify the mechanism (docs/ADRs) | 🟢 Complete | Continuation State schema, boundary contract, resume protocol, effect-safety WAL, tool taxonomy — accepted as specs/ADRs |
| **3** | Minimal Harness | Build the substrate (no recovery yet) | 🟢 Complete | Minimal Code Harness + Runtime honoring the boundary contract; baseline tasks complete |
| **4** | Recovery v1 (three pillars) | Unified distillation + re-grounding + effect-safety | 🟢 Complete | Agent recovers from injected failure end-to-end |
| **5** | Evaluation & Benchmark | Failure-injection harness, baselines, ablations | 🟢 Complete | Results reproduce the headline claims |
| **6** | Paper & Release | Write-up + reproducible OSS artifact | 🟢 Core done | Paper draft + reproducibility package merged. **v1.0 release & announcement deferred** to a future milestone (await a live-LLM study — current evidence is reference-harness only, ADR-0009). |

**Legend:** ⬜ Not started · 🟡 In Progress · 🟢 Complete · 🔴 Blocked

## Milestones (post-7-phase)

| Milestone | Name | Goal | Status | Outcome |
|---|---|---|---|---|
| **M1** | Live-LLM Validation | Re-run the benchmark against real LLMs | 🟢 Complete | **NO-GO** — live run didn't validate the claims; stays 0.x |
| **M2** | Recovery-faithful live benchmark | A non-batchable task + real-model metrics | 🟢 Complete (v0.2.0) | **NO-GO** for v1.0 — live run resolved the M1 blocker (crash fires, recovery exercised) and leans toward C1, but evidence is *suggestive, not confirmed* (n=2); stays 0.x |

> **Milestone M1 — Live-LLM Validation (complete 2026-06-16; outcome NO-GO).** M1 added real LLM providers
> behind the model seam (injected, no hardcoding — ADR-0007/0010: Anthropic + a stdlib OpenRouter factory),
> made live runs auditable/replayable/budgeted, and **ran the failure-injection study against a real model**
> (`openrouter/owl-alpha`). The live pipeline works — but the run **did not validate C1–C5**: the model
> batches the multi-file task into a single action and finishes before the injected crash, so the Phase-5
> scenario/metrics (built around the mock's one-action-per-step cadence) don't measure recovery and are
> unstable across repetitions. **Decision: NO-GO** — the project stays at **0.x**; the v1.0 release +
> announcement (AP-0036/0037) **stay `Blocked`**, now held *by evidence*. The fix becomes **M2**: a benchmark
> task that forces **non-batchable sequential** steps, metrics robust to a real model's action granularity,
> and repetitions with statistics. See the
> [claims registry](docs/research/claims-registry.md) (2026-06-16), `PAPER.md` §9, and
> [`project/phases/milestone-1-live-llm-validation/README.md`](project/phases/milestone-1-live-llm-validation/README.md).

> **Milestone M2 — Recovery-faithful live benchmark (complete 2026-06-23; shipped v0.2.0; outcome NO-GO for
> v1.0).** M2 fixed the M1 root cause. It built a **non-batchable chain task** (`cairn.eval.chain` — a salted
> hash-chain whose oracle advances at most once per fresh subprocess, so a model cannot one-shot it),
> **work-unit / action-granularity-robust metrics**, and a **repetition + statistics** harness (carrying the
> M1 injection-fired skip). The live run against `nvidia/nemotron-3-super-120b-a12b:free` was the first to
> **actually exercise recovery**: the injected crash **fired in every cell**, and RGR (B3) completed 2/2 with a
> consistent low recovery tax while cold restart (B0) completed only 1/2. **Decision: NO-GO** — the evidence
> *leans* toward C1 but is **suggestive, not confirmed** (n=2 underpowered; strict verdict not met; C2/C4/C5
> reference-only, C3 unwired; a powered run was rate-limited). The project **stays 0.x**, released as **v0.2.0**
> (a 0.x milestone, not the held v1.0); AP-0036/0037 stay `Blocked`. The v1.0 gate is now a **powered** live
> study. See the [claims registry](docs/research/claims-registry.md) (2026-06-23), `PAPER.md` §9, and
> [`project/phases/milestone-2-recovery-faithful-benchmark/README.md`](project/phases/milestone-2-recovery-faithful-benchmark/README.md).

## AP distribution

37 Action Points span the 7 phases; **M1 added AP-0038 … AP-0042** (5, all `Done`, merged PR #7) and **M2
adds AP-0043 … AP-0047** (5). **Phases 0–5 (AP-0001 … AP-0033) `Done`** and merged; Phase 6 AP-0034/0035
`Done`, AP-0036/0037 `Blocked` (now gated on a *powered* live study, post-M2); **M2 AP-0043…AP-0047 all
`Done`** (shipped v0.2.0). Full list: [`project/tracking/ap-index.md`](project/tracking/ap-index.md).
