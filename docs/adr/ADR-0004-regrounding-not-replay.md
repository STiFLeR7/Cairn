---
title: ADR-0004 — Resume by re-grounding, not trajectory replay
status: frozen
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0015]
related_adrs: [ADR-0001, ADR-0002]
---

# ADR-0004 — Re-grounding, not replay

- **Status:** Accepted
- **Date:** 2026-06-15

## Context

The classical recovery move is to replay a log from a checkpoint to rebuild state. For agents this is
unavailable: LLM execution is non-deterministic, so re-feeding the same inputs does not reproduce the same
trajectory ([problem-formalization](../concepts/problem-formalization.md), Assumption 2).

## Decision

Resume by **re-grounding**: reconstruct situational awareness from the Continuation State plus a
re-observation of the world, then re-plan — accepting that the resumed path may differ from the original.
The success bar is **outcome equivalence**, not trajectory equivalence. See
[resume-protocol.md](../design/resume-protocol.md).

## Consequences

- **Robust to non-determinism and to cross-version resume** (claim C4): re-grounding does not depend on
  reproducing the original model's exact behavior.
- Requires a sufficient Continuation State (ADR-0002) and re-observation before action.
- Gives up deterministic auditability of the resumed path — acceptable, since the world and effect ledger
  remain the source of truth and fidelity is measured on outcomes.

## Supersedes / superseded by

None.
