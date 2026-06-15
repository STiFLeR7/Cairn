<div align="center">

# Cairn

**Recoverable long-horizon agents.**

*Agents should survive failure the way good engineers do — by remembering what they were doing,
checking what actually happened, and continuing — not by starting over.*

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Phase%205%3A%20Evaluation%20complete-brightgreen.svg)](ROADMAP.md)
[![Tests](https://img.shields.io/badge/tests-42%20passing-brightgreen.svg)](tests/)

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

**Phase 5 — Evaluation & Benchmark: complete (on branch).** Recovery is now *measured*, not just
demonstrated. A failure-injection benchmark runs the four baselines (B0 cold-restart, B1 log-replay, B2
snapshot-only, B3 RGR) across the failure-step matrix and scores five fidelity axes against the
uninterrupted run. In the deterministic reference harness, **RGR beats cold restart** (recovery tax 1.5 vs
5.0 steps; preserves all pre-failure work) and the **effect-safety WAL yields zero duplicate effects** vs
one without it; an ablation locates the *plan* as the minimal sufficient state. **42 passing tests.**
Phases 0–5 done; **Phase 6 — Paper & Release** is next. Results are honestly scoped (reference harness, not
a live-LLM study — [ADR-0009](docs/adr/ADR-0009-evaluation-framework.md)). See the [Roadmap](ROADMAP.md),
the [Master Checklist](CHECKLIST.md), and the [claims registry](docs/research/claims-registry.md).

```bash
python -m pytest -q                  # 42 passing
python examples/recovery_demo.py     # crash mid-task, then recover via re-grounding
python benchmarks/recovery_matrix.py # the baseline×failure-step benchmark (C1, C3)
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
| [`src/cairn/`](src/cairn/) | The harness: `state`, `contract`, `runtime/` (sandbox, snapshot, ledger, checkpoint, digest), `harness/` (loop, distill, reconcile, effects, resume), `eval/` (failure, baselines, metrics, ablation, runner), `tasks/`, `app` |
| [`benchmarks/`](benchmarks/) | Concrete benchmark scenarios + runnable studies (recovery matrix, ablation, cross-version) |
| [`examples/`](examples/), [`tests/`](tests/) | Quickstart + recovery demo + suite (42 tests) |
| `benchmarks/` | Empty until Phase 5 (failure-injection eval) |

## How we work

Cairn is **documentation-first**, **Action-Point (AP) driven**, and **phase-based**. Nothing is
"done" until its documentation is updated. See [`docs/governance/`](docs/governance/).

## License

[Apache-2.0](LICENSE).
