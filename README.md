<div align="center">

# Cairn

**Recoverable long-horizon agents.**

*Agents should survive failure the way good engineers do — by remembering what they were doing,
checking what actually happened, and continuing — not by starting over.*

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Phase%204%3A%20Recovery%20v1%20complete-brightgreen.svg)](ROADMAP.md)
[![Tests](https://img.shields.io/badge/tests-32%20passing-brightgreen.svg)](tests/)

</div>

---

## What is Cairn?

Cairn is an open, framework-agnostic **reference implementation and benchmark for recoverable
long-horizon agents**. When an autonomous agent fails at step 47, today it usually starts over.
Cairn makes recovery a first-class, *measurable* property:

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

## What Cairn is — and is not

| Cairn **is** | Cairn **is not** |
|---|---|
| A specification (the Continuation State + boundary contract) | A production agent framework |
| A minimal reference implementation | A model |
| A failure-injection benchmark | A general workflow orchestrator |

Cairn **complements** agent frameworks (OpenHands, LangGraph, custom harnesses) rather than replacing them.

## Project status

**Phase 4 — Recovery v1: complete (on branch).** The three recovery pillars now work end-to-end: a single
**unified distillation** writes the cairn for both compaction and checkpointing, **re-grounding resume**
recovers from a crash (load → re-observe → reconcile → re-plan → continue), and **effect-safety** stops a
resumed agent re-firing an irreversible effect. An injected-failure demo recovers a task with **no
duplicate effect** and a recovery tax far below a cold restart. **32 passing tests.** Phases 0–4 done;
**Phase 5 — Evaluation & Benchmark** is next. See the [Roadmap](ROADMAP.md), the
[Master Checklist](CHECKLIST.md), and live state under [`project/`](project/).

```bash
python -m pytest -q             # 32 passing
python examples/quickstart.py   # end-to-end baseline task
python examples/recovery_demo.py # crash mid-task, then recover via re-grounding
```

The harness is **never hardcoded** (ADR-0007): model provider, tools, tasks, sandbox, storage, and
policies are all injected through [`cairn.app.build_harness`](src/cairn/app.py). The concrete task and
scripted model live only in [`examples/`](examples/) and [`tests/`](tests/), never in the library.

## Repository map

| Path | Purpose |
|---|---|
| [`ROADMAP.md`](ROADMAP.md) | The 7-phase project spine |
| [`CHECKLIST.md`](CHECKLIST.md) | Master checklist (always-visible status) |
| [`docs/`](docs/) | **Knowledge** — vision, concepts, governance rules, research, design |
| [`docs/governance/`](docs/governance/) | How we work: documentation policy, AP workflow, phase process |
| [`docs/design/`](docs/design/) | **Specs** — Continuation State schema, boundary contract, resume protocol, effect-safety |
| [`project/`](project/) | **Live state** — phases, Action Points, tracking, templates |
| [`src/cairn/`](src/cairn/) | The harness: `state`, `contract`, `runtime/` (sandbox, snapshot, ledger, checkpoint, digest), `harness/` (loop, distill, reconcile, effects, resume), `tasks/`, `app` |
| [`examples/`](examples/), [`tests/`](tests/) | Quickstart + recovery demo + suite (32 tests) |
| `benchmarks/` | Empty until Phase 5 (failure-injection eval) |

## How we work

Cairn is **documentation-first**, **Action-Point (AP) driven**, and **phase-based**. Nothing is
"done" until its documentation is updated. See [`docs/governance/`](docs/governance/).

## License

[Apache-2.0](LICENSE).
