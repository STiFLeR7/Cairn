---
id: AP-0049
title: Multi-provider OpenAI-compatible transports (Groq, ZenMux)
phase: milestone-3-powered-live-study
status: Done
owner: maintainers
created: 2026-06-29
updated: 2026-06-29
depends_on: [AP-0040]
related_docs: [src/cairn/model_live.py, benchmarks/scenarios.py, tests/test_model_live.py]
related_adrs: [ADR-0007, ADR-0010]
---

## Objective

Stop the powered study being hostage to a single rate-limited free tier. Add Groq and ZenMux as live
providers with **no bespoke per-vendor code**: a provider is just an endpoint + a key-env, routed through
one generic OpenAI-compatible transport (ADR-0010 — a vendor is config, not a new code path).

## Scope

**In:** generalize `openrouter_transport` into `openai_chat_transport(*, model, url, api_key_env, …)` and
keep `openrouter_transport` as a thin back-compat wrapper; add an `OPENAI_COMPATIBLE_PROVIDERS` registry in
`benchmarks/scenarios.py` (`openrouter` → `OPENROUTER_API`, `groq` → `GROQ_API_KEY`, `zenmux` → `ZENMUX_API`);
route `build_live_transport` through it; reject unknown providers; keep the path inert without a key.
**Out:** the run itself (AP-0050); non-OpenAI-compatible vendors.

## Acceptance Criteria

- [x] One generic `openai_chat_transport` factory; `openrouter_transport` delegates (existing tests pass)
- [x] `groq` and `zenmux` selectable via `build_live_transport(provider=…)` as pure config
- [x] `api_key_env` overrides the provider default; keys read from env only, never hardcoded
- [x] Missing key → `LiveModelConfigError` (inert); unknown provider → `ValueError`
- [x] Offline tests with an injected `request` (no network); full suite green

## Status / Log

- 2026-06-29 — Done. Added `openai_chat_transport` (endpoint/key-env injected) in `model_live.py`;
  `openrouter_transport` now delegates to it. `benchmarks/scenarios.py` gained `OPENAI_COMPATIBLE_PROVIDERS`
  (openrouter/groq/zenmux) and `build_live_transport` routes any registry provider through the generic
  factory with retry + transcript + budget wrapping unchanged. Tests: generic transport is endpoint-agnostic,
  missing-key raises, provider routing covers all three + rejects unknown (`tests/test_model_live.py`).
  Suite green (110 passed).
