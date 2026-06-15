---
title: Research Claims Registry
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0011]
related_adrs: [ADR-0001]
---

# Research Claims Registry

The falsifiable claims Cairn commits to defending. Registering claims *before* building keeps the work
honest: every later phase either supports, refines, or refutes a registered claim, and negative results
are recorded rather than buried.

## Claim schema

Each claim has:

- **ID** — `C<n>`, monotonic, never reused.
- **Statement** — a single falsifiable proposition.
- **Rationale** — why we expect it to hold.
- **Evaluated by** — the fidelity axis/axes ([recovery-fidelity.md](../concepts/recovery-fidelity.md)),
  baseline comparison, and the Phase 5 AP that tests it.
- **Status** — `registered` → `supported` | `refined` | `refuted` (set by evidence, with a dated note).

## Freeze policy

A claim is **immutable once registered**. Evidence updates only its **Status** (with a dated log line). To
change a claim's *statement*, register a **new** claim that supersedes the old one and mark the old one
`refined` (or `refuted`) — never edit a registered statement in place. This mirrors the ADR practice.

## Registered claims

### C1 — Re-grounding beats cold restart
- **Statement:** After a failure at step `k`, Re-grounding Recovery (RGR, B3) achieves higher recovery
  fidelity than cold restart (B0) on the same task and failure.
- **Rationale:** RGR preserves completed work, intent, and ruled-out dead-ends; cold restart discards all
  of it.
- **Evaluated by:** task success, solution quality, no-regression, recovery tax; B3 vs B0; `AP-0029`/`AP-0030`.
- **Status:** registered.

### C2 — Unified distillation does not degrade checkpoint fidelity
- **Statement:** A Continuation State produced by the **unified** distillation mechanism (durable core +
  elastic tail, shared with compaction) yields recovery fidelity no worse than a checkpoint-only baseline
  that distills solely for recovery.
- **Rationale:** the durable core is exactly the state both compaction and checkpointing require; the
  elastic tail is frozen at checkpoint time, so unification should not cost fidelity. This is the testable
  heart of *Checkpoints Are Compactions*.
- **Evaluated by:** all five axes; unified vs checkpoint-only ablation; `AP-0031`.
- **Status:** registered.

### C3 — Effect-safety WAL eliminates duplicate effects
- **Statement:** With the write-ahead effect ledger, resume produces **zero** duplicated irreversible
  effects for `check-before-retry` tools.
- **Rationale:** `INTENT`-without-`COMPLETE` detection + idempotency-key/query gating closes the danger
  window for queryable effects.
- **Evaluated by:** effect-safety axis (hard gate); with-WAL vs without-WAL; `AP-0026`/`AP-0030`.
- **Scope note:** does **not** claim coverage of `never-retry` tools (acknowledged limit — see
  [tool-effect-taxonomy.md](../concepts/tool-effect-taxonomy.md)).
- **Status:** registered.

### C4 — Re-grounding is robust to cross-version resume
- **Statement:** RGR retains recovery fidelity when the model/version that resumes differs from the one
  that checkpointed, in cases where log-replay (B1) fails.
- **Rationale:** re-grounding re-derives from intent and observed world rather than reproducing tokens, so
  it does not depend on the original model's exact behavior.
- **Evaluated by:** task success, solution quality; checkpoint-on-A / resume-on-B; `AP-0032`.
- **Status:** registered.

### C5 — A minimal sufficient Continuation State is empirically identifiable
- **Statement:** Ablating components of the Continuation State reveals a minimal subset below which
  fidelity sharply degrades — i.e. continuation sufficiency is measurable, not merely asserted.
- **Rationale:** fidelity provides the constraint; ablation provides the search over `S`.
- **Evaluated by:** all axes under component ablation; `AP-0031`.
- **Status:** registered.

## Status log

- 2026-06-15 — C1–C5 registered (Phase 1, `AP-0011`).
