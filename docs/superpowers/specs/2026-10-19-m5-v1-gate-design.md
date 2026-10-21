# Milestone M5 — v1.0 gate (powered, capability-matched live study) — design

- **Date:** 2026-10-19
- **Status:** Design approved in conversation; awaiting written-spec review
- **Branch:** `milestone-5-v1-gate`
- **Predecessor:** M3 take-3 NO-GO (`project/phases/milestone-3-powered-live-study/action-points/AP-0051-*`),
  which set the next gate: a paid/reliable model, a capability-matched C1 verdict, and C3 wired live.

## 1. Intent

Run the live recovery study that can honestly decide **v1.0 GO or NO-GO**. M3's strongest run was
directionally strong for C1 but its strict verdict was confounded by two things this milestone removes:

1. **Rate limits:** free tiers lost whole models and repeats. M5 uses subscription CLIs (Claude Code,
   Codex) that sustain a powered run.
2. **Model competence:** the strict `verdict_c1` requires B3 to finish the task in *every* repetition, so
   it measures model reliability as much as recovery quality. M5 measures each model's own capability
   first and judges recovery relative to it.

M5 also wires **C3 (effect safety)** into the live run, which M3 named as part of the gate.

**Success:** a pre-registered verdict, computed by code frozen before any live call, returns GO, NO-GO or
INCONCLUSIVE, and the result is published whichever way it falls (ADR-0009).

## 2. Scope

**In scope**

- A Codex CLI response transport.
- A capability-matched C1 verdict, a live C3 verdict and a combined v1.0 gate verdict.
- A calibration run per model (no crash).
- Pre-registration of the protocol and verdict code before any live call.
- The powered live run on one Claude model and one OpenAI model.
- v1.0 go/no-go, take 4.

**Out of scope**

- C2, C4, C5 stay reference-harness only (as accepted in M3).
- No changes to the chain task, the baselines, the harness or `TerminalWorld`.
- No tag, release or announcement. A GO unblocks AP-0036/0037, which still need explicit owner approval.
- The existing strict `verdict_c1` is kept unchanged for comparison; it is not deleted or redefined.

## 3. Action points

| ID | Title | Depends on |
|---|---|---|
| AP-0052 | `codex_cli_transport`: Codex as a no-tools response transport | — |
| AP-0053 | Calibration run, capability-matched C1 verdict, live C3 verdict, gate verdict | — |
| AP-0054 | Pre-registration: freeze protocol + verdict code before any live call | AP-0052, AP-0053 |
| AP-0055 | Powered live run (Claude, Codex) | AP-0054 |
| AP-0056 | v1.0 go/no-go, take 4 | AP-0055 |

## 4. Components

### 4.1 Codex transport (AP-0052)

`codex_cli_transport(*, model: str | None = None, command: str = "codex", timeout: float = 120.0,
run=None, reasoning_effort: str | None = "medium", codex_home_source: str | None = None) -> Transport`
in `src/cairn/model_live.py`, mirroring `claude_code_transport`:

- Invokes `codex exec --ephemeral --skip-git-repo-check -s read-only -C <fresh empty temp dir>
  --output-schema <schema file> -o <reply file> --color never --ignore-user-config` with the rendered
  prompt on stdin, plus `-m <model>` when a model is given and `-c model_reasoning_effort="<effort>"`
  when an effort is set (the study pins `medium`).
- **Isolated Codex home.** `--ignore-user-config` alone still loads `~/.codex/hooks.json` and
  `~/.codex/AGENTS.md`, so on first call the transport creates one temp `CODEX_HOME`
  (`cairn-codex-home-*`) holding only a copy of `auth.json` from `codex_home_source` (default
  `$CODEX_HOME` or `~/.codex`; missing auth raises `LiveModelConfigError`), reuses it for every later
  call, and removes it at exit. Codex runs with the inherited environment plus that `CODEX_HOME`, so the
  user's hooks, instructions and config never reach the model. Auth contents are never printed or logged.
- **Tree-killing timeout.** On Windows `subprocess.run(timeout=)` on a `.cmd` shim kills only `cmd.exe`
  and then blocks on pipes held by the node/codex grandchildren. The default runner
  (`_run_tree_killing`) kills the whole tree (`taskkill /T /F`, `kill()` elsewhere) and raises
  `TimeoutExpired`, so the timeout is enforced.
