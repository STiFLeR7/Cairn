<div align="center">

# Cairn

**Recoverable long-horizon agents.**

*Agents should survive failure the way good engineers do — by remembering what they were doing,
checking what actually happened, and continuing — not by starting over.*

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-P1--P4%20evidence%20current-brightgreen.svg)](ROADMAP.md)
[![Tests](https://img.shields.io/badge/tests-P4%20controls%20verified-brightgreen.svg)](tests/)
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
- A narrowly admitted **receipt/reconciliation** semantics: re-observe before retry, then retry,
  skip, or escalate from durable evidence. It is not an exactly-once guarantee.

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
python examples/byom_recovery.py     # primitives + Agent loop (offline, mock model)
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

**Recovery proof ladder P1–P5: complete, narrowly. P6 is kit-ready, not admitted.** The existing BYOM library
remains 0.x and experimental. The evidence-backed claims are the three narrow contracts below, not a
claim that Cairn makes arbitrary agents reliable or provides exactly-once external effects.

| Proof phase | Admitted result | Evidence boundary |
|---|---|---|
| **P1 — crash/restart** | Repository recovery fidelity in the deterministic reference harness | [RecoveryBench report](results/phase-1/REPORT.md) |
| **P2 — compaction continuity** | [Continuation Contract v0](docs/design/continuation-contract-v0.md) | P2.4: 40 eligible U/R/C cells across Claude Code Opus/Sonnet; 20 pre-continuation Sonnet acquisition failures are retained, not counted as recovery successes ([verdict](results/phase-2/p24-verdict.json)) |
| **P3 — external effects** | [Receipt/Reconciliation Contract v0](docs/design/receipt-reconciliation-contract-v0.md) | One deterministic create-once provider effect: 36 reference and 15 sealed-holdout cells; no duplicate or silent-loss cells. The holdout reused the provider/harness, so this is not independent-provider validation ([verdict](results/phase-3/p3-verdict.json)) |
| **P4 — external host** | [Claude Code integration proof](docs/design/phase-4-claude-code-integration.md) | One Claude Code host/provider proof. V5 gives the shared-checkpoint/effect reference control; V6 adds a post-compaction causal negative and independently sealed generic U/R/C holdout ([admission verdict](results/phase-4/reconstitution-v6/verdict.json)). |
| **P5 — second host portability** | Two-host portability evidence | Claude Code’s admitted P4 evidence and OpenHands SDK 1.42.1’s sealed reference plus independent holdout passed the same host-neutral recovery/effect criteria ([verdict](results/phase-5/two-host-portability-verdict.json)). This is deterministic two-host evidence, not universal compatibility or a standard. |
| **P6 — independent conformance** | [Conformance Kit v0](conformance/v0/README.md) | Copy-isolated host-neutral evaluator and evidence profile are published ([kit verdict](results/phase-6/kit-verdict.json)). An external runtime passed its public control but failed its sealed holdout/reproducer gate because it could not consume a sealed workload ([stopped verdict](results/phase-6/external-independent-runtime-v1/)). No independent implementation or sealed holdout has passed; this is not an interoperability claim. |

P2 requires a fresh process without the original transcript and is conditioned on acquiring a clean,
verified checkpoint. P3 requires re-observation before a retry and admits only the decision semantics
proven for its reference effect: absent → retry; matching present → skip; unknown, mismatch, and
never-retry → escalate. Neither contract establishes broad live-model performance, a framework API,
or general external-effect delivery. P4 admits one host integration only; it does not expand either v0
contract. P5 adds only deterministic two-host portability evidence; it does not establish universal
compatibility, a host-native Cairn integration, exactly-once delivery, or an ecosystem standard. P6
publishes a conformance kit only; it does not yet add an independently implemented third host.

The journey so far:

| Stage | What happened | Outcome |
|---|---|---|
| **Legacy phases 0–6** | Specify, build, and *measure* recovery in a deterministic reference harness | 🟢 Historical mechanism and benchmark work; see the proof ladder above for the currently admitted P1–P4 boundaries |
| **M1–M3** | Run the benchmark against **real LLMs** to confirm the headline claim (C1) | 🟢 Live pipeline works; RGR looks strong — but **NO-GO** for v1.0: evidence is *suggestive, not confirmed* (free-tier rate limits + underpowered runs) |
| **M4** | Ship the recovery mechanism as a **BYOM library** so anyone can reproduce C1 on their own model | 🟢 **Complete** — mechanism shipped; stays 0.x |

**Honest scope ([ADR-0009](docs/adr/ADR-0009-evaluation-framework.md)).** The legacy live C1 claim remains
suggestive rather than confirmed. P1–P4 establish narrowly scoped recovery semantics and one external-host
integration proof in the recorded
reference and sealed-holdout experiments; they do not change the v1.0 or broad live-performance gate.
See the [Roadmap](ROADMAP.md), [Master Checklist](CHECKLIST.md), and
[claims registry](docs/research/claims-registry.md).

```bash
python -m pytest -q                  # current full suite
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
| [`docs/design/`](docs/design/) | **Specs and admitted contracts** — state/boundary/resume designs plus Continuation Contract v0 and Receipt/Reconciliation Contract v0 |
| [`project/`](project/) | **Live state** — phases, Action Points, tracking, templates |
| [`src/cairn/`](src/cairn/) | The library: `contract` (public Protocols), `recovery` (`checkpoint`/`recover`), `agent` (opt-in loop), `worlds/` (`Workspace`), `runtime/`, `harness/` (loop, distill, reconcile, effects), `eval/`, `tasks/`, `app` |
| [`benchmarks/`](benchmarks/) | Runnable studies — recovery matrix, ablation, cross-version, live-pipeline |
| [`examples/`](examples/), [`tests/`](tests/) | Quickstart + BYOM + recovery demos + the current full suite |

## How we work

Cairn is **documentation-first**, **Action-Point (AP) driven**, and **phase/milestone-based**. Nothing is
"done" until its documentation is updated; each phase/milestone lands on its own branch and reaches
`master` only via PR. See [`docs/governance/`](docs/governance/) and [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

[Apache-2.0](LICENSE).
