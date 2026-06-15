---
title: Glossary
status: active
last_updated: 2026-06-15
owner: maintainers
related_aps: [AP-0002, AP-0004]
related_adrs: [ADR-0001]
---

# Glossary

Canonical definitions. Other docs link here rather than re-defining terms.

| Term | Definition |
|---|---|
| **Cairn (the project)** | This project: a reference implementation and benchmark for recoverable long-horizon agents. |
| **cairn (the artifact)** | A dropped marker — an instance of the **Continuation State** persisted on the trail so the agent can re-find its way. |
| **Continuation State** | The typed, durable object capturing the minimal sufficient state for an agent to continue a task. Has a *durable core* and an *elastic tail*. |
| **Re-grounding Recovery (RGR)** | The recovery method: restore situational awareness by re-observing the world and re-grounding from the Continuation State, rather than replaying the trajectory. |
| **"Checkpoints Are Compactions"** | The project thesis: context compaction and crash-recovery checkpointing are the same operation at different timescales, served by one distillation mechanism. |
| **Code Harness** | The layer where code is the medium for planning, reasoning, tool use, state, and verification — the agent *decides*. |
| **Agent Runtime Harness** | The environment that sustains the agent: workspace, memory, artifacts, execution, recovery, permissions, observability — the agent *lives* here. |
| **Boundary contract** | The interface between Code Harness and Runtime (checkpoint/load, effect ledger, workspace snapshot, observation). |
| **Effect ledger** | Append-only, write-ahead log of irreversible external actions, used for effect-safety on resume. |
| **Effect-safety** | The guarantee that a resumed agent does not re-execute irreversible external actions. |
| **Recovery fidelity** | How well a resumed agent matches an uninterrupted run, measured by outcome equivalence (success, quality, no regression, effect-safety, recovery tax). |
| **Re-grounding** | Re-establishing situational awareness after context loss by re-observing and reconciling against the Continuation State. |
| **Action Point (AP)** | The unit of meaningful change. See [AP workflow](ap-workflow.md). |
| **Phase** | A bounded stage of the project with a goal and completion criteria. See [phase process](phase-process.md). |
