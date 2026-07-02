<div align="center">

# Cairn

**Recoverable long-horizon agents.**

*Agents should survive failure the way good engineers do — by remembering what they were doing,
checking what actually happened, and continuing — not by starting over.*

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-M4%3A%20BYOM%20recovery%20library%20complete-brightgreen.svg)](ROADMAP.md)
[![Tests](https://img.shields.io/badge/tests-141%20passing-brightgreen.svg)](tests/)
[![Version](https://img.shields.io/badge/version-0.x%20(v1.0%20held)-orange.svg)](CHANGELOG.md)

</div>

---

## What is Cairn?

Cairn is an open, framework-agnostic **recovery library, reference implementation, and benchmark for
recoverable long-horizon agents**. When an autonomous agent fails at step 47, today it usually starts
over. Cairn makes recovery a first-class, *measurable* property built on three pillars:

- A durable, typed **Continuation State** (a "cairn" — a marker dropped on the trail) that doubles
  as the agent's working memory *and* its recovery checkpoint.
- A **Re-grounding Recovery (RGR)** protocol that restores situational awareness after context loss
  *without* faithful replay.
- **Effect-safety** guarantees that stop a resumed agent from re-acting on the world
  (re-sending an email, re-opening a PR).

> A cairn is a small stack of stones hikers leave to re-find a route after losing the trail.
> That is exactly what a checkpoint is: a minimal, durable marker left behind on purpose.

## The thesis

**Checkpoints Are Compactions.** Long-horizon agents already recover from context loss constantly —
every time they compact an overflowing context window. A checkpoint is just a compaction you can roll
back to. Cairn builds *one* distillation mechanism that serves both.

## Add recovery to your own agent (BYOM)

Cairn is **bring-your-own-model**: keep your model, keys, and tools; Cairn adds crash-recovery. Bring a
`World` (the bundled `Workspace`, or your own) and either call the primitives yourself or use the opt-in
`Agent` loop:

```python
from cairn import Agent, Workspace, FileCheckpointStore, FileEffectLedger

agent = Agent(your_model, Workspace("ws", "snaps"),
              store=FileCheckpointStore("ck"),
              ledger=FileEffectLedger("effects.jsonl", "run"))

run = agent.run(goal)        # checkpoints every executed step
# ... process crashes ...
run = agent.resume(goal)     # re-grounds from the last checkpoint and continues
print(run.resumed, run.recovery_tax, run.finished)
```

Prefer to keep your own loop? Use the `checkpoint()` / `recover()` primitives directly. Full walkthrough:
the **[BYOM guide](docs/guide/recovery-in-your-agent.md)** and the **[public API reference](docs/guide/public-api-reference.md)**.

```bash
python examples/byom_recovery.py     # primitives + Agent loop + exactly-once effect (offline, mock model)
```

## What Cairn is — and is not

| Cairn **is** | Cairn **is not** |
|---|---|
| A bring-your-own-model recovery library | A production agent framework |
| A specification (the Continuation State + boundary contract) | A model |
| A minimal reference implementation | A general workflow orchestrator |
| A failure-injection benchmark | A hosted service |

Cairn **complements** agent frameworks (OpenHands, LangGraph, custom harnesses) rather than replacing them.

## Project status

**Milestone M4 — BYOM Recovery Library: complete & merged.** Cairn's recovery mechanism now ships as a
clean, documented public API a developer drops into their own agent — public `checkpoint()`/`recover()`
primitives, an opt-in `Agent` loop, pluggable `World`/`CheckpointStore`/`EffectLedger` contracts, a
runnable offline example, a guide + API reference, and CI. **141 passing tests.** The public surface is
locked by a contract test; the project stays **0.x**.

The journey so far:

| Stage | What happened | Outcome |
|---|---|---|
| **Phases 0–6** | Specify, build, and *measure* recovery in a deterministic reference harness | 🟢 In-harness, **RGR beats cold restart** (recovery tax 1.5 vs 5.0; all pre-failure work preserved) and the **effect-safety WAL yields zero duplicate effects** |
| **M1–M3** | Run the benchmark against **real LLMs** to confirm the headline claim (C1) | 🟢 Live pipeline works; RGR looks strong — but **NO-GO** for v1.0: evidence is *suggestive, not confirmed* (free-tier rate limits + underpowered runs) |
| **M4** | Ship the recovery mechanism as a **BYOM library** so anyone can reproduce C1 on their own model | 🟢 **Complete** — mechanism shipped; stays 0.x |

**Honest scope ([ADR-0009](docs/adr/ADR-0009-evaluation-framework.md)).** The in-harness results establish
that the *mechanisms* behave as designed and are reproducible. The headline live claim — *RGR beats cold
restart on a real model* (C1) — is **suggestive but not yet confirmed**; a **powered** live study on a
paid/reliable API is the remaining gate. Cairn therefore stays **0.x**: no v1.0 tag, no PyPI publish, and
no announcement until that evidence exists. See the [Roadmap](ROADMAP.md), the
[Master Checklist](CHECKLIST.md), and the [claims registry](docs/research/claims-registry.md).

```bash
python -m pytest -q                  # 141 passing
python examples/byom_recovery.py     # BYOM: add crash-recovery to YOUR agent (offline, mock model)
python examples/recovery_demo.py     # crash mid-task, then recover via re-grounding
python benchmarks/recovery_matrix.py # the baseline × failure-step benchmark (C1, C3)
```

The harness is **never hardcoded** (ADR-0007): model provider, tools, tasks, sandbox, storage, and
policies are all injected. The concrete task and scripted model live only in
[`examples/`](examples/) and [`tests/`](tests/), never in the library.

## Repository map

| Path | Purpose |
|---|---|
| [`PAPER.md`](PAPER.md) | The research write-up ("Checkpoints Are Compactions") |
| [`REPRODUCE.md`](REPRODUCE.md) | One-command reproduction of the tests, demo, and benchmarks |
| [`ROADMAP.md`](ROADMAP.md) | The 7-phase spine + post-phase milestones (M1–M4) |
| [`CHECKLIST.md`](CHECKLIST.md) | Master checklist (always-visible status) |
| [`CHANGELOG.md`](CHANGELOG.md) | Notable changes (Keep a Changelog) |
| [`docs/guide/`](docs/guide/) | **Using Cairn** — BYOM recovery guide + public API reference |
| [`docs/`](docs/) | **Knowledge** — vision, concepts, governance rules, research, design, ADRs |
| [`docs/design/`](docs/design/) | **Specs** — Continuation State schema, boundary contract, resume protocol, effect-safety |
| [`project/`](project/) | **Live state** — phases, Action Points, tracking, templates |
| [`src/cairn/`](src/cairn/) | The library: `contract` (public Protocols), `recovery` (`checkpoint`/`recover`), `agent` (opt-in loop), `worlds/` (`Workspace`), `runtime/`, `harness/` (loop, distill, reconcile, effects), `eval/`, `tasks/`, `app` |
| [`benchmarks/`](benchmarks/) | Runnable studies — recovery matrix, ablation, cross-version, live-pipeline |
| [`examples/`](examples/), [`tests/`](tests/) | Quickstart + BYOM + recovery demos + the suite (141 tests) |

## How we work

Cairn is **documentation-first**, **Action-Point (AP) driven**, and **phase/milestone-based**. Nothing is
"done" until its documentation is updated; each phase/milestone lands on its own branch and reaches
`master` only via PR. See [`docs/governance/`](docs/governance/) and [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

[Apache-2.0](LICENSE).
