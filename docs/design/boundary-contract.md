---
title: Code Harness ↔ Runtime Boundary Contract
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0014]
related_adrs: [ADR-0003]
---

# Code Harness ↔ Runtime Boundary Contract

The interface recovery forces us to make explicit
([recovery-in-the-two-layer-model.md](../concepts/recovery-in-the-two-layer-model.md)). It is the stable
seam between the **Runtime** (mechanism — faithful, durable) and the **Code Harness** (semantics —
intelligent, lossy). See [ADR-0003](../adr/ADR-0003-boundary-contract.md).

Signatures are language-neutral pseudotypes; the reference implementation (Phase 3) binds them to code.

## 1. Runtime-owned operations (mechanism)

```
snapshot_workspace() -> snap_id
    Capture the durable external state (taxonomy layer 1). Returns an opaque id.

checkpoint(state: ContinuationState, snap_id, effect_offset) -> checkpoint_id
    Atomically persist a cairn together with the workspace snapshot id and the
    effect-ledger offset valid at this instant. ATOMIC: either fully durable or not at all.

load_latest() -> (state, snap_id, effect_offset) | null
    Return the most recent fully-durable checkpoint, or null if none.

restore_workspace(snap_id) -> void
    Restore the workspace to a previously captured snapshot.

append_effect(intent, idempotency_key) -> effect_id
    Append an INTENT record to the append-only effect ledger BEFORE the side effect runs.

complete_effect(idempotency_key) -> void
    Append a COMPLETE record after the side effect succeeds.

list_effects_since(offset) -> [EffectRecord]
    Return effect-ledger records at or after offset (for resume-time reconciliation).
```

## 2. Code-Harness-owned operations (semantics)

```
distill(trajectory, prev_state?) -> ContinuationState
    Produce/update the cairn from recent activity (the salience policy). Same call
    serves compaction and checkpoint writes (AP-0016).

reconcile(state, observed_world) -> ResumePlan
    On resume, compare the cairn against the re-observed world and produce the next
    action / repaired plan (AP-0015).
```

The split is the [*one concern, two altitudes*](../concepts/code-harness-and-runtime.md) rule made
executable: the Runtime moves and guards bytes; the Code Harness decides meaning.

## 3. Invariants

The Runtime MUST uphold:

- **I1 — Write-ahead effects.** `append_effect` (INTENT) is durable *before* the side effect executes;
  `complete_effect` follows success. (Basis of effect-safety — [AP-0017](effect-safety-protocol.md).)
- **I2 — Atomic checkpoint.** `load_latest` never returns a partially-written cairn or a checkpoint whose
  `snap_id` is not fully captured. A checkpoint becomes visible only when wholly durable.
- **I3 — Monotonic effect offsets.** Offsets never decrease; `checkpoint` records the offset observed at
  checkpoint time.
- **I4 — Mutual consistency.** A persisted checkpoint references a real, restorable `snap_id` and a valid
  `effect_offset`.
- **I5 — Latest-before-failure.** `load_latest` returns the most recent checkpoint that became durable at
  or before the failure.

The Code Harness MAY assume I1–I5 and MUST treat `distill` output as satisfying the
[schema](continuation-state-schema.md) durable-core sufficiency rule.

## 4. Sequence sketches

**Normal operation (checkpoint at a step boundary):**
```
Code Harness: state = distill(trajectory, prev_state)
Runtime:      snap = snapshot_workspace()
Runtime:      checkpoint(state, snap, current_effect_offset)   # atomic (I2)
```

**Performing an irreversible effect (write-ahead, I1):**
```
Runtime: append_effect(intent="send_email#42", key="email-42")   # INTENT durable first
<<< side effect executes >>>
Runtime: complete_effect("email-42")                              # COMPLETE
```

**Resume after failure:**
```
Runtime:      (state, snap, offset) = load_latest()              # I5
Runtime:      restore_workspace(snap)
Runtime:      effects = list_effects_since(offset)
Code Harness: plan = reconcile(state, observe(world, effects))   # torn-step handling (AP-0015)
Code Harness: continue …
```

## 5. What this contract deliberately does not specify

- The *storage backend* for snapshots/ledger/checkpoints (Runtime's choice; Phase 3).
- The *salience policy* inside `distill` (AP-0016) and the *reconcile logic* (AP-0015).
- The *effect classification* used during reconcile (AP-0017 / AP-0018).

Keeping these out is intentional: the contract is the stable seam; the intelligence lives behind it.

## Summary

The boundary contract is a small operation set split into Runtime mechanism (`snapshot_workspace`,
`checkpoint`, `load_latest`, `restore_workspace`, `append_effect`/`complete_effect`,
`list_effects_since`) and Code Harness semantics (`distill`, `reconcile`), governed by five invariants
(write-ahead effects, atomic checkpoints, monotonic offsets, mutual consistency, latest-before-failure).
It is the seam Phase 3 builds against.
