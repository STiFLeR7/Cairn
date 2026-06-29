# Milestone M3 — Powered live study (the v1.0 gate)

- **Status:** 🟡 In progress *(started 2026-06-29; branch `milestone-3-powered-live-study`)*
- **Goal:** Turn M2's *suggestive* live C1 evidence into a **powered, confirmable** result, and close the
  remaining fairness gap the M2 go/no-go flagged. M2 ran the non-batchable chain live for the first time and
  the crash fired in every cell, but the evidence was underpowered (n=2, single free model, rate-limited
  before a larger run) and the strict verdict was NOT SHOWN. M3 runs the study with **more repetitions and
  both crash points across multiple providers** (OpenRouter / Groq / ZenMux), hardens the tax metric so a
  *failed* run can't look cheap, and re-decides v1.0.

> **Why this milestone exists.** v1.0 is held until a live-LLM study *validates* the claims (not merely
> suggests them). M2 produced the first genuine recovery exercise live; M3 is the powered run that the v1.0
> gate actually requires. See `hold-v1-until-live-llm` and the [claims registry](../../../docs/research/claims-registry.md).

## Goals

- **Success-conditioned recovery tax** (`AP-0048`) — the fairness fix: `recovery_tax` is the cost of a
  *successful* recovery, measured over successful repetitions only, so a run that fails cheaply cannot
  register a misleadingly low tax or "win" by failing. The strict C1 verdict compares cost-of-success to
  cost-of-success and declines when a competitor never actually recovers.
- **Multi-provider OpenAI-compatible transports** (`AP-0049`) — Groq and ZenMux added as pure config
  (endpoint + key env) routed through one generic `openai_chat_transport`, so the powered run is not hostage
  to a single rate-limited free tier. No new bespoke code per vendor (ADR-0010).
- **Powered live study + claims update** (`AP-0050`) — run the chain study with more repetitions and both
  crash points against the available providers/models; record dated **live** evidence for C1 (and C3 where
  wired) with repetition statistics, supporting *or* refuting (ADR-0009).
- **v1.0 go/no-go, take 3** (`AP-0051`) — re-decide on the M3 evidence; on "go", unblock AP-0036/0037 (still
  gated on explicit approval); on "no-go", record the gap and the next input.

**Constraints:**
- **No hardcoded harness** (ADR-0007 / ADR-0010) — providers are injected config; the harness is unchanged.
- **Honest results** (ADR-0009) — negatives recorded, not buried; statistics reported with their spread.
- **Secret hygiene** — provider keys (`OPENROUTER_API`, `GROQ_API_KEY`, `ZENMUX_API`) live in `.env`
  (gitignored), read from the environment only, never staged, printed, or committed.
- **Branch-per-phase** — this milestone lives on its own branch; master stays clean and merges via PR.

## Action Points

| ID | Title | Status |
|---|---|---|
| [AP-0048](action-points/AP-0048-success-conditioned-tax.md) | Success-conditioned recovery tax (fairness fix) | Done |
| [AP-0049](action-points/AP-0049-multi-provider-transports.md) | Multi-provider OpenAI-compatible transports (Groq, ZenMux) | Done |
| [AP-0050](action-points/AP-0050-powered-live-study.md) | Powered live study + claims update | In progress |
| [AP-0051](action-points/AP-0051-v1-go-no-go-take3.md) | v1.0 go/no-go, take 3 | Blocked (on AP-0050) |

## Dependency order

```
AP-0048 (tax fix) ──┐
                    ├──→ AP-0050 (powered live study) ──→ AP-0051 (v1.0 go/no-go take 3)
AP-0049 (providers)─┘
```

## Completion criteria

- [x] `recovery_tax` is success-conditioned; a failed run cannot register a cheap tax (AP-0048, tested)
- [x] Groq + ZenMux selectable as providers via config; inert without a key; unknown provider rejected (AP-0049)
- [ ] A powered live run (more repeats, both crash points, ≥1 provider) with dated C1 evidence + statistics (AP-0050)
- [ ] A recorded v1.0 go/no-go take 3; version status reflects the evidence (AP-0051)
