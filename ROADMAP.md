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

> **Next milestone (post-7-phase): live-LLM study → v1.0.** The 7-phase arc delivered the specification,
> a recoverable reference harness, and a reproducible benchmark — all validated on a *deterministic*
> reference harness. The next milestone replaces the scripted mock with real LLM model providers, runs the
> failure-injection benchmark live, and (on success) cuts the **v1.0** release + announcement (AP-0036/0037,
> currently deferred). Until then the project stays at **0.x**.

## AP distribution

37 planned Action Points span the 7 phases (~4–6 each). **Phases 0–5 APs (AP-0001 … AP-0033) are
committed and `Done`**; Phase 6 APs are provisional placeholders refined when their phase is entered.
Full list: [`project/tracking/ap-index.md`](project/tracking/ap-index.md).
