# Cairn v1.0.0 — release notes (DRAFT)

> **Draft, pending approval.** This documents the intended `v1.0.0` release. The tag and GitHub release
> are cut only on explicit human approval (AP-0036). On execution: bump `pyproject.toml` to `1.0.0`, set
> `CITATION.cff` `version`/`date-released`, move the `CHANGELOG` `Unreleased` section under `v1.0.0`, tag
> `v1.0.0`, and publish.

## Cairn v1.0.0 — Recoverable long-horizon agents

Cairn is a framework-agnostic **reference implementation and benchmark** for recoverable long-horizon AI
agents, built around the thesis **"Checkpoints Are Compactions."** v1.0.0 is the first complete cut: the
specification, a runnable reference harness with recovery, and a reproducible benchmark.

### Highlights

- **Continuation State** ("cairn") — a typed durable core (sufficient statistic) + prunable elastic tail.
- **Re-grounding Recovery (RGR)** — resume by load → re-observe → reconcile → re-plan → continue, surviving
  non-determinism where replay cannot.
- **Effect-safety write-ahead ledger** — eliminates duplicate irreversible effects for queryable tools;
  escalates the unqueryable ones.
- **Unified distillation** — one mechanism for context compaction *and* checkpointing.
- **Failure-injection benchmark** — four baselines (B0–B3), five fidelity axes, ablation, cross-version.
- **No hardcoded harness** — model, tools, tasks, sandbox, storage, policies all injected (ADR-0007).

### Results (deterministic reference harness — see scope)

- **C1 supported:** RGR beats cold restart (recovery tax 1.5 vs 5.0 steps; no-regression 1.0 vs 0.0).
- **C3 supported:** write-ahead ledger → 0 duplicate effects (gate PASS) vs 1 without (gate FAIL).
- **C5 supported:** ablation identifies `plan` as the minimal sufficient component (fidelity cliff).
- **C2 evidenced**, **C4 mechanism shown** (cross-version provenance).

### Scope & honesty

All v1.0.0 evidence is from a **deterministic scripted-mock harness**, establishing mechanism correctness
and reproducibility — **not** a live-LLM study. A live-LLM empirical study with statistical testing, and
faithfully-realized non-crash failure types, are the headline future work. See `PAPER.md` §9 and the
[claims registry](../research/claims-registry.md).

### Reproduce

```bash
make all        # or: python -m pytest -q && python examples/recovery_demo.py && python benchmarks/recovery_matrix.py
```
See [`REPRODUCE.md`](../../REPRODUCE.md). 42 tests; deterministic.

### Install / cite

- Apache-2.0. Python 3.12+, no third-party runtime dependencies.
- Cite via [`CITATION.cff`](../../CITATION.cff).

### Acknowledgements

Built in the open with rigorous AP/phase governance (Phases 0–6) and documentation-first discipline.
