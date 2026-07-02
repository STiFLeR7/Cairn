# AP-5 — BYOM Public-API Contract + Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Milestone M4 by (1) *locking* the public `cairn` surface with a contract test that fails on any drift and guards the 0.x version, and (2) reconciling the documentation-first record — design spec, milestone README, trackers, CHANGELOG — with what actually shipped in AP-1…AP-4, honestly recording the deviations.

**Architecture:** AP-5 adds **one** test file (the surface lock) and otherwise only updates documentation/trackers. No `src/` behavior changes. The lock test pins the exact 20-name `cairn.__all__`, asserts every name imports, and asserts `__version__` stays `0.x` (guards against an unapproved v1.0 bump). The docs work makes the merged-but-untracked M4 slices visible in the same trackers the earlier milestones use, and corrects the design spec where the implementation deliberately diverged (AP-3: `recover()` has no `goal` param; `observe_world` retained; several §5 names shipped differently).

**Tech Stack:** Python 3.10+, pytest (`pythonpath=["src"]`). Docs are Markdown.

**Governance (in force):** 0.x, **no PyPI publish / no release / no announcement** (v1.0 hold intact). AP-5 ships no tag and no outward artifact — the CHANGELOG entry is `[Unreleased]`, not a version bump. Honest scope (ADR-0009): the trackers/spec record M4 as a *mechanism library* milestone that does **not** confirm C1; deviations are recorded, not hidden. Branch-per-phase: all AP-5 work on `milestone-4-ap5-contract-polish`; master only via PR.

---

## Ground truth (verified against the code at plan time)

**The exact public surface** — `sorted(cairn.__all__)`, 20 names:
```
['Action', 'Agent', 'AgentRun', 'Checkpoint', 'CheckpointStore', 'EffectLedger',
 'EffectfulTool', 'EscalationRequired', 'FileCheckpointStore', 'FileEffectLedger',
 'Regrounded', 'Resolution', 'ResumePlan', 'StepRecord', 'Workspace', 'World',
 '__version__', 'checkpoint', 'recover', 'regrounded_history']
```
`cairn.__version__ == "0.2.0"`.

**Design-spec §5 vs. what shipped** (the reconciliation AP-5 must document honestly):
| Spec §5 listed | Reality on master | Note |
|---|---|---|
| `Observation` (type) | **not exported** | internal to `harness.observe`; not part of the public surface. |
| `RunResult` (type) | shipped as **`AgentRun`** | the Agent-loop outcome type. |
| `Model` (contract) | **not exported** | the seam is `ModelProvider` (duck-typed `propose`); documented, not re-exported. |
| `MockModel` (ref impl) | shipped as **`ScriptableMockModel`** in `cairn.model_mock` | example/test helper, not a top-level export. |
| `recover(goal, world, store, effect_tools, ...)` | **`recover(world, store, ledger, *, effect_tools=None, escalate=True)`** | **no `goal`** — carried in the loaded checkpoint (AP-3 deviation). |
| `Agent(model, world, *, store=None, tools=None, ...)` | `Agent(model, world, *, store, ledger, effect_tools=None, max_steps=20, ...)` | `ledger` is required + explicit; `effect_tools` not `tools`. |
| (not mentioned) | also exported: `regrounded_history`, `Resolution`, `ResumePlan`, `EscalationRequired`, `AgentRun` | finalized surface. |

**AP-3 scope deviation to record** (already noted in code/commits, now into the spec): `CodeHarness.resume` was **not** force-migrated onto `recover()` and `observe_world` was retained, because the harness interleaves `_setup_task_env(task, cwd)` between restore and observe (a Task concern the task-agnostic primitive must not reorder). The benchmark stays the regression guard.

---

## File Structure

