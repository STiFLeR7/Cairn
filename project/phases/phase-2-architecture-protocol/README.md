# Phase 2 — Architecture & Protocol Design

- **Status:** 🟢 Complete on branch *(2026-06-15 — awaiting review + merge to `master`)*
- **Goal:** Specify the recovery *mechanism* — schemas, the boundary contract, and the protocols —
  as design docs and ADRs. Design, not implementation: no runnable code (that is Phase 3+).

## Goals

Phase 1 established *what* recovery requires (continuation sufficiency, fidelity, the two-layer split,
the taxonomies). Phase 2 turns that into a buildable design:

- The **Continuation State** ("cairn") schema — durable core + elastic tail.
- The **Code Harness ↔ Runtime boundary contract** — the interface recovery forces us to make explicit.
- The **re-grounding resume protocol** — load → re-observe → reconcile → re-plan → continue.
- The **unified distillation** design — one mechanism for compaction and checkpointing (core/tail).
- The **effect-safety write-ahead protocol** — INTENT/COMPLETE ledger + idempotency.
- The **tool-effect → recovery-policy mapping** — operationalizing the three tool classes.

Each load-bearing decision is captured as an **ADR**; each spec lives in `docs/design/`.

## Action Points

| ID | Title | Status |
|---|---|---|
| [AP-0013](action-points/AP-0013-continuation-state-schema.md) | Continuation State (cairn) schema spec | Done |
| [AP-0014](action-points/AP-0014-boundary-contract.md) | Code Harness ↔ Runtime boundary contract spec | Done |
| [AP-0015](action-points/AP-0015-resume-protocol.md) | Re-grounding resume protocol spec | Done |
| [AP-0016](action-points/AP-0016-unified-distillation.md) | Unified compaction/checkpoint distillation design (core/tail) | Done |
| [AP-0017](action-points/AP-0017-effect-safety-protocol.md) | Effect-safety write-ahead protocol spec | Done |
| [AP-0018](action-points/AP-0018-tool-recovery-policy.md) | Tool effect taxonomy → recovery-policy mapping | Done |

## Dependency order

```
AP-0013 (schema) ─┬─→ AP-0016 (distillation: produces the schema)
                  ├─→ AP-0015 (resume: consumes schema + contract)
AP-0014 (contract)┘        ▲
        └─→ AP-0017 (effect-safety WAL) ─→ AP-0018 (tool→policy mapping)
```

Suggested execution: **AP-0013 → AP-0014** (the keystones), then **AP-0016** and **AP-0017**, then
**AP-0015**, then **AP-0018**.

## Checklist

- [x] Continuation State schema specified, traced to the state taxonomy (AP-0013)
- [x] Boundary contract specified (operations + invariants) (AP-0014)
- [x] Re-grounding resume protocol specified step-by-step (AP-0015)
- [x] Unified distillation (core/tail) designed; compaction≡checkpoint made concrete (AP-0016)
- [x] Effect-safety write-ahead protocol specified (AP-0017)
- [x] Tool→recovery-policy mapping specified (AP-0018)
- [x] ADRs recorded for the load-bearing decisions

## Completion criteria

- [x] All six specs authored in `docs/design/` and internally consistent
- [x] Every design decision traces to a Phase 1 concept (schema↔taxonomy, protocol↔fidelity, etc.)
- [x] ADRs accepted for the keystone decisions (schema shape, boundary contract, unified distillation)
- [x] The design is implementable — Phase 3 can build the substrate against these contracts
- [x] All Phase 2 APs `Done` or explicitly deferred (with reason)
- [x] ROADMAP and trackers updated
- [x] No runnable code introduced (Phase 2 is design)
