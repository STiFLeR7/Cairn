# Cairn as a Bring-Your-Own-Model Recovery Library — Design

- **Date:** 2026-06-29
- **Status:** Approved (brainstorming) → ready for implementation planning
- **Branch:** `milestone-4-byom-library`
- **Author:** maintainers + Claude
- **Supersedes/relates:** the v1.0 gate (held; see `hold-v1-until-live-llm`), ADR-0007 (no hardcoded
  harness), ADR-0004 (re-grounding resume), ADR-0005 (unified distillation), ADR-0006 (effect-safety WAL),
  the boundary contract (`docs/design/boundary-contract.md`).

## 1. Context & motivation

Cairn's v1.0 gate is a *powered live study* that confirms C1 (RGR beats cold restart). The maintainer has
**no paid API**; free tiers can't sustain a clean run (rate limits + flaky free models — recorded in M3 as
measurement-limited, not mechanism-limited; see `free-tier-confounds-are-test-artifacts`). Rather than block
on buying API access, we **head Cairn toward its actual strength**: the *recovery mechanism* itself —
Re-grounding Recovery (RGR): unified distillation, re-observe/reconcile, and an effect-safety WAL.

**Direction (chosen):** make Cairn a **bring-your-own-model (BYOM) recovery library** — a clean, documented,
installable-shaped API that an external developer drops into *their own* agent, with *their own* model and
keys. Validation of C1 then also becomes something a user can reproduce on their own model; Cairn ships the
*mechanism*, not a dependency on us proving it on a paid model.

This does **not** lift the v1.0 hold and ships **nothing outward** (no PyPI publish, no release, no
announcement) — it is a 0.x, in-repo milestone.

## 2. Decisions (locked during brainstorming)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Integration shape | **Both**: recovery *primitives* as the core, **plus** a thin opt-in "batteries-included" loop on top. |
| 2 | World model | **`World` abstraction** (`observe` + effects); `Workspace` is the bundled reference implementation. |
| 3 | Distribution | **Design + docs, no publish.** 0.x, in-repo, on its own branch. Honors the v1.0 hold. |
| 4 | Implementation approach | **A — extract the validated RGR core** into a public module + protocols; re-point the existing loop and benchmark at it. Reuse proven code; benchmark stays green as the regression guard. |

## 3. Goals & non-goals

**Goals**
- A clean public API an outside developer can use to add crash-recovery to their agent with their own model.
- Two entry points: low-level primitives (`checkpoint`/`recover`) for devs who keep their own loop, and an
  opt-in `Agent` loop for devs who want it turnkey.
- A `World` abstraction so the recovery mechanism is not married to the filesystem workspace.
- The existing recovery-faithful benchmark keeps running, on top of the new public API (regression guard).
- A runnable example using a **local/mock model** (no paid API).

**Non-goals (YAGNI / explicitly deferred)**
- Non-workspace `World` *implementations* (the abstraction ships; only `Workspace` is implemented).
- Framework adapters (LangChain, LlamaIndex, etc.).
- PyPI publish / any outward release; async; distributed/multi-process recovery.
- Lifting the v1.0 hold or changing the claims status.

## 4. Architecture

Today's monolithic `Runtime` protocol bundles three concerns (execute, world/workspace, persistence).
Approach A **splits** it into finer protocols and exposes the RGR steps as standalone functions, while a
bundled implementation continues to satisfy all of them so nothing existing breaks.