- Uses the same system instruction and JSON reply schema as the Claude transport, so `parse_action`
  is unchanged.
- Returns only the reply text. Cairn executes the parsed action in `TerminalWorld`, as for every
  transport. Codex never touches the benchmark checkout: it runs in an empty temp dir with a read-only
  sandbox, and the prompt forbids tool use.
- Errors (missing command, timeout, non-zero exit, empty or invalid reply) raise
  `LiveModelConfigError`, as the Claude transport does.
- Registered in `benchmarks/scenarios.py` next to the `claude_code` provider.

**Known risk:** on this machine Codex's Windows sandbox cannot start a shell. For a no-tools transport
that is acceptable (any attempted tool call fails closed). A throwaway probe confirms a plain completion
works under `-s read-only` before AP-0052 is implemented; if it does not, the fallback is to stop and
ask (running Codex unsandboxed as a transport is not assumed).

**Tests:** unit tests with an injected `run` (as `test_claude_code_transport_*`): argument shape,
reply extraction, each error path.

### 4.2 Verdicts and calibration (AP-0053)

All in `src/cairn/eval/runner.py` (pure functions over the existing `aggregate_repeated` summary), with
unit tests on synthetic summaries.

**Calibration.** For each model, run the chain task (`live_chain_scenario(6)`) **with no injected
crash** `R_cal = 10` times. `calibration_rate = successes / completed runs`. A model is **eligible** only
if `calibration_rate >= 0.80` and at least 9 of 10 runs completed without transport error.

**`verdict_c1_capability(summary, calibration_rate)`** — C1 supported iff all hold:

1. B0 and B3 both have fired cells, and B0 has at least one success (AP-0048 rule, unchanged).
2. **Capability-matched success:** `B3.success_rate >= calibration_rate - 0.10` and
   `B3.success_rate >= B0.success_rate`.
3. **Tax:** B3's success-conditioned recovery tax is strictly below B0's with no overlap
   (`B3.tax.max < B0.tax.min`), unchanged from the strict verdict.
4. **Regression:** `B3.no_regression.mean >= B0.no_regression.mean`.

Returns a structured verdict with each condition's value and pass/fail.

**`verdict_c3_live(summary)`** — C3 supported iff B3 has **0** effect duplicates in every fired cell and
B0 has **at least one** duplicate across its cells (showing the torn effect is real without the WAL).

**`verdict_v1_gate(per_model)`** — over both models:

- **INCONCLUSIVE** if either model is ineligible at calibration, or more than 10% of planned study cells
  for either model were lost to transport errors or rate limits.
- **GO** if C1 (capability-matched) and C3 are both supported on **both** models.
- **NO-GO** otherwise.

### 4.3 Live scenario with C3

A live chain scenario with an `EffectSpec(key="send-report", at_step=k)` torn at the crash step, so
every study cell exercises C1 and C3 together and C3 costs no extra calls. This reuses the existing
`EffectSpec` and baseline machinery; the only new piece is composing them with the live chain scenario.

## 5. Study protocol (AP-0055)

Per model (Claude `sonnet` at `--effort low` via `claude_code_transport`; Codex pinned to model
`gpt-6-sol` at reasoning effort `medium` via `codex_cli_transport` with an isolated Codex home; for both,
the exact model ids reported by the CLI are recorded at run time as `observed_models`):

1. Calibration: 10 uncrashed chain runs. Stop for that model if ineligible (recorded, not hidden).
2. Study: chain `n=6`, crash steps `k ∈ {2, 3}`, baselines B0 (cold restart) and B3 (RGR), **8 repeats**
   → 32 planned cells per model, each with the torn `send-report` effect.
3. Transcript and manifest per model under `benchmarks/transcripts/` (existing format), including
   transport errors and skipped cells.

Estimated usage: ~1,500–2,500 CLI calls per model.

## 6. Pre-registration (AP-0054)

Before the first live call:

- Write `results/m5/protocol.json`: models/aliases, `R_cal`, eligibility threshold, `n`, crash steps,
  repeats, baselines, effect spec, all verdict thresholds, and the loss threshold.
