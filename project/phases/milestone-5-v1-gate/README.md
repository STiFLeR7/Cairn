# Milestone M5 — v1.0 gate (powered, capability-matched live study)

- **Status:** 🟢 Complete *(branch `milestone-5-v1-gate`; all five APs done; **decision GO** 2026-10-21 —
  C1 (capability-matched) and C3 supported on both models; AP-0036/0037 unblocked, awaiting owner approval)*
- **Goal:** Run the live recovery study that can honestly decide **v1.0 GO or NO-GO**. M3's strongest run was
  directionally strong for C1 but its strict verdict was confounded by free-tier rate limits and model
  competence. M5 uses subscription CLIs (Claude Code, Codex), measures each model's own capability first,
  judges recovery relative to it, and wires C3 (effect safety) into the live run.

> **Why this milestone exists.** M3 ended NO-GO take 3 and set the next gate: a paid/reliable model, a
> capability-matched C1 verdict, and C3 live. Design: [spec](../../../docs/superpowers/specs/2026-10-19-m5-v1-gate-design.md);
> plan: [plan](../../../docs/superpowers/plans/2026-10-19-m5-v1-gate.md).

## Goals

- **Codex transport** (`AP-0052`) — Codex as a no-tools response transport next to Claude Code.
- **Calibration and verdicts** (`AP-0053`) — uncrashed calibration per model, capability-matched C1, live C3
  and the combined gate verdict; the strict `verdict_c1` is kept for comparison.
- **Pre-registration** (`AP-0054`) — protocol and verdict code hashed and committed before any live call.
- **Powered live run** (`AP-0055`) — Claude `sonnet` (effort low) and Codex `gpt-6-sol` (reasoning effort
  medium, isolated Codex home), 32 planned cells each; per-unit checkpoints, pause on consecutive errors,
  `--resume`.
- **v1.0 go/no-go, take 4** (`AP-0056`) — GO, NO-GO or INCONCLUSIVE, published whichever way it falls.

**Constraints:**
- **Honest results** (ADR-0009) — negatives recorded, not buried; thresholds fixed before live data.
- **Pre-registration guard** — the study runner refuses to run if any frozen file (every `src/cairn/**/*.py` and `benchmarks/*.py` file plus `protocol.json`) differs from its
  pre-registered hash, and refuses to overwrite a prior record without `--force` (the old record is kept as
  `.superseded-<UTC>`). The freeze must equal the committed bytes and is never overwritten without
  `--force`; every record stores the preregistration digest, and the gate is INCONCLUSIVE for a record
  bound to a different one.
- **No hardcoded harness** (ADR-0007 / ADR-0010) — no changes to the chain task, baselines, harness or `TerminalWorld`.
- **No release** — a GO only unblocks AP-0036/0037, which still need explicit owner approval.
- **Branch-per-phase** — master stays clean and merges via PR.

## Action Points

| ID | Title | Status |
|---|---|---|
| [AP-0052](action-points/AP-0052-codex-transport.md) | `codex_cli_transport`: Codex as a no-tools response transport | Done |
| [AP-0053](action-points/AP-0053-calibration-and-verdicts.md) | Calibration run, capability-matched C1 verdict, live C3 verdict, gate verdict | Done |
| [AP-0054](action-points/AP-0054-preregistration.md) | Pre-registration: freeze protocol + verdict code before any live call | Done |
| [AP-0055](action-points/AP-0055-powered-live-run.md) | Powered live run (Claude, Codex) | Done |
| [AP-0056](action-points/AP-0056-v1-go-no-go-take4.md) | v1.0 go/no-go, take 4 | Done |

## Dependency order

```
AP-0052 (codex) ───┐
                   ├──→ AP-0054 (pre-registration) ──→ AP-0055 (live run) ──→ AP-0056 (go/no-go take 4)
AP-0053 (verdicts)─┘
```

## Completion criteria

- [x] Codex transport implemented and tested (AP-0052)
- [x] Calibration, capability-matched C1, live C3 and gate verdicts implemented and tested (AP-0053)
- [x] Pre-registration written and committed (AP-0054)
- [x] Powered live run recorded for both models (AP-0055)
- [x] A recorded v1.0 go/no-go take 4 (AP-0056) — **GO**

## Outcome

**Decision: GO** for v1.0 (`results/m5/gate-verdict.json`: "C1 (capability-matched) and C3 supported on both models"). Details, numbers and honest scope: [AP-0056](action-points/AP-0056-v1-go-no-go-take4.md). AP-0036/0037 are Unblocked — awaiting owner approval; nothing has been tagged, released or announced.

## Note: verifying after the v1.0 version bump

The M5 pre-registration pins the code at `168a6e6`. After the v1.0 version bump, `python benchmarks/m5_preregister.py` at HEAD reports `src/cairn/__init__.py` as changed (`__version__` 0.3.0 → 1.0.0). This is expected; verify the M5 evidence at commit `e1b4280`.