| File | Create/Modify | Responsibility |
|---|---|---|
| `tests/test_public_api_contract.py` | Create | Lock the exact `cairn.__all__`; assert importability; guard `__version__` at 0.x. |
| `docs/superpowers/specs/2026-06-29-byom-recovery-library-design.md` | Modify | Add a "§12 — Implementation reconciliation (as-built)" section recording the §5/§9 deviations; leave the original text as the historical brainstorm record. |
| `project/phases/milestone-4-byom-library/README.md` | Create | The M4 milestone tracker README (mirrors M1–M3), summarizing the 5 slices, decisions, honest scope, and pointers to the superpowers spec/plans + PRs #10/#11. |
| `project/tracking/phase-tracking.md` | Modify | Add the M4 row to the board + a "Current milestone: M4" section; bump "Last updated". |
| `project/tracking/ap-index.md` | Modify | Add the "Milestone M4" AP table (slices AP-1…AP-5); update the header rollup + "Last updated". |
| `CHANGELOG.md` | Modify | Add an `[Unreleased] — Milestone M4` section (no version bump; in-repo 0.x). |

---

## Task 1: Public-API contract test (the surface lock)

**Files:**
- Create: `tests/test_public_api_contract.py`

**Note on TDD framing:** this is a *characterization / lock* test — it pins the surface that exists now so future drift fails CI. It should pass green immediately. If it does NOT pass on the first run, that is a real finding (unexpected drift): STOP and report, do not "adjust" the pinned set to whatever happens to be there.

- [ ] **Step 1: Write the contract test**

Create `tests/test_public_api_contract.py` with EXACTLY this content:

```python
"""Public API contract — the lock on the top-level `cairn` surface (M4 AP-5).

If you add/remove/rename a public name, this test fails on purpose: update `EXPECTED`
deliberately (a public-surface change is a decision, not an accident) and document it in
CHANGELOG.md + docs/guide/public-api-reference.md in the same change.
"""

import cairn

# The exact, intended public surface as of Milestone M4 (BYOM recovery library).
EXPECTED = {
    "__version__",
    # types
    "Action", "StepRecord", "Checkpoint", "Regrounded", "Resolution", "ResumePlan", "AgentRun",
    # contracts (Protocols)
    "World", "CheckpointStore", "EffectLedger",
    # effect safety
    "EffectfulTool", "EscalationRequired",
    # reference implementations
    "Workspace", "FileCheckpointStore", "FileEffectLedger",
    # primitives
    "checkpoint", "recover", "regrounded_history",
    # opt-in loop
    "Agent",
}


def test_all_matches_the_intended_surface_exactly():
    actual = set(cairn.__all__)
    missing = EXPECTED - actual
    extra = actual - EXPECTED
    assert not missing, f"public names declared but missing from __all__: {sorted(missing)}"
    assert not extra, f"public names in __all__ not in the intended contract: {sorted(extra)}"


def test_all_has_no_duplicates():
    assert len(cairn.__all__) == len(set(cairn.__all__))


def test_every_public_name_is_importable():
    for name in cairn.__all__:
        assert hasattr(cairn, name), f"cairn.{name} is in __all__ but not importable"


def test_version_is_still_0x():
    # Guards against an accidental/unapproved v1.0 bump — the v1.0 release is HELD
    # (needs explicit approval + powered live evidence; the project stays 0.x).
    assert cairn.__version__.startswith("0."), (
        f"__version__ is {cairn.__version__!r}; v1.0+ requires explicit approval + live evidence"
    )
```

- [ ] **Step 2: Run the contract test — it must PASS immediately**

Run: `python -m pytest tests/test_public_api_contract.py -q`
Expected: PASS (4 tests). If any FAIL, STOP and report the exact mismatch (drift is a finding, not something to paper over by editing `EXPECTED`).

- [ ] **Step 3: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS (137 + 4 = 141).

- [ ] **Step 4: Commit**

```bash
git add tests/test_public_api_contract.py
git commit -m "M4 AP-5: lock the public cairn.__all__ surface + guard 0.x version"
```

---

## Task 2: Design-spec reconciliation (§5/§9 as-built)

**Files:**
- Modify: `docs/superpowers/specs/2026-06-29-byom-recovery-library-design.md`

