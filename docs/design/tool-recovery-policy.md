---
title: Tool → Recovery-Policy Mapping
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0018]
related_adrs: [ADR-0006]
---

# Tool → Recovery-Policy Mapping

Operationalizes the [tool-effect taxonomy](../concepts/tool-effect-taxonomy.md): how a tool is *declared*
to a recovery class, the exact resume policy each class runs, how tools are *promoted* to a safer class,
and the conservative default for undeclared tools. It parameterizes the
[effect-safety protocol](effect-safety-protocol.md) ([ADR-0006](../adr/ADR-0006-effect-safety-wal.md)).

## 1. Tool declaration schema

Every tool capable of an irreversible effect declares:

```jsonc
{
  "name": "send_email",
  "class": "safe-to-retry | check-before-retry | never-retry",
  "idempotency_key": "fn(args) -> string | null",   // how to derive a stable key
  "verify_hook": "fn(key) -> happened? | null"       // how to ask the world "did this run?"
}
```

- `safe-to-retry`: `idempotency_key` and `verify_hook` optional (redo is harmless).
- `check-before-retry`: **requires** at least one of `idempotency_key` or `verify_hook`.
- `never-retry`: neither available.

## 2. Per-class resume policy (operational)

Applied to each `INTENT`-without-`COMPLETE` key during
[resume reconciliation](resume-protocol.md):

| Class | Policy | Uses |
|---|---|---|
| `safe-to-retry` | re-invoke the tool; write COMPLETE | — |
| `check-before-retry` | call `verify_hook(key)` (or re-invoke with `idempotency_key` so the provider dedupes); if it already happened → skip + write COMPLETE; else redo + COMPLETE | `verify_hook` / `idempotency_key` |
| `never-retry` | **escalate**: surface to a human / block continuation; do not auto-execute | escalation channel |

## 3. Promotion (wrapping) rules

A tool can be lifted to a safer class — strongly encouraged for anything irreversible:

- `never-retry` → `check-before-retry`: add an `idempotency_key` (so the provider dedupes) **or** a
  `verify_hook` (so resume can ask whether it happened).
- `check-before-retry` → `safe-to-retry`: only if re-execution is provably idempotent end-to-end.

Promotion is the project's recommended way to shrink the `never-retry` surface rather than accept
escalation.

## 4. Conservative default (fail-safe)

> **Any tool not declared, or declared with an effect but without a usable key/verify hook, is treated as
> `never-retry`.**

Unknown effects are assumed dangerous. This makes the safe path the default and forces effectful tools to
opt into retryability explicitly — preventing a silent duplicate-effect bug from an unclassified tool.

## 5. Consistency

This mapping is consistent with the effect-safety protocol (same three classes, same policies) and the
tool-effect taxonomy (same definitions). It supplies the `tool_class` recorded in each effect-ledger
record and the hooks the resume reconciliation invokes.

## Summary

Tools declare a recovery class plus optional idempotency-key / verify hooks. Resume runs a per-class
policy (redo / verify-then-redo-or-skip / escalate). Tools are promoted out of `never-retry` by adding a
key or verify hook, and **undeclared effectful tools default to `never-retry`** so the safe path is the
default.
