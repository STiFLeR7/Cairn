---
id: AP-0056
title: v1.0 go/no-go, take 4
phase: milestone-5-v1-gate
status: Done
owner: maintainers
created: 2026-10-19
updated: 2026-10-21
depends_on: [AP-0055]
related_docs: [docs/superpowers/specs/2026-10-19-m5-v1-gate-design.md, docs/research/claims-registry.md, ROADMAP.md]
related_adrs: [ADR-0009]
---

## Objective

Compute `verdict_v1_gate` from the recorded runs with the pre-registered code and decide v1.0.

## Scope

**In:** record the decision, per-model numbers and the strict `verdict_c1` alongside, in the claims
registry, ROADMAP, CHECKLIST, the M5 README and the v1.0-hold record. On GO, AP-0036/0037 move from
Blocked to "awaiting owner approval". On NO-GO or INCONCLUSIVE, record the gap and next input; the project
stays 0.x.
**Out:** any tag, release or announcement without explicit owner approval.

## Acceptance Criteria

- [x] Recorded, evidence-cited go/no-go decision
- [x] Trackers and the v1.0-hold record updated
- [x] Result published whichever way it falls (ADR-0009)

## Decision: GO

`results/m5/gate-verdict.json`: "C1 (capability-matched) and C3 supported on both models". Pre-registered
(`results/m5/preregistration.json`, commit `e1b4280`, sha256 `226cc8866f2c…`; 92 source files + protocol at
code commit `168a6e6`) before any live call. Protocol: `results/m5/protocol.json`.

| | Claude `claude-sonnet-5-5` (CLI, effort low) | Codex `gpt-6-sol` (CLI, effort medium, isolated `CODEX_HOME`) |
|---|---|---|
| Calibration | 10/10 (rate 1.00) | 10/10 |
| Cells | 32/32 fired (B0 16, B3 16), 0 skipped, 0 lost | same |
| Calls / errors | 520 / 0 | 520 / 0 |
| C1-capability | supported: success B3 1.00 vs B0 1.00; B3 tax max 5.00 < B0 tax min 8.00 (B3 4.50 ± 0.50, B0 8.00 ± 0.00); no-regression B3 0.42 vs B0 0.00 | identical on every metric |
| C3 | supported: B3 0 duplicate effects, B0 16 | identical |
| Strict `verdict_c1` | also supported | also supported |

The runs are independent: 0 of 520 Codex replies are identical to Claude's. Sources:
[`claude.json`](../../../../results/m5/claude.json), [`codex.json`](../../../../results/m5/codex.json).

**Honest scope.**
1. Both models were fully competent on the task, so the capability-matched rule was never stressed.
2. The chain oracle advances one step per call, so recovery cost in work units is determined by task structure
   for a competent model. The evidence shows RGR's recovery mechanism cuts recovery tax (5 vs 8 work units at
   most/least) and preserves pre-crash work, with near-zero variance; it is not a broad live-performance or
   model-robustness claim.
3. C3's torn effect is injected by the harness at the crash step, so C3-live is "effect safety under live
   control flow", not model-dependent evidence.
4. C2/C4/C5 remain reference-harness only.
5. Single task (chain n=6), crash steps 2 and 3, 8 repeats, two models.
6. Not an ecosystem standard; not exactly-once delivery.

**Consequence.** AP-0036 (v1.0 release) and AP-0037 (announcement) move from `Blocked` to "Unblocked -
awaiting owner approval". No tag, release or announcement is made by this AP.

## Status / Log

- 2026-10-21 — Done. Decision GO recorded in the claims registry, ROADMAP, CHECKLIST, CHANGELOG, README and
  the AP index.
