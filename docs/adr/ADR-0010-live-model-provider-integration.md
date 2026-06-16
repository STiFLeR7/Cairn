---
title: ADR-0010 — Live LLM provider integration (injected transport)
status: frozen
last_updated: 2026-06-16
owner: maintainers
related_aps: [AP-0038, AP-0039, AP-0040]
related_adrs: [ADR-0007]
---

# ADR-0010 — Live LLM provider integration via an injected transport

- **Status:** Accepted
- **Date:** 2026-06-16

## Context

Milestone M1 (Live-LLM Validation) needs the harness to run against a *real* model instead of the
deterministic `ScriptableMockModel`. The model seam is already `ModelProvider.propose(goal, history) ->
Action` (code-as-action, ADR-0007). The constraints when adding a real LLM are:

1. **No hardcoded harness** (ADR-0007) — no vendor, model id, API key, or endpoint may appear in core
   harness code; the provider must stay injected and configurable.
2. **CI must stay offline and free** — importing the adapter and running its tests must not require a
   vendor SDK, a network call, or a paid API key.
3. **The vendor SDK must not become a core dependency** — `pyproject` `dependencies` stays empty; only an
   opt-in extra pulls a provider library.

## Decision

1. **A `LiveModelProvider` that depends only on an injected `Transport`.** A `Transport` is a plain
   `Callable[[str], str]` (rendered prompt → raw reply text). The provider renders `(goal, history)` into a
   prompt, calls the transport, and parses the reply into an `Action`. The harness still only ever sees a
   `ModelProvider`; the LLM is reached purely through the injected transport.
2. **Overridable prompt rendering and parsing.** `render_prompt` and `parse_action` are module defaults but
   are injectable, so prompt strategy and reply parsing are not baked into the harness. Parsing rule: a
   fenced code block → `CODE`; else a completion sentinel (`TASK_COMPLETE`) → `FINISH`; else `FINISH`
   flagged as unparseable (a malformed reply ends the run rather than looping, recorded honestly in
   `Action.result`).
3. **Vendor SDKs are optional extras behind lazy-imported factories.** `anthropic_transport(*, model, ...)`
   requires `model` (injected — no default model id), reads the key from `api_key`/`$ANTHROPIC_API_KEY`
   (never source), and lazily imports `anthropic`. It accepts an injected `client` so the factory itself is
   testable with a fake — no SDK, no network. The SDK ships only as the `cairn[live]` optional extra.

## Consequences

- Core + CI remain offline and dependency-free; `test_model_live.py` exercises the provider and the
  Anthropic factory entirely with fakes.
- Adding another vendor is a new `*_transport` factory (or any callable) — the provider, harness, and
  benchmarks are unchanged. Determinism/cost controls (caching, transcripts, budget) wrap the transport in
  AP-0039 without touching the provider.
- The adapter is a bundled *plugin* like `ScriptableMockModel`, not a harness default: nothing selects it
  unless a caller injects it. This preserves the no-hardcoded-harness principle while making live runs easy.

## Supersedes / superseded by

None.
