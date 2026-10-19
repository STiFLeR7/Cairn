---
id: AP-0052
title: "codex_cli_transport: Codex as a no-tools response transport"
phase: milestone-5-v1-gate
status: Done
owner: maintainers
created: 2026-10-19
updated: 2026-10-19
depends_on: []
related_docs: [docs/superpowers/specs/2026-10-19-m5-v1-gate-design.md, src/cairn/model_live.py, benchmarks/scenarios.py]
related_adrs: [ADR-0007, ADR-0010]
---

## Objective

Add Codex as a second subscription-CLI response transport, so the v1.0 gate study can run on one Claude
and one OpenAI model without rate-limited free tiers.

## Scope

**In:** `codex_cli_transport(*, model=None, command="codex", timeout=120.0, run=None)` in
`src/cairn/model_live.py`, mirroring `claude_code_transport`: `codex exec --ephemeral
--skip-git-repo-check -s read-only -C <fresh empty temp dir> --output-schema <schema> -o <reply>` with the
prompt on stdin (plus `-m <model>` when given); same system instruction and JSON reply schema, so
`parse_action` is unchanged. Returns only the reply text; Cairn executes the action in `TerminalWorld`.
Errors raise `LiveModelConfigError`. Registered as the `codex_cli` provider in `benchmarks/scenarios.py`.
On Windows, Codex is an npm `.cmd` shim, so the command is resolved with `shutil.which` before launch.
**Out:** running Codex unsandboxed; tool use by the model; any change to the harness.

## Acceptance Criteria

- [x] Argument shape, reply extraction and each error path (missing command, timeout, non-zero exit, empty or invalid reply) unit-tested with an injected `run`
- [x] Codex runs in an empty temp dir with a read-only sandbox; never touches the benchmark checkout
- [x] Windows `.cmd` shim resolved via `shutil.which`
- [x] `codex_cli` provider registered next to `claude_code`

## Status / Log

- 2026-10-19 — Done. Implemented and reviewed on branch `milestone-5-v1-gate`.
