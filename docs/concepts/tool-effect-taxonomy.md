---
title: Tool Effect Taxonomy
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0012]
related_adrs: [ADR-0001]
---

# Tool Effect Taxonomy

Layer 2 of the [state taxonomy](state-taxonomy.md) — **irreversible effects** — is the danger zone for
recovery: on resume, the agent must not re-execute an action that already changed the world. Whether that
is *possible to guarantee* depends on the tool. This taxonomy classifies tools by reversibility /
idempotency and assigns each class a recovery policy. It feeds the effect-safety write-ahead protocol
(`AP-0017`).

## The danger window

Effects are unsafe precisely in the window between the last checkpoint and the failure. If the agent
crashed just after calling a tool but before recording the result, resume must decide: **did this already
happen, and may I do it again?** The answer depends on the tool's class.

## The three classes

| Class | Definition | Recovery policy on resume | Examples |
|---|---|---|---|
| **`safe-to-retry`** | Pure or naturally idempotent — re-executing has no additional effect | **Just redo.** No bookkeeping required. | read a file, `GET` a resource, `PUT` to a fixed key, recompute a deterministic value, `mkdir -p` |
| **`check-before-retry`** | Has an idempotency key or a queryable external state — you can ask "did this happen?" | **Verify, then redo-or-skip.** Use the idempotency key / query the world before acting. | send a payment with an idempotency key, create a resource with a client-supplied id, open a PR (queryable by branch), enqueue with a dedupe id |
| **`never-retry`** | Non-idempotent **and** unqueryable — you cannot tell whether it happened and repeating it is harmful | **Do not auto-retry. Escalate** to a human / hard-block, or require a wrapping that promotes it to `check-before-retry`. | fire-and-forget notification with no id, an external action with no receipt, a side effect on a system you cannot read back |

## The write-ahead discipline (forward reference, `AP-0017`)

To make `check-before-retry` safe, effects follow a write-ahead protocol against the Runtime's append-only
**effect ledger**:

```
1. log INTENT(action, idempotency_key)      # before doing anything
2. execute the effect
3. log COMPLETE(idempotency_key)            # after success
```

On resume, any **`INTENT` without a matching `COMPLETE`** marks the danger window. The agent then applies
the class policy: `safe-to-retry` → redo; `check-before-retry` → query/idempotency-key then redo-or-skip;
`never-retry` → escalate. This is what turns effect-safety from a hope into a procedure, and it is the
mechanism behind the **effect-safety** fidelity axis (see [recovery-fidelity.md](recovery-fidelity.md))
and claim **C3** ([claims registry](../research/claims-registry.md)).

## Honest scope limit

Effect-safety **cannot be universally guaranteed**: `never-retry` tools exist, and no protocol can read a
world that offers no receipt. Cairn's position is explicit about this — such tools are escalated to a
human or must be wrapped to become queryable. Pretending otherwise would be the kind of silent gap the
project is built to avoid.

## Summary

Tools split into three recovery classes — `safe-to-retry`, `check-before-retry`, `never-retry` — each
with a definite resume policy. A write-ahead `INTENT`/`COMPLETE` ledger makes the first two safe; the
third is an acknowledged limit handled by escalation. This taxonomy is the semantic basis for the
effect-safety protocol designed in Phase 2.
