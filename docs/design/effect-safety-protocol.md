---
title: Effect-Safety Write-Ahead Protocol
status: active
last_updated: 2026-09-01
owner: maintainers
related_aps: [AP-0017]
related_adrs: [ADR-0006]
---

# Effect-Safety Write-Ahead Protocol

Prevents a resumed agent from re-executing irreversible effects (taxonomy layer 2). It is the mechanism
behind the **effect-safety** fidelity axis and **claim C3**. It builds on the
[tool-effect taxonomy](../concepts/tool-effect-taxonomy.md) and the effect-ledger operations in the
[boundary contract](boundary-contract.md). See [ADR-0006](../adr/ADR-0006-effect-safety-wal.md).

## 1. The effect ledger

An append-only, Runtime-owned log. Each record:

```jsonc
{ "seq": 1234,                 // monotonic offset (contract I3)
  "type": "INTENT | COMPLETE",
  "action": "send_email#42",   // human/debug label
  "idempotency_key": "email-42",
  "tool_class": "check-before-retry",   // from the tool taxonomy (AP-0018)
  "step": 47,
  "timestamp": "<runtime-stamped>" }
```

## 2. Write-ahead sequence (normal operation)

Every irreversible effect follows INTENT → execute → COMPLETE:

```
1. append_effect(action, idempotency_key, tool_class)   # INTENT durable FIRST (invariant I1)
2. << execute the side effect >>
3. complete_effect(idempotency_key)                     # COMPLETE durable after success
```

Because INTENT is durable before the effect runs, a crash can never leave an executed effect
*unrecorded*. The cost is the opposite, recoverable, ambiguity: an INTENT with no COMPLETE.

## 3. Resume-time reconciliation

On resume, after `load_latest()` returns `(state, snap, offset)`:

```
records = list_effects_since(offset)
for each idempotency_key with an INTENT but no matching COMPLETE:   # the danger window
    apply the policy for its tool_class
```

The danger window is exactly the set of `INTENT`-without-`COMPLETE` keys between the last checkpoint and
the failure. For each, the policy is keyed to the tool class:

| Tool class | Resume policy |
|---|---|
| `safe-to-retry` | **Redo.** Idempotent/pure — re-executing is harmless. |
| `check-before-retry` | **Verify, then redo-or-skip.** Use the idempotency key or query the external world: if it already happened, skip and write COMPLETE; else redo. |
| `never-retry` | **Do not auto-retry. Escalate** to a human (or block) — the effect may or may not have happened and repeating it is harmful. |

After resolution, a COMPLETE is written so the key leaves the danger window.

## 4. Design intent and evidence boundary

For `check-before-retry` tools, the design requires an authoritative check (idempotency key / world query)
before any re-execution. That is the intended mechanism behind **claim C3**
([claims registry](../research/claims-registry.md)); it is not, by itself, an exactly-once delivery proof.

Phase 3 admitted the narrower [Receipt/Reconciliation Contract v0](receipt-reconciliation-contract-v0.md)
for one deterministic create-once provider effect: a fresh process re-observed before retry, retried only
when absent, skipped a matching present resource, and escalated unknown, mismatch, and never-retry cases.
The evidence is 36 reference and 15 sealed-holdout cells with no duplicate or silent-loss cells
([verdict](../../results/phase-3/p3-verdict.json)). The holdout reused the deterministic provider and
harness, so this document must not be read as independent-provider or general durable-effects validation.

## 5. Honest scope limit

`never-retry` tools (non-idempotent **and** unqueryable) **cannot** be made safe automatically — no
protocol can read a world that offers no receipt. The protocol's guarantee is therefore explicitly
*conditional on tool class*: it eliminates duplicates for `safe-to-retry` and `check-before-retry`, and
**escalates** `never-retry`. Tools can be **promoted** out of `never-retry` by adding an idempotency key /
verify hook (see [tool-recovery-policy.md](tool-recovery-policy.md)).

## Summary

Irreversible effects use a write-ahead INTENT/COMPLETE ledger. On resume, `INTENT`-without-`COMPLETE`
keys mark the danger window and are resolved by a per-tool-class policy (redo / verify-then-redo-or-skip /
escalate). This eliminates duplicate effects for the two safe classes (claim C3) and explicitly escalates
the unqueryable `never-retry` class.