**Approach:** do NOT rewrite the original brainstorm text (it is the historical record). APPEND a new section at the end that records what actually shipped and why it diverged.

- [ ] **Step 1: Append the reconciliation section**

Open `docs/superpowers/specs/2026-06-29-byom-recovery-library-design.md`. After the final line (the end of "## 11. Open questions"), append EXACTLY this content:

```markdown

## 12. Implementation reconciliation (as-built, 2026-07-02)

M4 shipped across five slices (AP-1…AP-5) using the superpowers spec→plan→execute workflow, all
merged to `master` (AP-1–AP-3 via PR #10 `93e03e5`; AP-4 via PR #11 `0e2ad54`; AP-5 via this PR).
This section records where the delivered code deliberately diverged from §5/§9 above. The sections
1–11 are preserved as the original approved brainstorm; §12 is authoritative for the as-built API.

### 12.1 Final public surface (locked by `tests/test_public_api_contract.py`)

`cairn.__all__` (20 names): `Action, StepRecord, Checkpoint, Regrounded, Resolution, ResumePlan,
AgentRun` (types); `World, CheckpointStore, EffectLedger` (Protocols); `EffectfulTool,
EscalationRequired` (effect safety); `Workspace, FileCheckpointStore, FileEffectLedger` (reference
implementations); `checkpoint, recover, regrounded_history` (primitives); `Agent` (opt-in loop);
plus `__version__`.

### 12.2 Deviations from §5 (documented, not silent)

- **`recover()` takes no `goal`.** As-built: `recover(world, store, ledger, *, effect_tools=None,
  escalate=True) -> Regrounded`. The goal is carried inside the loaded checkpoint
  (`state.durable_core.intent`), so passing it again would be redundant and could contradict the
  cairn. (§5/§6 showed `recover(goal, ...)`.)
- **`RunResult` → `AgentRun`.** The opt-in loop's outcome type shipped as `AgentRun` (with
  `finished, steps, checkpoints, history, final_state, resumed, recovery_tax, resolutions`).
- **`Observation` and `Model` are not exported.** `Observation` is internal to `harness.observe`.
  The model seam is the existing `ModelProvider` (duck-typed `propose(goal, history) -> Action`);
  it is documented as "bring any object with `propose`", not re-exported as a `Model` name.
- **`MockModel` → `ScriptableMockModel`** in `cairn.model_mock` — an example/test helper, not a
  top-level export (kept out of the public contract deliberately; examples import it directly).
- **`Agent` constructor:** `Agent(model, world, *, store, ledger, effect_tools=None, max_steps=20,
  escalate=True, model_version="byom", harness_version="")`. `ledger` is required and explicit;
  effect tools are `effect_tools` (not `tools`); there is no hidden default store/ledger wiring.
- **Additional exports finalized:** `regrounded_history` (the re-grounding helper), `Resolution`,
  `ResumePlan`, `EscalationRequired`.

### 12.3 Scope deviation — the benchmark harness was not force-migrated (AP-3)

`recover()` is the public RGR primitive, but `CodeHarness.resume` (the benchmark's validated path)
was **not** re-pointed onto it, and `observe_world` was **retained**. Reason: `CodeHarness`
interleaves `_setup_task_env(task, cwd)` between world-restore and re-observe — a *Task* concern the
task-agnostic `recover()` primitive must not reorder. Forcing the migration risked the green
benchmark (the regression guard) for no user-facing gain. The primitives and the `Agent` loop are
proven world-agnostic independently (in-memory `FakeWorld`/`ExecFakeWorld` tests); the harness stays
as the regression guard. Honest-scope (ADR-0009): reuse where proven, do not churn validated paths.

### 12.4 §9 milestone decomposition — as-run

§9 estimated "~4–5 Action Points"; M4 ran **five slices**: AP-1 contracts split; AP-2 recovery
primitives (`checkpoint`/`recover` + fake-World proof); AP-3 opt-in `Agent` loop + de-dup;
AP-4 example + guide + API reference + CI smoke; AP-5 public-API contract lock + this reconciliation
+ trackers/CHANGELOG. The detailed per-slice record lives in `docs/superpowers/plans/`.

### 12.5 Governance (unchanged)

Still **0.x**; **no PyPI publish, no release, no announcement** — M4 ships nothing outward. The v1.0
hold and the outward-action-needs-approval rule remain in force; the surface lock guards the version
at 0.x. C1 is **not** confirmed by M4 — the library lets a user reproduce the evidence on their own
model (see `docs/research/claims-registry.md`).
```

