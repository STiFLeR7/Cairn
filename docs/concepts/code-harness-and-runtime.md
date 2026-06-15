---
title: The Two-Layer Model — Code Harness and Agent Runtime Harness
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0010]
related_adrs: [ADR-0001]
---

# The Two-Layer Model

Autonomy does not come from a powerful model alone. It emerges from the combination of **how the agent
thinks and acts** and **where it lives and operates**. Cairn names these two layers and the rule that
relates them.

- **Code Harness** — the layer where *code is the medium* for planning, reasoning, tool use, state, and
  verification. The agent **decides**.
- **Agent Runtime Harness** — the environment that *sustains* the agent: workspace, memory, artifacts,
  execution, recovery, permissions, observability. The agent **lives** here.

## 1. Code Harness — the agent decides

In a Code Harness the model does not merely *select* a tool; it *writes a program* that composes tools,
holds state in variables, branches and loops, and verifies results by execution.

```python
# Tool-calling: the model selects one action and waits.
{ "tool": "search", "arguments": { "query": "..." } }

# Code Harness: the model constructs a workflow.
results  = search(query)
top      = filter_results(results)
summary  = summarize(top)
if not good_enough(summary):
    summary = expand(summary)
return summary
```

Code becomes the **action language**: the planner, the workflow, the state container, and the
orchestration layer at once. Loops, retries, conditionals, and composition emerge naturally instead of
being externally orchestrated. Systems built on this idea include Claude Code, OpenHands, smolagents'
`CodeAgent`, and Codex-style software-engineering agents.

**Owns:** reasoning, planning, tool orchestration, working state (variables), verification, workflow
construction.

## 2. Agent Runtime Harness — the agent lives here

The Runtime owns everything required to *sustain* long-running autonomous behavior:

- **Workspace** — persistent working directories that survive across steps and sessions.
- **Memory** — durable record of past actions, plans, failures, successes, decisions.
- **Artifacts** — `plan.md`, `results.json`, logs — outputs that outlive a session.
- **Execution** — terminal, filesystem, tool access, sandboxing.
- **Recovery** — checkpoints and resume, so failure does not mean restart.
- **Permissions** — what may be read, written, run, or reached over the network.
- **Observability** — actions, decisions, logs, metrics.

**Owns:** workspace, memory, artifacts, execution substrate, recovery mechanism, permissions,
observability.

## 3. The organizing rule: one concern, two altitudes

The two layers appear to share words — both seem to have "memory," "execution," "recovery," "planning."
They do not duplicate these; **they split each concern by scope.** This is the load-bearing rule of the
whole framework:

> **The Code Harness decides; the Runtime sustains. Wherever they share a word, it is the same concern
> at two altitudes — a *logical/transient* facet owned by the Code Harness, and a *physical/durable*
> facet owned by the Runtime.**

| Concern | Code Harness (logical / transient) | Runtime (physical / durable) |
|---|---|---|
| **Memory** | working state in variables, in-context | cross-session durable store |
| **Execution** | *what* to run — the program it constructs | *where* it runs — sandbox, terminal, filesystem |
| **Recovery** | retry / repair logic (`if failed: repair()`) | checkpoint + resume after crash |
| **Planning** | the live reasoning steps | persisted plan artifacts across sessions |

Read the framework through this rule and the apparent redundancy disappears: every shared term is one
idea cut cleanly at the boundary.

## 4. Topology: logically above, physically inside

Is the Code Harness *above* the Runtime (an orchestrator that calls down into runtime services) or
*inside* it (a guest process the Runtime hosts)? Both — and resolving this prevents the diagrams from
contradicting one another:

> **Control flows down; code runs within.** The Code Harness is **logically above** the Runtime — it
> directs the Runtime's services. The generated code is **physically inside** the Runtime — it executes
> within the Runtime's sandbox. The agent is the guest process that is also giving the orders.

```
        User Goal
            │
        Foundation Model        ← intelligence
            │
        Code Harness            ← decides: reasoning, planning, workflow   (logically above)
            │  directs ▼   ▲ observes
        Agent Runtime Harness   ← sustains: workspace, memory, execution,  (physically contains
            │                     recovery, permissions, observability       the running code)
   ┌────────┼─────────┬───────────┐
Workspace  Memory  Execution   Recovery
            │
        Observation ──► next action (back up to the Code Harness)
```

The developer analogy makes it intuitive: the developer (Code Harness) decides what to build and how,
but still sits **inside** the environment they command — OS, IDE, shell, VCS, CI (the Runtime).

## 5. Why both — and why recovery is the proof

Each layer alone is incomplete:

- **Code-only** systems are *smart but fragile*: flexible reasoning, but weak persistence and recovery,
  and workspace management is often missing.
- **Runtime-only** systems are *stable but rigid*: durable and secure, but they fall back on rigid tool
  calls and lose planning flexibility.

Combined, they are smart **and** stable **and** persistent **and** autonomous. The sharpest demonstration
that this split is *real* (not cosmetic) is **recovery**, which cannot be done well by either layer
alone — see [recovery-in-the-two-layer-model.md](recovery-in-the-two-layer-model.md).

## Summary

Cairn rests on two layers — the Code Harness (decides) and the Agent Runtime Harness (sustains) — related
by one rule: *shared concerns are split by scope, not duplicated.* The Code Harness is logically above
the Runtime but physically inside its sandbox. The next document shows why recovery is the canonical
case that requires both.