- Commit the verdict code and protocol; record that commit hash and the SHA-256 of `runner.py`,
  `model_live.py`, `scenarios.py` and `protocol.json` in `results/m5/preregistration.json`, committed and
  pushed **before** AP-0055 starts.
- AP-0055 refuses to run if the working tree differs from the pre-registered hashes.
- The freeze covers every `src/cairn/**/*.py`, `benchmarks/*.py` and `protocol.json`, and must equal the
  committed bytes: `write_preregistration` refuses if any frozen path is untracked or its working-tree
  bytes differ from `HEAD`. It also refuses to overwrite an existing `preregistration.json` unless forced
  (`write --force`), and then keeps the old file as `.superseded-<UTC>`.
- Every record is bound to the preregistration: it stores `preregistration_sha256` (SHA-256 of
  `preregistration.json`) and `preregistration_commit`. The gate is INCONCLUSIVE if any record's digest
  differs from the current preregistration, and `gate-verdict.json` lists per-model accounting, skipped
  cells, call stats, observed models and every `*.superseded-*` file.
- Thresholds are not changed after any live data is seen. A change requires a new pre-registration and
  invalidates earlier live data for the gate.

## 7. Go/no-go (AP-0056)

Compute `verdict_v1_gate` from the recorded runs with the pre-registered code. Record the decision,
per-model numbers, and the strict `verdict_c1` alongside for comparison in the claims registry, ROADMAP,
CHECKLIST, the M5 README and the v1.0-hold record. On GO, AP-0036/0037 move from `Blocked` to
"awaiting owner approval". On NO-GO or INCONCLUSIVE, record the gap and next input; the project stays 0.x.

## 8. Error handling

- Transport errors are counted per cell, never retried silently within a cell; a repeat that errors is
  recorded and counted against the 10% loss threshold (`run_repeated(..., resilient=True)` behaviour).
- Rate-limit or usage-cap exhaustion pauses the run; resumption continues with remaining planned cells
  and is noted in the record. Implemented as: every calibration run and every study repeat is one unit,
  appended as a JSON line to `results/m5/<label>.partial.jsonl` (header line: preregistration digest and
  label). Two consecutive errored units pause the run (`StudyPaused`, exit code 3) with the checkpoint kept.
  `python benchmarks/m5_study.py <label> --resume` requires the header digest to equal the current one,
  reuses units whose latest line is `ok`, re-attempts errored or missing units, and reports every earlier
  error line in the record as `resumed_errors` (count and texts). Units still errored at the end count as
  lost. Calibration eligibility is decided only once all calibration units are done. On completion the
  record is written and the checkpoint is renamed `<label>.partial.done-<UTC>.jsonl`.
- **Retry counting.** `build_live_transport` counts calls and raised errors at the base transport (inside
  `retrying`), so every retried attempt is visible; records store this as `call_stats`. Transport errors
  include CLI `is_error` responses (e.g. structured-output exhaustion) and count as loss in both
  calibration and study (record field `notes`); `errors` keeps up to 20 texts and `error_count` the total.

## 9. Testing

- Unit: Codex transport (injected runner), each verdict function (synthetic summaries covering every
  branch), gate verdict outcomes (GO / NO-GO / INCONCLUSIVE).
- Offline end-to-end: the full M5 pipeline with fake transports (as `run_offline_repeated_study`), so the
  live run only swaps the transport.
- Full existing suite stays green.

## Amendments (2026-10-19, before freeze)

Made after the final review and before any live call or pre-registration; no live data existed.

1. Codex transport: isolated `CODEX_HOME` (only `auth.json`), `--ignore-user-config`, pinned reasoning
   effort, tree-killing timeout (§4.1).
2. Codex model pinned to `gpt-6-sol` at `medium` effort; Claude's `--effort low` recorded in the protocol;
   Claude's exact model ids recorded from `modelUsage` (§5).
3. Records bound to the preregistration digest; gate INCONCLUSIVE on mismatch; the freeze must equal the
   committed bytes; `write` refuses to overwrite without `--force` (§6).
4. Per-unit checkpoints with pause after two consecutive errored units, `--resume`, `resumed_errors`, and
   base-level `call_stats` (§8).
5. The C1 capability boundary `B3.success_rate >= calibration_rate - 0.10` is evaluated as
   `>= round(calibration_rate - 0.10, 9)` so float error cannot fail an exact boundary (§4.2).