- [ ] **Step 2: Verify nothing else in the suite broke (docs-only)**

Run: `python -m pytest -q`
Expected: PASS (141).

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-06-29-byom-recovery-library-design.md
git commit -m "M4 AP-5: reconcile design spec with as-built API (§12: recover no-goal, AgentRun, retained harness)"
```

---

## Task 3: Milestone M4 tracker README

**Files:**
- Create: `project/phases/milestone-4-byom-library/README.md`

**Approach:** mirror the structure/voice of the existing `project/phases/milestone-3-powered-live-study/README.md` (a milestone overview + per-slice status). Since M4 used the superpowers workflow (no `AP-00XX` files), reference the superpowers spec/plans as the detailed record.

- [ ] **Step 1: Create the README**

Create `project/phases/milestone-4-byom-library/README.md` with EXACTLY this content:

```markdown
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
```

- [ ] **Step 2: Verify the relative links resolve**

Run from repo root:
```bash
ls docs/superpowers/specs/2026-06-29-byom-recovery-library-design.md \
   docs/superpowers/plans/2026-06-29-byom-agent-loop-ap3.md \
   docs/superpowers/plans/2026-07-02-byom-example-and-docs-ap4.md \
   docs/superpowers/plans/2026-07-02-byom-contract-and-polish-ap5.md \
   src/cairn/recovery.py src/cairn/agent.py examples/byom_recovery.py
```
Expected: all exist.

- [ ] **Step 3: Commit**

```bash
git add project/phases/milestone-4-byom-library/README.md
git commit -m "M4 AP-5: milestone M4 tracker README (slices, as-built, honest scope)"
```

---

## Task 4: Trackers + CHANGELOG (make merged M4 visible)

**Files:**
- Modify: `project/tracking/phase-tracking.md`
- Modify: `project/tracking/ap-index.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update the phase-tracking board**

In `project/tracking/phase-tracking.md`:

(a) Change the `> Last updated: 2026-06-29.` line to `> Last updated: 2026-07-02.`

(b) In the status table, add this row immediately after the M3 row (line beginning `| M3 |`):
```markdown
| M4 | BYOM Recovery Library | 🟢 Complete (merged; in-repo 0.x — ships nothing outward) | 5 / 5 |
```

(c) Immediately below the `**Legend:** ...` line, insert a new current-milestone section (above the existing `## Current milestone: M3 ...`):
```markdown
## Current milestone: M4 — BYOM Recovery Library (entered 2026-06-29)

Pivot to Cairn's strength — the recovery **mechanism** — packaged as a **bring-your-own-model**
library an outside dev drops into their own agent with their own model/keys. Five slices, all merged
(AP-1–AP-3 via PR #10 `93e03e5`; AP-4 via PR #11 `0e2ad54`; AP-5 via this PR): **contracts split**
(`World`/`CheckpointStore`/`EffectLedger` Protocols; `LocalRuntime` satisfies all three so the
benchmark stays green), **public primitives** (`checkpoint`/`recover`, fake-World proof), **opt-in
`Agent` loop** (+ `regrounded_history` de-dup), **example + guide + API reference + CI smoke**, and
**public-API contract lock + spec reconciliation + trackers**. Ships **nothing outward** — 0.x, v1.0
hold intact; C1 **not** confirmed (the library lets a user reproduce it on their own model). As-built
deviations recorded in design §12 (notably `recover()` has no `goal`; harness not force-migrated).
See [`project/phases/milestone-4-byom-library/README.md`](../phases/milestone-4-byom-library/README.md).
```

