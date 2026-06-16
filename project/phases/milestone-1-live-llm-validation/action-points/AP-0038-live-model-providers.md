---
id: AP-0038
title: Live LLM ModelProvider adapters (injected, no hardcoding)
phase: milestone-1-live-llm-validation
status: Done
owner: maintainers
created: 2026-06-16
updated: 2026-06-16
depends_on: []
related_docs: [docs/adr/ADR-0010-live-model-provider-integration.md, src/cairn/model.py, src/cairn/model_live.py]
related_adrs: [ADR-0007, ADR-0010]
---

## Objective

Integrate one or more **real LLM `ModelProvider`s** behind the existing `cairn.model` seam so the harness
can run against a genuine model instead of the deterministic `ScriptableMockModel`. The provider and model
id are **injected via configuration** — Cairn's core remains free of any hardcoded model, key, or endpoint
(ADR-0007). This is the foundational AP of the milestone: every later AP runs on top of it.

## Scope

**In:** a live provider adapter (e.g. an Anthropic-API-backed `ModelProvider`) implementing the same
interface the mock satisfies; config-driven selection of provider + model id (env/CLI/config, never
in-source); secret handling that keeps API keys out of the repo and logs; a documented provider-integration
decision (**ADR-0010**); a thin "live vs mock" switch so the existing harness/benchmarks accept either.
**Out:** the actual study run (AP-0040); determinism/caching/budget machinery (AP-0039); supporting more
than one provider family if one suffices for the study (additional providers are optional).

## Deliverables

- A real-LLM `ModelProvider` adapter wired behind `cairn.model`, selected purely by injected config.
- `ADR-0010` — live-LLM provider integration decision (interface mapping, secret handling, why this design
  preserves no-hardcoded-harness).
- A unit/contract test that the live adapter satisfies the `ModelProvider` protocol (mocked transport — no
  network in CI), plus docs on how to point a run at a real model.

## Acceptance Criteria

- [x] A real LLM provider runs behind the existing model seam with **provider + model id injected** (no
      hardcoded model/key/endpoint in core) — verified by the same no-hardcoded-harness grep used each phase
- [x] The adapter satisfies the `ModelProvider` protocol; existing harness/benchmarks accept it via config
- [x] API keys are sourced from the environment/secret store, never committed or logged
- [x] `ADR-0010` records the integration decision; CI tests pass without live network calls
- [x] Docs + trackers updated

## Dependencies

- none (builds on the merged Phase 3 `cairn.model` seam)

## Status / Log

- 2026-06-16 — Proposed → Accepted (refined on Milestone M1 entry).
- 2026-06-16 — Accepted → Done. Delivered `src/cairn/model_live.py`: `LiveModelProvider` over an injected
  `Transport` (`prompt -> text`), overridable `render_prompt`/`parse_action` (fenced block → `CODE`,
  `TASK_COMPLETE` sentinel → `FINISH`, malformed → safe `FINISH`), and `anthropic_transport(*, model, ...)`
  — `model` injected (no default id), key from `$ANTHROPIC_API_KEY`, SDK lazily imported as the `cairn[live]`
  extra, fake-`client` injection for offline tests. `ADR-0010` accepted. `tests/test_model_live.py` (10
  tests, all offline) → **52 passed**; core grep shows no model-id/key literals (ADR-0007 preserved).
