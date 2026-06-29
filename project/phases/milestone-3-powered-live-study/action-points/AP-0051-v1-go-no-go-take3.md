---
id: AP-0051
title: v1.0 go/no-go, take 3
phase: milestone-3-powered-live-study
status: Done
owner: maintainers
created: 2026-06-29
updated: 2026-06-29
depends_on: [AP-0050]
related_docs: [docs/research/claims-registry.md, ROADMAP.md, project/phases/phase-6-paper-release]
related_adrs: [ADR-0009]
---

## Objective

Re-decide v1.0 on the M3 powered evidence. On "go", unblock AP-0036 (v1.0 release) and AP-0037
(announcement) — still gated on explicit user approval. On "no-go", record the gap and the next input.

## Scope

**In:** read the AP-0050 manifests + claims registry; decide go/no-go against the v1.0 gate (powered live
study validates the claims); update version status, ROADMAP, and the `hold-v1-until-live-llm` record.
**Out:** the run (AP-0050); cutting any tag or posting any announcement without explicit approval.

## Acceptance Criteria

- [x] A recorded, evidence-cited go/no-go decision
- [x] On "no-go": gap + next-milestone input recorded; project stays 0.x
- [x] Trackers + the v1.0-hold memory updated to reflect the outcome

## Decision: NO-GO (take 3) — strongest live signal yet, still not a clean confirmation

- 2026-06-29 — **NO-GO for v1.0.** The M3 powered run (AP-0050) is a clear step beyond M2: the first
  genuinely **powered** cell count (`gpt-oss-120b`, **28 fired cells**) shows RGR **≈ halving recovery tax
  with no overlap**, a higher success rate, and less regression than cold restart — directionally strong
  for C1, and corroborated by the Nemotron tax pattern. **But the strict `verdict_c1` is NOT SHOWN** on every
  model, for two honest reasons:
  1. **Model-competence confound.** Free models fail the task itself unpredictably (`gpt-oss` ~27%,
     `nemotron` 50% at n=2), so B3 never completes in *every* repetition. The strict every-repeat gate
     therefore measures model reliability as much as recovery quality — a **verdict-methodology gap** to fix
     next (a capability-matched / success-conditioned C1 verdict, distinct from "B3 succeeds every time").
  2. **Rate-limit confound.** Free/credit-less tiers can't sustain a powered run — 2 of 4 models produced
     0 cells (Groq quota exhausted, ZenMux 402), Nemotron lost 2/3 repeats to 429.
- **Consequence.** v1.0 stays **held**; project remains **0.x**. **AP-0036 (release) and AP-0037
  (announcement) stay `Blocked`.** No tag, release, or announcement. The v1.0 gate for the *next* milestone:
  a **paid / higher-rate-limit, instruction-reliable model**, a **capability-matched C1 verdict**, and
  wiring **C3 (effect-safety)** live. M3 itself ships nothing new outward — it is recorded on its branch and
  merged to keep master the integration point (per branch-per-phase).
