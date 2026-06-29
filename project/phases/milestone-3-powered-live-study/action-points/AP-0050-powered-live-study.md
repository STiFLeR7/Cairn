---
id: AP-0050
title: Powered live study + claims update
phase: milestone-3-powered-live-study
status: Done
owner: maintainers
created: 2026-06-29
updated: 2026-06-29
depends_on: [AP-0048, AP-0049]
related_docs: [benchmarks/live_study.py, docs/research/claims-registry.md]
related_adrs: [ADR-0009]
---

## Objective

Run the non-batchable chain recovery study **powered**: more repetitions and both crash points, across the
available providers (OpenRouter / Groq / ZenMux), to move C1 from *suggestive* (M2) toward *confirmed* — or
to honestly record that it is not yet confirmed. Targets C1 (and C3 where wired); C2/C4/C5 remain
reference-harness for now.

## Scope

**In:** run `run_live_study` against Nemotron 3 Super (OpenRouter) and Groq/ZenMux free models with
`repeats > 2` and `steps=(2,3)`; record manifests + transcripts (secret-free); update the claims registry
with dated live evidence and the success-conditioned verdict; honest scope per ADR-0009.
**Out:** the go/no-go decision (AP-0051); paid/non-free tiers unless approved.

## Acceptance Criteria

- [x] ≥1 provider/model completes a powered run (more repeats than M2, both crash points), crashes fire
- [x] Manifests written, transcripts replayable offline, verified secret-free before commit
- [x] Claims registry updated with dated live C1 evidence + statistics, supporting or refuting
- [x] Result honestly scoped; the strict `verdict_c1` (now success-conditioned) reported as SHOWN / NOT SHOWN

## Status / Log

- 2026-06-29 — Done. Ran the chain study with up to 8 repeats + both crash points across four free-tier
  models / three providers (driver `benchmarks/run_m3_study.py`). Per-repeat resilience added to
  `run_repeated` (`resilient=True`, `errored` count, `on_error`) so a rate-limited repeat is isolated and
  recorded instead of aborting the whole study — turning M2's all-or-nothing fragility into honest partial
  results. Results (manifests committed):
  - **`openai/gpt-oss-120b` (Groq, 8 repeats): 28 fired, 0 errored — the headline powered run.** B3 (RGR)
    success 0.73 / tax **3.64 ± 0.77** (max 5.0) / no_reg 0.44; B0 (cold restart) success 0.46 / tax
    **6.33 ± 0.47** (min 6.0) / no_reg 0.23. RGR ≈ **halves tax with no overlap**, higher success, less
    regression — directionally strong C1.
  - **`nvidia/nemotron-3-super-120b-a12b:free` (OpenRouter, 3 repeats): 4 fired, 2 lost to 429.** Same tax
    pattern (B3 3.0 vs B0 6.5), tiny n.
  - **`llama-3.3-70b-versatile` (Groq) / `openai/gpt-4o-mini` (ZenMux): 0 fired** — Groq quota exhausted /
    ZenMux 402 payment-required. Honest negatives (resilience → clean `NOT SHOWN` manifests, no crash).
  - **Strict `verdict_c1` NOT SHOWN on all** — because real free models fail the *task itself* unpredictably
    (B3 `success.min < 1.0`), not because RGR failed. Methodology gap (competence vs recovery-quality)
    recorded as the AP-0051 input; the verdict was **not** loosened to manufacture a GO (ADR-0009).
  - A `User-Agent` header was added to the stdlib poster (Groq sits behind Cloudflare, which 403s
    `Python-urllib`). Artifacts secret-scanned clean. See claims registry (2026-06-29).
