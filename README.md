<div align="center">

# Cairn

**Recoverable long-horizon agents.**

*Agents should survive failure the way good engineers do — by remembering what they were doing,
checking what actually happened, and continuing — not by starting over.*

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Phase%203%3A%20Minimal%20Harness%20complete-brightgreen.svg)](ROADMAP.md)
[![Tests](https://img.shields.io/badge/tests-13%20passing-brightgreen.svg)](tests/)

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

**Phase 3 — Minimal Harness: complete & merged.** The substrate is runnable: a fully pluggable Code
Harness + Runtime that honors the Phase 2 boundary contract, with **13 passing tests** — but **no
recovery yet** (that is Phase 4). Phases 0–3 are done; **Phase 4 — Recovery v1** is next. See the
[Roadmap](ROADMAP.md), the [Master Checklist](CHECKLIST.md), and live state under [`project/`](project/).

```bash
python -m pytest -q          # 13 passing
python examples/quickstart.py # end-to-end baseline task
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
| [`src/cairn/`](src/cairn/) | The harness: `state`, `contract`, `runtime/`, `harness/`, `tasks/`, `app` |
| [`examples/`](examples/), [`tests/`](tests/) | Quickstart wiring + smoke suite (13 tests) |
| `benchmarks/` | Empty until Phase 5 (failure-injection eval) |

## How we work

Cairn is **documentation-first**, **Action-Point (AP) driven**, and **phase-based**. Nothing is
"done" until its documentation is updated. See [`docs/governance/`](docs/governance/).

## License

[Apache-2.0](LICENSE).
