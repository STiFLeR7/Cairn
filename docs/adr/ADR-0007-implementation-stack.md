---
title: ADR-0007 — Implementation stack and the no-hardcoded-harness principle
status: frozen
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0019, AP-0020, AP-0021, AP-0022]
related_adrs: [ADR-0003]
---

# ADR-0007 — Implementation stack & no-hardcoded harness

- **Status:** Accepted
- **Date:** 2026-06-15

## Context

Phase 3 introduces the first runnable code (the Minimal Harness). It needs a language, a sandbox model,
and a model-provider strategy. The overriding constraint is that the harness must be a *framework-agnostic
reference implementation* — it must not be hardcoded to a specific model, toolset, task, or path.

## Decision

1. **Language: Python.** Best fit for the agent ecosystem, matches the Phase 2 pseudocode, and gives easy
   subprocess control for the sandbox. Tooling: `pyproject.toml`, `pytest`.
2. **Sandbox: a pluggable `Sandbox` interface with a local-subprocess default.** Docker/E2B/etc. are
   injected implementations added later — never assumed by the harness.
3. **Model: a pluggable `ModelProvider` interface with a scriptable mock default.** The mock makes
   recovery tests deterministic; real LLM adapters are injected plugins.
4. **No hardcoded harness (overriding principle).** The model provider, tool registry, task definitions,
   storage backends, sandbox, and recovery policies are all **injected** and configurable. No literal
   model id, tool list, task, or path appears in harness code. Everything is programmed against the
   [boundary contract](../design/boundary-contract.md) (ADR-0003) and the Phase 3 interfaces.

## Consequences

- The codebase is built around interfaces (ABCs / `typing.Protocol`) + dependency injection + config;
  concrete implementations live *behind* the interfaces and ship as defaults, never inline.
- Deterministic recovery testing (Phase 4/5) is possible via the scriptable mock model.
- Slightly more upfront abstraction than a one-off script — accepted as the price of the
  contract-portability goal.

## Supersedes / superseded by

None.
