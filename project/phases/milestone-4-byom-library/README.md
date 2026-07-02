# Milestone M4 — BYOM Recovery Library

> **Status: 🟢 Complete (merged; in-repo, 0.x — ships nothing outward).**
> Branch(es): `milestone-4-byom-library` (AP-1–AP-3), `milestone-4-ap4-example-docs` (AP-4),
> `milestone-4-ap5-contract-polish` (AP-5). Master only via PR (#10, #11, + AP-5's PR).
> Entered 2026-06-29. Design: [`docs/superpowers/specs/2026-06-29-byom-recovery-library-design.md`](../../../docs/superpowers/specs/2026-06-29-byom-recovery-library-design.md).

## Why this milestone

M1–M3 established that Cairn's v1.0 gate is a *powered live study* the maintainer can't yet run on a
paid API (M3: strongest live signal yet, still **NO-GO**; the free-tier confounds are measurement
artifacts, not the mechanism failing). Rather than block on buying API access, M4 **heads Cairn
toward its actual strength** — the recovery *mechanism* — and ships it as a **bring-your-own-model
(BYOM) recovery library**: a clean, documented public API an outside developer drops into *their own*
agent, with *their own* model and keys. C1 validation then becomes something a **user** can reproduce
on their own model; Cairn ships the mechanism, not a dependency on us proving it on a paid model.

This does **not** lift the v1.0 hold and ships **nothing outward** (no PyPI, no release, no
announcement). It is a 0.x, in-repo milestone. Honest scope (ADR-0009): M4 does not claim C1 is
confirmed.

## Slices (superpowers spec→plan→execute; not the legacy AP-00XX numbering)

| Slice | Title | Status | Record |
|---|---|---|---|
| AP-1 | Split the contracts (`World`/`CheckpointStore`/`EffectLedger` Protocols; `LocalRuntime`/`Workspace` satisfy them) | 🟢 Done (PR #10) | design §4; suite green |
| AP-2 | Recovery primitives — public `checkpoint()`/`recover()` over the protocols + fake-World abstraction proof | 🟢 Done (PR #10) | `src/cairn/recovery.py`; `tests/test_recovery_primitives.py` |
| AP-3 | Opt-in `Agent` loop on the primitives + de-dup (`regrounded_history` single source) | 🟢 Done (PR #10) | `src/cairn/agent.py`; [plan](../../../docs/superpowers/plans/2026-06-29-byom-agent-loop-ap3.md) |
| AP-4 | Example (primitives + Agent + exactly-once effect) + guide + API reference + CI smoke | 🟢 Done (PR #11) | `examples/byom_recovery.py`; `docs/guide/`; [plan](../../../docs/superpowers/plans/2026-07-02-byom-example-and-docs-ap4.md) |
| AP-5 | Public-API contract lock + spec reconciliation + trackers/CHANGELOG | 🟢 Done (this PR) | `tests/test_public_api_contract.py`; design §12; [plan](../../../docs/superpowers/plans/2026-07-02-byom-contract-and-polish-ap5.md) |

## What shipped

- **Contracts (Layer 1):** `World` (`snapshot`/`restore`/`digest`; executable Worlds also `execute`),
  bundled `CheckpointStore` + `EffectLedger`, `EffectfulTool`. `LocalRuntime` satisfies all three so
  the **benchmark, eval baselines, and prior tests run unchanged** (the regression guard).
- **Primitives (Layer 2):** `checkpoint(...)` and `recover(...)` — the full RGR as public functions;
  proven world-agnostic by an in-memory `FakeWorld`.
- **Opt-in loop (Layer 3):** `Agent(model, world, *, store, ledger, ...)` with `.run()`/`.resume()`;
  proven world-agnostic by an in-memory `ExecFakeWorld`.
- **Reference world + infra:** `Workspace`, `FileCheckpointStore`, `FileEffectLedger`.
- **Developer surface:** runnable offline example, the "recovery in your own agent" guide, the public
  API reference, and a minimal CI (pytest 3.10/3.12) that runs the example smoke test.
- **The public surface is locked** by `tests/test_public_api_contract.py` and the version guarded at 0.x.

## As-built deviations (honest record)

Recorded in design §12: `recover()` takes **no `goal`** (carried in the checkpoint); the outcome type
is **`AgentRun`** (not `RunResult`); `Observation`/`Model`/`MockModel` are not top-level exports
(`ScriptableMockModel` is an example helper); and `CodeHarness.resume`/`observe_world` were **not**
force-migrated onto `recover()` because the harness interleaves a Task-specific env setup between
restore and observe — churning the validated benchmark for no user-facing gain was rejected.

## Governance

0.x; no publish/release/announcement; ADR-0007 (no hardcoded harness) and ADR-0009 (honest scope)
honored; branch-per-phase (master only via PR). The v1.0 hold and outward-action-needs-approval rule
remain in force.