- [ ] **Step 2: Update the AP index**

In `project/tracking/ap-index.md`:

(a) Change `> Last updated: 2026-06-23.` to `> Last updated: 2026-07-02.`

(b) At the end of the header blockquote (after the M2 rollup sentence, before the blank line preceding `**Status values:**`), append:
```markdown
> **Milestone M3** (AP-0048 … AP-0051) complete & merged 2026-06-29: **NO-GO** take 3 (stays 0.x).
> **Milestone M4** (BYOM recovery library) complete & merged 2026-07-02 as **five superpowers slices
> (AP-1 … AP-5)**, in-repo 0.x — ships nothing outward; the recovery mechanism as a bring-your-own-model
> library; C1 **not** confirmed (user-reproducible).
```

(c) At the very end of the file (after the M3 table), append a new section:
```markdown
## Milestone M4 — BYOM Recovery Library *(merged 2026-07-02; superpowers slice workflow)*

> M4 used the superpowers spec→plan→execute workflow, so its units are **slices AP-1…AP-5** (not
> the legacy `AP-00XX` files). Detailed record: [`docs/superpowers/`](../../docs/superpowers/) and
> [`project/phases/milestone-4-byom-library/README.md`](../phases/milestone-4-byom-library/README.md).

| Slice | Title | Status |
|---|---|---|
| AP-1 | Split contracts (`World`/`CheckpointStore`/`EffectLedger` Protocols; `LocalRuntime` satisfies) | Done *(PR #10)* |
| AP-2 | Recovery primitives (`checkpoint`/`recover`) + fake-World abstraction proof | Done *(PR #10)* |
| AP-3 | Opt-in `Agent` loop on the primitives + `regrounded_history` de-dup | Done *(PR #10)* |
| AP-4 | BYOM example + guide + public API reference + CI smoke test | Done *(PR #11)* |
| AP-5 | Public-API contract lock + design-spec reconciliation (§12) + trackers/CHANGELOG | Done *(this PR)* |
```

- [ ] **Step 3: Add the CHANGELOG entry**

In `CHANGELOG.md`, insert a new section immediately BEFORE the `## [0.2.0] — 2026-06-23 …` line
(i.e., after the intro paragraph that ends with "…updates this file."):

```markdown
## [Unreleased] — Milestone M4: BYOM recovery library (in-repo, 0.x — ships nothing outward)

Cairn's recovery **mechanism**, repackaged as a **bring-your-own-model (BYOM) library**: a clean,
documented public API an outside developer drops into *their own* agent with *their own* model and
keys. No new recovery science — it extracts and exposes the validated RGR core. **No tag, no PyPI
publish, no release, no announcement**: the v1.0 hold stands and this milestone ships nothing outward
(hence `[Unreleased]`, not a version bump). C1 is **not** confirmed by M4; the library lets a user
reproduce the evidence on their own model (see the [claims registry](docs/research/claims-registry.md)).

### Added
- **Recovery primitives** (`cairn.checkpoint`, `cairn.recover`) — the full Re-grounding Recovery
  protocol as public functions over `World` / `CheckpointStore` / `EffectLedger` seams; bring your
  own loop. Plus `regrounded_history` (the re-grounding helper) and `Regrounded`/`Resolution`/
  `ResumePlan` result types.
- **Contracts (Protocols):** `World` (`snapshot`/`restore`/`digest`; executable Worlds also
  `execute`), `CheckpointStore`, `EffectLedger`. `LocalRuntime` satisfies all three, so the M1–M3
  benchmark/eval paths run unchanged (regression guard).
- **Opt-in `Agent` loop** (`cairn.Agent`, `cairn.AgentRun`) — batteries-included `run()`/`resume()`
  on the primitives; proven world-agnostic by an in-memory `ExecFakeWorld`.
- **Reference implementations:** `Workspace` (executable filesystem `World`), `FileCheckpointStore`,
  `FileEffectLedger`.
- **Developer materials:** `examples/byom_recovery.py` (offline, deterministic — primitives + Agent +
  exactly-once effect), `docs/guide/recovery-in-your-agent.md`, `docs/guide/public-api-reference.md`,
  and an opt-in local-model (Ollama) path (never run in CI).
- **CI:** minimal GitHub Actions workflow running the test suite (incl. the example smoke test) on
  Python 3.10/3.12 — tests only, no publish steps.
- **Public-API contract test** (`tests/test_public_api_contract.py`) locking the exact `cairn.__all__`
  surface and guarding `__version__` at 0.x.

### Notes (as-built)
- `recover()` takes **no `goal`** (carried in the checkpoint); the Agent outcome type is `AgentRun`
  (not the brainstorm's `RunResult`); `CodeHarness.resume`/`observe_world` were **not** force-migrated
  onto `recover()` (the harness interleaves Task-specific env setup — churning the validated benchmark
  was rejected). Full reconciliation: design doc §12.
```