### Layer 1 — Contracts (what a dev implements or accepts)
- **`Model`** (= today's `ModelProvider`): `propose(goal, history) -> Action`. Dev brings their own
  (local/Ollama/mock/their framework adapter). Unchanged seam.
- **`World`**: the observable, snapshottable thing the agent acts on.
  - `observe(effect_offset) -> Observation`
  - `snapshot() -> str` (opaque snapshot id)
  - `restore(snap_id: str) -> None`
  - Reference implementation **`Workspace`** (local filesystem; = current workspace runtime + digest).
  - **Note on execution:** `World` is the *observe + snapshot/restore* seam only — it does **not** require an
    `apply(action)` method. In the **primitives path** the dev applies actions however they like (their own
    tools/code) and only calls `checkpoint`/`recover`. The bundled `Workspace` *additionally* exposes
    execution (it wraps today's `Runtime.execute`), which the **`Agent` opt-in loop** uses to run a code
    action; an `Agent` therefore needs an *executable* World (the bundled `Workspace` is one).
- **`EffectfulTool`**: the exactly-once contract for irreversible side-effects, via the effect-WAL
  (register intent + idempotency key before acting; mark complete after).
- **Bundled recovery infra** (dev does *not* implement these): `CheckpointStore` + `EffectLedger`
  (= current `runtime/checkpoint_store.py` + `runtime/effect_ledger.py`).

### Layer 2 — Recovery primitives (public functions; "bring your own loop")
- `checkpoint(goal, history, world, store, *, step, ...) -> Checkpoint`
  distill → snapshot world → persist atomically. Returns the durable `Checkpoint` (today's
  `ContinuationState`).
- `recover(goal, world, store, effect_tools, ...) -> Regrounded`
  the full RGR: load latest checkpoint → `world.restore` → re-observe → reconcile torn step →
  resolve effect danger-window → re-ground a minimal `history`. Returns `Regrounded(history, resolutions,
  plan)`. The dev resumes **their** loop from `history`.

### Layer 3 — Opt-in loop (public; "batteries-included")
- `Agent(model, world, *, store=None, tools=None, effect_tools=None, max_steps=...)`
  - `.run(goal) -> RunResult`
  - `.resume(goal) -> RunResult`
  This is today's `CodeHarness`, re-pointed onto Layer 2 + `World`. Defaults wire a `Workspace` +
  file-backed store/ledger so the simple case is one call.

### Backward-compatibility
The existing `LocalRuntime` implements all three new protocols (`World` + `CheckpointStore` +
`EffectLedger`), so the **benchmark, eval baselines, and current tests run unchanged**. New public names are
re-exported from `cairn/__init__`. No behavior change to validated code paths — verified by the green suite.

## 5. Public API surface (re-exported from `cairn/__init__`)

```
# Types
Action, Observation, StepRecord, Checkpoint, RunResult, Regrounded
# Contracts (Protocols)
Model, World, EffectfulTool, CheckpointStore, EffectLedger
# Reference implementations
Workspace, FileCheckpointStore, FileEffectLedger      # (names map to current runtime impls)
MockModel                                              # deterministic, for tests/examples
# Primitives
checkpoint(...), recover(...)
# Opt-in loop
Agent
```

Names are finalized during implementation against the existing code (e.g. `ContinuationState` → exported as
`Checkpoint`); the public surface is small and stable, internal modules stay where they are.

## 6. Data flow

**Primitives path (dev keeps their loop):**
```
loop step:
    action = model.propose(goal, history)
    obs    = apply(action)                   # dev's own world mutation (their tools/code) — NOT a World method
    history.append(StepRecord(...))
    checkpoint(goal, history, world, store, step=i)   # world only needs observe/snapshot here
# crash …
regrounded = recover(goal, world, store, effect_tools)
history = regrounded.history                # continue the loop from here
```
**Effects (exactly-once):** an `EffectfulTool` appends `(intent, idempotency_key)` to the WAL *before* the
side-effect and marks it complete after; `recover()` resolves the danger window so a torn effect is neither
lost nor duplicated.

**Opt-in path:** `Agent(model, world).run(goal)` / `.resume(goal)` does the above internally.

## 7. Error handling

- `recover()` with no durable checkpoint → returns empty `history` (fresh start; mirrors today's
  `resume` → `run` fallback).
- `world.restore(snap_id)` on a missing/corrupt snapshot → surfaced error (no silent partial restore).
- Torn step (in-flight at crash) → reconciled: the reopened step is excluded from re-grounded history and
  redone.
- Never-retry effects in the danger window → escalate (do not blind-retry), per ADR-0006.

## 8. Testing strategy

- **Regression guard:** the entire existing suite stays green on the new public API.
- **Abstraction proof (key new test):** a **fake, non-workspace `World`** (in-memory) + a scripted `Model`
  drive `checkpoint`/`recover` end-to-end — proving the recovery mechanism works for an outside dev, not just
  for the bundled `Workspace`.
- **Primitives unit tests:** `checkpoint`/`recover` over the fake World, incl. the no-checkpoint and torn-step
  paths.
- **Example smoke test:** the runnable example with the `MockModel` runs in CI (offline, deterministic).
- **Local model (Ollama):** documented and runnable by the user, but **CI-gated** (no network in CI).

## 9. MVP scope → milestone decomposition

A new milestone **M4 — BYOM recovery library**, on branch `milestone-4-byom-library`, ~4–5 Action Points:

1. **Split the contracts:** introduce `World` / `CheckpointStore` / `EffectLedger` protocols; make
   `LocalRuntime`/`Workspace` satisfy them; suite green.
2. **Recovery primitives:** public `checkpoint()` / `recover()` over the protocols; unit-tested incl. the
   fake-World abstraction proof.
3. **Opt-in `Agent` loop + benchmark migration:** re-point `CodeHarness` onto the primitives; export `Agent`;
   migrate eval/benchmark to public names; suite green.
4. **Example + docs:** a local/mock BYOM example (both paths) + "Recovery in your own agent" guide + public
   API reference.
5. **Public-API contract test + polish:** lock the `cairn/__init__` surface with a test; CHANGELOG/trackers.

## 10. Governance

- Stays **0.x**; **no PyPI publish, no release, no announcement** (the v1.0 hold and the
  outward-action-needs-approval rule remain in force).
- **No hardcoded harness** (ADR-0007): `Model`, `World`, tools, store are all injected.
- **Honest scope** (ADR-0009): the library does not claim C1 is confirmed; it lets a user reproduce the
  evidence on their own model.
- **Branch-per-phase:** all work on `milestone-4-byom-library`; master only via PR.

## 11. Open questions

None blocking. Public names (`Checkpoint` vs `ContinuationState`, `Workspace` vs current class name) are
finalized against the code during AP-1, preferring the existing names unless a clearer public name aids
readability.
