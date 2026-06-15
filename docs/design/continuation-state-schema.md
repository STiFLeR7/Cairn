---
title: Continuation State Schema (the "cairn")
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0013]
related_adrs: [ADR-0002]
---

# Continuation State Schema

The **Continuation State** (a *cairn*) is the typed object that realizes the sufficient state `S` from
[problem-formalization.md](../concepts/problem-formalization.md). It is **structured, not a context
blob** — structure is what lets one object serve both compaction and checkpointing
([ADR-0002](../adr/ADR-0002-continuation-state-shape.md)). It has a **durable core** (the sufficient
statistic, never pruned) and an **elastic tail** (recent detail, prunable online / frozen at checkpoint).

Every field is traced to a layer of the [state taxonomy](../concepts/state-taxonomy.md).

## 1. Top-level shape

```jsonc
{
  "schema_version": "1.0",
  "durable_core": {
    "intent":        { ... },   // taxonomy layer 4
    "plan":          { ... },   // layer 4
    "decisions":     [ ... ],   // layer 3 (distilled)
    "effects_ref":   { ... },   // layer 2 (pointer)
    "world":         { ... },   // layer 1 (pointer + digest)
    "verification":  [ ... ],   // layer 3/1
    "provenance":    { ... }    // metadata
  },
  "elastic_tail":    { ... }    // layer 3 (recent, prunable)
}
```

## 2. Durable core — field by field

### `intent` — *(taxonomy layer 4: plan/intent)*
```jsonc
"intent": {
  "root_goal": "string",        // the task as originally given
  "active_subgoal": "string"    // what the agent is doing right now
}
```
Without intent a re-grounded agent does not know *what* it is doing. Mandatory.

### `plan` — *(layer 4)*
```jsonc
"plan": {
  "steps": [
    { "id": "s1", "description": "string",
      "status": "done | pending | blocked",
      "depends_on": ["s0"] }
  ]
}
```
The skeleton of progress: which steps are done, pending, or blocked, and their dependencies.

### `decisions` — decision ledger, *(layer 3, distilled)*
```jsonc
"decisions": [
  { "id": "d1", "decision": "string", "rationale": "string",
    "ruled_out": false }
]
```
Key decisions **and** their rationale, including **ruled-out dead-ends** (`ruled_out: true`). The
ruled-out set is what stops a resumed agent from re-exploring failed paths — a primary cause of poor
naive recovery.

### `effects_ref` — *(layer 2: irreversible effects, by reference)*
```jsonc
"effects_ref": { "ledger_id": "string", "offset": 1234 }
```
A pointer into the Runtime's append-only effect ledger (the ledger itself is Runtime-owned; the cairn
only references the offset valid at write time). Consumed by the
[effect-safety protocol](effect-safety-protocol.md).

### `world` — *(layer 1: durable external, by reference + digest)*
```jsonc
"world": {
  "snapshot_id": "string",                 // Runtime workspace snapshot
  "digest": { "src/app.py": "sha256:…" }   // salient files → content hash
}
```
A pointer to the workspace snapshot plus a digest of salient files, so the resumed agent knows the state
of the world without re-reading everything, and can detect drift (torn writes).

### `verification` — *(layer 3/1)*
```jsonc
"verification": [
  { "target": "tests/unit", "result": "pass | fail | unknown", "at_step": 42 }
]
```
What has been verified and the outcome — so the agent neither re-verifies needlessly nor trusts stale
results.

### `provenance` — metadata
```jsonc
"provenance": {
  "model_version": "string", "harness_version": "string",
  "step_index": 47, "created_at": "<stamped by Runtime>",
  "schema_version": "1.0"
}
```
Enables fidelity analysis and **cross-version resume** (claim C4): the resuming agent knows what produced
the cairn. `created_at` is stamped by the Runtime at persist time (the Code Harness does not invent
timestamps).

## 3. Elastic tail — *(layer 3: recent working memory)*

```jsonc
"elastic_tail": {
  "recent_steps": [ { "step": 46, "summary": "string" } ],
  "scratch": "string|null"
}
```
Recent raw working detail. **Online compaction may prune it freely**; a **checkpoint freezes it** at the
moment of writing. It is never relied upon for sufficiency — the durable core alone must suffice.

## 4. The core / tail boundary rule

> A field belongs in the **durable core** iff losing it would break continuation equivalence (it is part
> of the sufficient statistic `S`). Everything else is **elastic tail**.

This rule is what makes one object safe for both write paths: compaction prunes only the tail; the core
is invariant. See [unified-distillation.md](unified-distillation.md) and
[ADR-0005](../adr/ADR-0005-unified-distillation.md).

## 5. Versioning

- `schema_version` is mandatory and semver-like.
- **Readers tolerate unknown fields** (forward-compatible) and **supply documented defaults for missing
  optional fields** (backward-compatible).
- A breaking change bumps the major version and is recorded in an ADR.

## 6. Worked example (debugging task, failure at step 47)

```jsonc
{
  "schema_version": "1.0",
  "durable_core": {
    "intent": { "root_goal": "Fix the failing checkout test",
                "active_subgoal": "Patch the race in inventory.reserve()" },
    "plan": { "steps": [
      { "id": "s1", "description": "Reproduce the failure", "status": "done", "depends_on": [] },
      { "id": "s2", "description": "Localize the bug", "status": "done", "depends_on": ["s1"] },
      { "id": "s3", "description": "Patch inventory.reserve()", "status": "pending", "depends_on": ["s2"] },
      { "id": "s4", "description": "Re-run the suite", "status": "pending", "depends_on": ["s3"] }
    ]},
    "decisions": [
      { "id": "d1", "decision": "Bug is a race in reserve(), not a stale cache",
        "rationale": "Fails only under concurrent checkout; cache disabled still fails", "ruled_out": false },
      { "id": "d2", "decision": "Not a serializer bug", "rationale": "Ruled out — payloads identical across runs",
        "ruled_out": true }
    ],
    "effects_ref": { "ledger_id": "run-9f3a", "offset": 0 },
    "world": { "snapshot_id": "snap-47", "digest": { "src/inventory.py": "sha256:1c9…", "tests/test_checkout.py": "sha256:a40…" } },
    "verification": [ { "target": "tests/test_checkout.py", "result": "fail", "at_step": 12 } ],
    "provenance": { "model_version": "claude-opus-4-8", "harness_version": "cairn-0.x",
                    "step_index": 47, "created_at": "<runtime-stamped>", "schema_version": "1.0" }
  },
  "elastic_tail": {
    "recent_steps": [ { "step": 46, "summary": "Added a failing assertion narrowing the race window" } ],
    "scratch": null
  }
}
```

A resumed agent reading this knows the goal, that s1–s2 are done and s3 is next, that the race hypothesis
is confirmed and the serializer path is a dead end, which files matter, that no irreversible effects have
fired (`offset 0`), and that the suite last failed — enough to continue without restarting.

## Summary

The Continuation State is a typed object with a sufficient **durable core** (intent, plan, decisions incl.
dead-ends, effect/world pointers, verification, provenance) and a prunable **elastic tail**. Each field
traces to a state-taxonomy layer; the core/tail rule makes the object dual-purpose for compaction and
checkpointing.