- [ ] **Step 4: Run the suite (docs-only change)**

Run: `python -m pytest -q`
Expected: PASS (141).

- [ ] **Step 5: Commit**

```bash
git add project/tracking/phase-tracking.md project/tracking/ap-index.md CHANGELOG.md
git commit -m "M4 AP-5: trackers + CHANGELOG — record merged M4 (phase board, ap-index, [Unreleased])"
```

---

## Final review (after all tasks)

Dispatch a holistic reviewer over the whole AP-5 diff (`git diff master...HEAD`). Confirm:
- **Contract test locks the real surface** (20 names) and fails on drift; version guard present.
- Suite green (141); no `src/` behavior change (only the new test + docs/trackers).
- **Honesty:** the spec §12, milestone README, trackers, and CHANGELOG all record the deviations
  (no-`goal` `recover`, `AgentRun`, retained harness) and the "C1 not confirmed / ships nothing
  outward" framing — nothing oversold, no verdict loosened.
- **Governance:** `[Unreleased]` (no version bump/tag), 0.x guard, v1.0 hold language intact.
- All new relative doc links resolve.

Then use **superpowers:finishing-a-development-branch** to open the PR to `master` (Option 2 — push +
PR; do NOT self-merge — the maintainer runs the review + merge).

## Self-review (author checklist — done at plan-write time)

1. **Spec coverage (pending AP-5 DoD):** public-API contract test ✅ (Task 1); CHANGELOG ✅ (Task 4);
   trackers — M4 README ✅ (Task 3), ap-index ✅ + phase-tracking ✅ (Task 4); design-spec deviation
   recorded ✅ (Task 2, §12 covers both the `recover()` no-`goal` and the retained-`observe_world`
   deviations); 0.x/no-publish governance confirmed ✅ (version guard test + CHANGELOG `[Unreleased]`
   + explicit language). DoD "suite green; trackers updated; PR to master" ✅.
2. **Placeholder scan:** none — the contract test is complete code; every doc block is full content.
3. **Consistency:** the pinned `EXPECTED` set equals the verified live `__all__` (20 names); the §12
   table, README, ap-index, and CHANGELOG all state the SAME deviations (no-`goal` `recover`,
   `AgentRun`, non-exported `Observation`/`Model`/`MockModel`, retained harness) — cross-checked.
4. **Scope discipline:** no `src/` behavior change; only a test + documentation/trackers. No new
   exports, no version bump. M4 README lives under `project/phases/` mirroring M1–M3; M4's detailed
   record stays in `docs/superpowers/` (it used that workflow), not retrofitted into `AP-00XX` files.
5. **Governance:** `[Unreleased]` (nothing shipped outward), 0.x guard test, v1.0 hold language intact,
   ADR-0007/0009 honored, branch-per-phase (all on `milestone-4-ap5-contract-polish`, PR to master).
