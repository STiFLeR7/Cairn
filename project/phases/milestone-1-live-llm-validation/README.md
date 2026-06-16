# Milestone M1 — Live-LLM Validation

- **Status:** 🟡 In Progress *(entered 2026-06-16 — branch `milestone-1-live-llm-validation`; AP-0038/0039 `Done`, AP-0040 runner offline-validated (live run gated), 69 tests)*
- **Goal:** Replace the deterministic scripted-mock model with **real LLM `ModelProvider`s** and re-run the
  Phase 5 failure-injection benchmark **live**, gathering empirical evidence for claims C1–C5 under genuine
  model non-determinism. On success this unblocks the deferred v1.0 release and announcement (AP-0036/0037);
  on failure or insufficient evidence, the negative result is recorded honestly and the project stays at 0.x.

> **Context.** The 7-phase arc (Phases 0–6) delivered the specification, a recoverable reference harness,
> and a reproducible benchmark — all validated on a *deterministic* mock (ADR-0009). Every C1–C5 verdict is
> scoped to that reference harness. This milestone is the prerequisite for any honest "v1.0": it tests the
> parts a deterministic mock structurally **cannot** — RGR's robustness to real non-determinism (C4 vs the
> fragility of log-replay B1), and whether the reference-harness fidelity cliffs (C5) survive a real model
> that actually exercises decisions and dead-ends.

## Goals

- **Live providers** (`AP-0038`) — real-LLM adapters behind the existing `cairn.model` seam, with the
  provider and model id **injected via config**, never hardcoded (ADR-0007 carries forward).
- **Determinism, cost & reproducibility controls** (`AP-0039`) — seed/temperature handling, response
  caching + transcript capture so live runs are auditable and re-runnable, and budget/rate-limit guards so a
  study can't run away on cost.
- **Live failure-injection study** (`AP-0040`) — run the Phase 5 matrix (step × failure-type × baseline)
  against at least one real model; capture raw results and transcripts.
- **Live results analysis & claims update** (`AP-0041`) — re-evaluate C1–C5 with live-scoped evidence;
  record negative/insufficient results rather than burying them; honest framing (ADR-0009) carried forward.
- **v1.0 go/no-go gate** (`AP-0042`) — decide, on the live evidence, whether to unblock AP-0036/0037. The
  release/announcement themselves remain **gated on explicit approval** even if the gate says "go."

**Constraints:**
- **No hardcoded harness** (ADR-0007) — the live providers are injected like every other dependency; no
  model id, key, or concrete task leaks into core.
- **Honest results** (ADR-0009) — live evidence is reported with the same discipline as the reference
  harness; a claim that fails to hold live is marked `refined`/`refuted`, not quietly dropped.
- **Outward/irreversible actions stay gated** — running a live study touches paid external APIs (cost) and
  any v1.0 release/tag/announcement remains held until explicit human go-ahead (see the
  [hold decision](../../../ROADMAP.md) and ADR-0009). A live-LLM provider integration ADR (**ADR-0010**) is
  authored when `AP-0038` starts.

## Action Points

| ID | Title | Status |
|---|---|---|
| [AP-0038](action-points/AP-0038-live-model-providers.md) | Live LLM `ModelProvider` adapters (injected, no hardcoding) | Done |
| [AP-0039](action-points/AP-0039-determinism-cost-repro.md) | Determinism, cost & reproducibility controls for live runs | Done |
| [AP-0040](action-points/AP-0040-live-failure-injection-study.md) | Live failure-injection study (Phase 5 matrix, real model) | In Progress *(runner offline-validated; live run gated)* |
| [AP-0041](action-points/AP-0041-live-results-claims-update.md) | Live results analysis & claims update (C1–C5) | Accepted |
| [AP-0042](action-points/AP-0042-v1-go-no-go.md) | v1.0 go/no-go gate (unblock AP-0036/0037 on success) | Accepted |

## Dependency order

```
AP-0038 (live providers) ──→ AP-0039 (determinism/cost/repro) ──→ AP-0040 (live study) ──→ AP-0041 (analysis/claims)
                                                                                                  │
                                                                                                  ▼
                                                                                   AP-0042 (v1.0 go/no-go gate)
                                                                                                  │
                                                                       (on "go" + explicit approval) ──→ unblock AP-0036/AP-0037
```

## Checklist

- [x] Real-LLM provider(s) run behind `cairn.model` with provider/model injected; no hardcoding (AP-0038, ADR-0007/0010)
- [x] Live runs are seed/temperature-controlled, cached, transcript-logged, and budget-guarded (AP-0039)
- [~] The Phase 5 failure-injection matrix runs through the live pipeline — offline-validated on a fake
  transport (reproduces C1/C3); **the real-model run is gated** (AP-0040)
- [ ] C1–C5 re-evaluated with dated, live-scoped evidence; negatives recorded (AP-0041, ADR-0009)
- [ ] Go/no-go documented; AP-0036/0037 unblocked only on "go" **and** explicit approval (AP-0042)
- [ ] No hardcoded harness; docs + trackers updated; tests green

## Completion criteria

- [ ] At least one real LLM provider is integrated behind the existing model seam, injected via config
- [ ] The live failure-injection study runs reproducibly (cached transcripts; documented cost/seed controls)
- [ ] The claims registry carries dated **live-LLM** evidence for C1–C5 (supporting *or* refuting), distinct
      from the reference-harness notes
- [ ] A recorded go/no-go decision on v1.0; if "go," AP-0036/0037 move from `Blocked` to actionable
      (still pending explicit approval for the outward release/announcement)
