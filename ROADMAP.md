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

| Milestone | Name | Goal | Status | Completion criteria |
|---|---|---|---|---|
| **M1** | Live-LLM Validation | Re-run the benchmark against real LLMs | 🟡 In Progress | Live providers behind the model seam; the failure-injection study runs live; C1–C5 carry dated live-scoped evidence; a recorded v1.0 go/no-go |

> **Milestone M1 — Live-LLM Validation (entered 2026-06-16).** The 7-phase arc delivered the specification,
> a recoverable reference harness, and a reproducible benchmark — all validated on a *deterministic*
> reference harness. M1 replaces the scripted mock with real LLM model providers (injected, no hardcoding —
> ADR-0007), runs the failure-injection benchmark live, and re-evaluates C1–C5 under genuine non-determinism.
> On a "go" decision (AP-0042) it unblocks the deferred **v1.0** release + announcement (AP-0036/0037) — which
> still require explicit approval for the outward steps. Until then the project stays at **0.x**. Scaffold:
> [`project/phases/milestone-1-live-llm-validation/README.md`](project/phases/milestone-1-live-llm-validation/README.md).

## AP distribution

37 planned Action Points span the 7 phases (~4–6 each); **Milestone M1 adds AP-0038 … AP-0042** (5 APs).
**Phases 0–5 APs (AP-0001 … AP-0033) are `Done`** and merged; Phase 6 APs AP-0034/0035 `Done`, AP-0036/0037
`Blocked` (deferred to M1's go/no-go); M1 APs (AP-0038 … AP-0042) are committed and `Accepted`.
Full list: [`project/tracking/ap-index.md`](project/tracking/ap-index.md).
