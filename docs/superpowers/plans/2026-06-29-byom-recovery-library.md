# BYOM Recovery Library — Implementation Plan (M4, slice 1: primitives core)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose Cairn's validated Re-grounding Recovery as public, model-agnostic primitives — `checkpoint()` and `recover()` over a `World` abstraction — proven to work for a non-workspace world.

**Architecture:** Approach A (extract validated core). Generalize the existing `distill`/`observe` to a `World.digest()` seam (instead of a hardcoded filesystem digest), add a `Workspace` reference `World`, and wrap the proven `distill → observe → reconcile → resolve_danger_window → re-ground` flow in two public functions. The existing benchmark/harness stay untouched and green; they migrate in slice 2 (AP-3).

**Tech Stack:** Python 3.12, dataclasses, `typing.Protocol`, pytest (`pythonpath=["src"]`).

**Scope of THIS plan:** AP-1 (contracts + `Workspace` World + `distill`/`observe` generalization) and AP-2 (the `checkpoint`/`recover` primitives + the non-workspace abstraction proof). AP-3 (Agent loop + benchmark migration), AP-4 (example + docs), AP-5 (public-API contract test) are outlined at the end and become their own plans. After AP-2 the repo has working, tested public primitives — software that stands on its own.

**Branch:** `milestone-4-byom-library` (already checked out).

---

## File Structure

- **Modify** `src/cairn/harness/distill.py` — add an optional `digest` param so the durable core's `world.digest` can come from a `World`, not only `world_digest(workspace_dir)`.
- **Modify** `src/cairn/harness/observe.py` — add a generic `observe(world, ledger, since_offset)` alongside the existing `observe_world` (kept for the unmigrated harness).
- **Modify** `src/cairn/contract.py` — add public `World`, `CheckpointStore`, `EffectLedger` Protocols (the BYOM contracts).
- **Create** `src/cairn/worlds/__init__.py` — re-export `Workspace`.
- **Create** `src/cairn/worlds/workspace.py` — `Workspace`, the reference `World` (filesystem + content digest), built on the existing `WorkspaceManager` + `world_digest`.
- **Create** `src/cairn/recovery.py` — `Checkpoint`, `Regrounded`, `checkpoint()`, `recover()`, `regrounded_history()`.
- **Modify** `src/cairn/__init__.py` — re-export the new public names.
- **Create** `tests/test_world_contracts.py` — `Workspace` satisfies `World`; snapshot→mutate→restore→digest round-trip; generalized `distill`/`observe`.
- **Create** `tests/test_recovery_primitives.py` — `checkpoint`/`recover` over `Workspace`; the no-checkpoint path; **the non-workspace `FakeWorld` abstraction proof**.

---

## Task 1: Generalize `distill` to accept a `World` digest

**Files:**
- Modify: `src/cairn/harness/distill.py`
- Test: `tests/test_world_contracts.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_world_contracts.py
from cairn.harness.distill import distill, CHECKPOINT


def test_distill_uses_supplied_digest_over_workspace():
    # When a digest is supplied (the World seam), distill records it verbatim and does NOT
    # touch the filesystem — so a non-workspace World works.
    state = distill(
        "goal", [], mode=CHECKPOINT, step=0,
        digest={"k": "v"}, workspace_dir="/does/not/exist",
    )
    assert state.durable_core.world.digest == {"k": "v"}


def test_distill_without_digest_falls_back_to_workspace(tmp_path):
    (tmp_path / "a.txt").write_text("hi", encoding="utf-8")
    state = distill("goal", [], mode=CHECKPOINT, step=0, workspace_dir=str(tmp_path))
    assert "a.txt" in state.durable_core.world.digest  # legacy path unchanged
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_world_contracts.py -q`
Expected: FAIL — `distill() got an unexpected keyword argument 'digest'`.

- [ ] **Step 3: Add the `digest` param**

In `src/cairn/harness/distill.py`, add `digest: Optional[dict] = None` to `distill(...)` and pass it through to `_durable_core(...)`. Add `from typing import Optional` to the imports. In `_durable_core`, add the same param and replace the world-digest line:

```python
# signature additions (distill and _durable_core both gain):
    digest: Optional[dict] = None,
```
```python
# distill(...) body — pass it down:
    core = _durable_core(
        goal, history, step=step, model_version=model_version,
        harness_version=harness_version, effect_offset=effect_offset,
        snap_id=snap_id, workspace_dir=workspace_dir, digest=digest,
    )
```
```python
# _durable_core(...) — replace the existing `core.world.digest = ...` line with:
    if digest is not None:
        core.world.digest = digest
    else:
        core.world.digest = world_digest(workspace_dir) if workspace_dir else {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_world_contracts.py -q`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add src/cairn/harness/distill.py tests/test_world_contracts.py
git commit -m "M4 AP-1: distill accepts a World digest (generalizes off the filesystem)"
```

---

## Task 2: Add a generic `observe(world, ledger, since_offset)`

**Files:**
- Modify: `src/cairn/harness/observe.py`
- Test: `tests/test_world_contracts.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_world_contracts.py
from cairn.harness.observe import observe


class _DigestWorld:
    def __init__(self, digest): self._d = digest
    def snapshot(self): return "s0"
    def restore(self, snap_id): pass
    def digest(self): return self._d


class _Ledger:
    def list_effects_since(self, offset): return [{"seq": offset, "type": "INTENT"}]


def test_observe_reads_world_digest_and_ledger():
    obs = observe(_DigestWorld({"f": "h"}), _Ledger(), since_offset=3)
    assert obs.digest == {"f": "h"}
    assert obs.effects_since == [{"seq": 3, "type": "INTENT"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_world_contracts.py::test_observe_reads_world_digest_and_ledger -q`
Expected: FAIL — `cannot import name 'observe'`.

- [ ] **Step 3: Add the generic `observe`**

In `src/cairn/harness/observe.py`, add (keep `observe_world` as-is):

```python
def observe(world, ledger, since_offset: int) -> ObservedWorld:
    """Re-observe via the World's own digest + the effect ledger (the generic, BYOM form).

    Unlike `observe_world` (which hashes a filesystem workspace), this asks the World for its
    digest, so a non-filesystem World re-grounds the same way.
    """
    return ObservedWorld(
        digest=world.digest(),
        effects_since=list(ledger.list_effects_since(since_offset)),
        workspace_dir=getattr(world, "workspace_dir", ""),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_world_contracts.py -q`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/cairn/harness/observe.py tests/test_world_contracts.py
git commit -m "M4 AP-1: generic observe(world, ledger, offset) over the World seam"
```

---

## Task 3: Public `World` / `CheckpointStore` / `EffectLedger` Protocols

**Files:**
- Modify: `src/cairn/contract.py`
- Test: `tests/test_world_contracts.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_world_contracts.py
from cairn.contract import World as WorldProto
from cairn.contract import CheckpointStore as CheckpointStoreProto
from cairn.contract import EffectLedger as EffectLedgerProto
from cairn.runtime.checkpoint_store import CheckpointStore as ConcreteCkpt
from cairn.runtime.effect_ledger import EffectLedger as ConcreteLedger


def test_concrete_impls_satisfy_protocols(tmp_path):
    ckpt = ConcreteCkpt(str(tmp_path / "ck"))
    ledger = ConcreteLedger(str(tmp_path / "e.jsonl"), "run")
    assert isinstance(ckpt, CheckpointStoreProto)
    assert isinstance(ledger, EffectLedgerProto)
    assert isinstance(_DigestWorld({}), WorldProto)  # a duck-typed World qualifies
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_world_contracts.py::test_concrete_impls_satisfy_protocols -q`
Expected: FAIL — `cannot import name 'World' from 'cairn.contract'`.

- [ ] **Step 3: Add the protocols**

Append to `src/cairn/contract.py` (it already imports `Optional, Protocol, Tuple, runtime_checkable` and `ContinuationState`):

```python
@runtime_checkable
class World(Protocol):
    """The observable, snapshottable world an agent acts on (the BYOM seam).

    A dev implements these three methods; `cairn.worlds.Workspace` is the bundled filesystem
    reference. `digest()` is the World's own content fingerprint used for re-grounding.
    """

    def snapshot(self) -> str: ...
    def restore(self, snap_id: str) -> None: ...
    def digest(self) -> dict: ...


@runtime_checkable
class CheckpointStore(Protocol):
    """Durable checkpoint persistence (bundled; dev does not implement). I2 atomic."""

    def checkpoint(self, state: ContinuationState, snap_id: str, effect_offset: int) -> str: ...
    def load_latest(self) -> Optional[Tuple[ContinuationState, str, int]]: ...


@runtime_checkable
class EffectLedger(Protocol):
    """Append-only write-ahead effect log (bundled; dev does not implement). I1/I3."""

    def append_effect(
        self, intent: str, idempotency_key: str, tool_class: str = "never-retry", step: int = 0
    ) -> int: ...
    def complete_effect(self, idempotency_key: str) -> None: ...
    def list_effects_since(self, offset: int) -> list[dict]: ...
    def current_offset(self) -> int: ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_world_contracts.py -q`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add src/cairn/contract.py tests/test_world_contracts.py
git commit -m "M4 AP-1: public World/CheckpointStore/EffectLedger protocols"
```

---

## Task 4: `Workspace` reference World

**Files:**
- Create: `src/cairn/worlds/__init__.py`
- Create: `src/cairn/worlds/workspace.py`
- Test: `tests/test_world_contracts.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_world_contracts.py
from cairn.worlds import Workspace


def test_workspace_world_snapshot_restore_digest(tmp_path):
    ws_dir = tmp_path / "ws"; ws_dir.mkdir()
    snaps = tmp_path / "snaps"
    w = Workspace(str(ws_dir), str(snaps))
    (ws_dir / "a.txt").write_text("one", encoding="utf-8")
    snap = w.snapshot()
    d1 = w.digest(); assert "a.txt" in d1
    (ws_dir / "a.txt").write_text("two", encoding="utf-8")   # diverge
    assert w.digest() != d1
    w.restore(snap)                                          # restore the snapshot
    assert w.digest() == d1
    assert isinstance(w, WorldProto)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_world_contracts.py::test_workspace_world_snapshot_restore_digest -q`
Expected: FAIL — `No module named 'cairn.worlds'`.

- [ ] **Step 3: Implement `Workspace`**

```python
# src/cairn/worlds/__init__.py
"""Bundled World implementations (the observable worlds an agent acts on)."""
from .workspace import Workspace

__all__ = ["Workspace"]
```
```python
# src/cairn/worlds/workspace.py
"""Workspace — the reference filesystem World (snapshot/restore + content digest).

Wraps the proven runtime pieces (`WorkspaceManager` + `world_digest`) behind the public
`World` seam, so the recovery primitives treat the filesystem like any other World.
"""

from __future__ import annotations

from ..runtime.digest import world_digest
from ..runtime.workspace import WorkspaceManager


class Workspace:
    def __init__(self, workspace_dir: str, snapshots_dir: str) -> None:
        self.workspace_dir = workspace_dir
        self._wm = WorkspaceManager(workspace_dir, snapshots_dir)

    def snapshot(self) -> str:
        return self._wm.snapshot()

    def restore(self, snap_id: str) -> None:
        self._wm.restore(snap_id)

    def digest(self) -> dict:
        return world_digest(self.workspace_dir)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_world_contracts.py -q`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add src/cairn/worlds/ tests/test_world_contracts.py
git commit -m "M4 AP-1: Workspace reference World (filesystem snapshot/restore/digest)"
```

---

## Task 5: `checkpoint()` primitive

**Files:**
- Create: `src/cairn/recovery.py`
- Test: `tests/test_recovery_primitives.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_recovery_primitives.py
from cairn.model import Action, CODE, StepRecord
from cairn.recovery import checkpoint, recover, Regrounded
from cairn.runtime.checkpoint_store import CheckpointStore
from cairn.runtime.effect_ledger import EffectLedger
from cairn.worlds import Workspace


def _fixture(tmp_path):
    ws_dir = tmp_path / "ws"; ws_dir.mkdir()
    world = Workspace(str(ws_dir), str(tmp_path / "snaps"))
    store = CheckpointStore(str(tmp_path / "ck"))
    ledger = EffectLedger(str(tmp_path / "e.jsonl"), "run")
    return ws_dir, world, store, ledger


def test_checkpoint_persists_a_loadable_state(tmp_path):
    ws_dir, world, store, ledger = _fixture(tmp_path)
    (ws_dir / "a.txt").write_text("done", encoding="utf-8")
    history = [StepRecord(step=0, action=Action(kind=CODE, code="write a.txt"), returncode=0)]
    state = checkpoint("the goal", history, world, store, ledger, step=0)
    assert state.durable_core.intent.root_goal == "the goal"
    loaded = store.load_latest()
    assert loaded is not None and loaded[0].durable_core.plan[0].status == "done"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_recovery_primitives.py::test_checkpoint_persists_a_loadable_state -q`
Expected: FAIL — `No module named 'cairn.recovery'`.

- [ ] **Step 3: Implement `recovery.py` (checkpoint + types)**

```python
# src/cairn/recovery.py
"""Public Re-grounding Recovery primitives — bring your own model AND your own loop.

`checkpoint(...)` distills + snapshots + persists a durable cairn each step. `recover(...)`
performs the full RGR (load -> restore -> re-observe -> reconcile -> resolve effects ->
re-ground) and hands back a `history` the caller continues their own loop from. Both operate
over the `World` / `CheckpointStore` / `EffectLedger` seams (cairn.contract), so nothing about
the model, the world, or the persistence is hardcoded (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .harness.distill import CHECKPOINT, distill
from .harness.effects import EffectfulTool, Resolution, resolve_danger_window
from .harness.observe import observe
from .harness.reconcile import ResumePlan, reconcile
from .model import CODE, Action, StepRecord
from .state import ContinuationState, PlanStep

#: A durable checkpoint (the "cairn"). Public alias of the internal state type.
Checkpoint = ContinuationState


@dataclass
class Regrounded:
    """The result of `recover`: the re-grounded history + what recovery did."""

    history: list = field(default_factory=list)
    resolutions: list = field(default_factory=list)
    plan: Optional[ResumePlan] = None


def checkpoint(
    goal: str,
    history: list,
    world,
    store,
    ledger,
    *,
    step: int,
    model_version: str = "",
    harness_version: str = "",
) -> Checkpoint:
    """Distill `history` into a cairn, snapshot the world, and persist atomically."""
    snap = world.snapshot()
    offset = ledger.current_offset()
    state = distill(
        goal, history, mode=CHECKPOINT, step=step,
        model_version=model_version, harness_version=harness_version,
        effect_offset=offset, snap_id=snap, digest=world.digest(),
    )
    store.checkpoint(state, snap, offset)
    return state


def recover(goal: str, world, store, ledger, *, effect_tools=None, escalate: bool = True) -> Regrounded:
    """The RGR protocol as a primitive. Returns a `Regrounded` to continue your loop from.

    No durable checkpoint -> empty history (start fresh). Otherwise: restore the world, re-observe
    via the World's digest, reconcile the torn step, resolve any effect danger window (exactly-once,
    ADR-0006), and re-ground a minimal history from the cairn's done steps.
    """
    loaded = store.load_latest()
    if loaded is None:
        return Regrounded(history=[], resolutions=[], plan=None)
    state, snap_id, offset = loaded
    world.restore(snap_id)
    observed = observe(world, ledger, offset)
    plan = reconcile(state, observed)
    resolutions = resolve_danger_window(plan.danger_window, effect_tools or {}, ledger, escalate=escalate)
    return Regrounded(history=regrounded_history(plan.plan), resolutions=resolutions, plan=plan)


def regrounded_history(plan_steps: list[PlanStep]) -> list[StepRecord]:
    """Re-ground a minimal history from the cairn's *done* steps (re-grounding, not replay)."""
    out: list[StepRecord] = []
    i = 0
    for p in plan_steps:
        if p.status == "done":
            out.append(StepRecord(step=i, action=Action(kind=CODE, code=p.description), returncode=0))
            i += 1
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_recovery_primitives.py::test_checkpoint_persists_a_loadable_state -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/cairn/recovery.py tests/test_recovery_primitives.py
git commit -m "M4 AP-2: checkpoint() primitive + recovery types"
```

---

## Task 6: `recover()` primitive — round-trip and no-checkpoint path

**Files:**
- Test: `tests/test_recovery_primitives.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_recovery_primitives.py
def test_recover_with_no_checkpoint_starts_fresh(tmp_path):
    _, world, store, ledger = _fixture(tmp_path)
    out = recover("goal", world, store, ledger)
    assert isinstance(out, Regrounded) and out.history == [] and out.plan is None


def test_recover_regrounds_history_from_checkpoint(tmp_path):
    ws_dir, world, store, ledger = _fixture(tmp_path)
    (ws_dir / "a.txt").write_text("done", encoding="utf-8")
    history = [StepRecord(step=0, action=Action(kind=CODE, code="write a.txt"), returncode=0)]
    checkpoint("goal", history, world, store, ledger, step=0)
    out = recover("goal", world, store, ledger)
    assert len(out.history) == 1                      # the one done step is re-grounded
    assert out.history[0].action.code == "write a.txt"
    assert out.plan is not None and out.plan.clean    # nothing diverged (restore matched)
```

- [ ] **Step 2: Run tests to verify they fail (or pass)**

Run: `python -m pytest tests/test_recovery_primitives.py -q`
Expected: PASS — `recover()` already implemented in Task 5. (If anything fails, fix `recovery.py` until green; this task is the recover() contract lock.)

- [ ] **Step 3: (No new impl expected — recover() landed in Task 5.)**

If a test fails, the likely cause is `resolve_danger_window` receiving an unexpected ledger; confirm `EffectLedger.complete_effect` exists (it does). No change otherwise.

- [ ] **Step 4: Run the full suite to confirm no regression**

Run: `python -m pytest -q`
Expected: PASS (all prior tests + the new ones).

- [ ] **Step 5: Commit**

```bash
git add tests/test_recovery_primitives.py
git commit -m "M4 AP-2: lock recover() contract (round-trip + no-checkpoint paths)"
```

---

## Task 7: The non-workspace abstraction proof (the key test)

**Files:**
- Test: `tests/test_recovery_primitives.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_recovery_primitives.py
class FakeWorld:
    """An in-memory, NON-filesystem World — proves recovery isn't married to the workspace."""

    def __init__(self):
        self.state: dict[str, str] = {}
        self._snaps: dict[str, dict] = {}
        self._n = 0

    def snapshot(self) -> str:
        sid = f"s{self._n}"; self._n += 1
        self._snaps[sid] = dict(self.state)
        return sid

    def restore(self, snap_id: str) -> None:
        self.state = dict(self._snaps[snap_id])

    def digest(self) -> dict:
        return {k: self.state[k] for k in sorted(self.state)}


def test_recovery_works_for_a_non_workspace_world(tmp_path):
    world = FakeWorld()
    store = CheckpointStore(str(tmp_path / "ck"))
    ledger = EffectLedger(str(tmp_path / "e.jsonl"), "run")

    # "Do" two steps in the in-memory world, checkpointing each.
    world.state["x"] = "1"
    h = [StepRecord(step=0, action=Action(kind=CODE, code="set x"), returncode=0)]
    checkpoint("goal", h, world, store, ledger, step=0)
    world.state["y"] = "2"
    h.append(StepRecord(step=1, action=Action(kind=CODE, code="set y"), returncode=0))
    checkpoint("goal", h, world, store, ledger, step=1)

    # Simulate a crash that corrupts in-memory state, then recover.
    world.state = {"x": "CORRUPT"}
    out = recover("goal", world, store, ledger)

    assert world.state == {"x": "1", "y": "2"}        # world restored from the snapshot
    assert [s.action.code for s in out.history] == ["set x", "set y"]  # both steps re-grounded
    assert out.plan is not None and out.plan.clean
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_recovery_primitives.py::test_recovery_works_for_a_non_workspace_world -q`
Expected: PASS — this is the proof the `World` abstraction generalizes beyond the filesystem.

- [ ] **Step 3: (No new impl — this validates Tasks 1–5.)**

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_recovery_primitives.py
git commit -m "M4 AP-2: abstraction proof — RGR recovers a non-workspace (in-memory) World"
```

---

## Task 8: Re-export the public API surface

**Files:**
- Modify: `src/cairn/__init__.py`
- Test: `tests/test_recovery_primitives.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_recovery_primitives.py
def test_public_api_is_importable_from_cairn():
    import cairn
    for name in ("checkpoint", "recover", "Regrounded", "Checkpoint",
                 "World", "Workspace", "Action", "StepRecord"):
        assert hasattr(cairn, name), f"cairn.{name} missing from public API"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_recovery_primitives.py::test_public_api_is_importable_from_cairn -q`
Expected: FAIL — `cairn.checkpoint missing`.

- [ ] **Step 3: Add the re-exports**

Append to `src/cairn/__init__.py` (below `__version__`):

```python
from .contract import CheckpointStore, EffectLedger, World
from .model import Action, StepRecord
from .recovery import Checkpoint, Regrounded, checkpoint, recover, regrounded_history
from .worlds import Workspace

__all__ = [
    "__version__",
    # contracts
    "World", "CheckpointStore", "EffectLedger",
    # types
    "Action", "StepRecord", "Checkpoint", "Regrounded",
    # primitives
    "checkpoint", "recover", "regrounded_history",
    # reference world
    "Workspace",
]
```

- [ ] **Step 4: Run test + full suite**

Run: `python -m pytest -q`
Expected: PASS (entire suite).

- [ ] **Step 5: Commit**

```bash
git add src/cairn/__init__.py tests/test_recovery_primitives.py
git commit -m "M4 AP-2: re-export the public recovery API from cairn"
```

---

## Slice 1 done — definition of done

- `python -m pytest -q` green (existing suite + `test_world_contracts.py` + `test_recovery_primitives.py`).
- `import cairn; cairn.checkpoint / cairn.recover / cairn.World / cairn.Workspace` all resolve.
- The non-workspace `FakeWorld` test proves the abstraction.
- No change to `agent_loop`, eval, or the benchmark (they migrate in AP-3) — so they stay green as the regression guard.

---

## Remaining milestone (separate plans — outline only)

These are scoped here for traceability; each becomes its own detailed plan before execution.

- **AP-3 — Opt-in `Agent` loop + benchmark migration.** Add `cairn/agent.py` `Agent(model, world, *, store, ledger, tools, effect_tools).run(goal)/.resume(goal)` by re-pointing the existing `CodeHarness` onto Task-5 primitives (with an *executable* `Workspace`). Migrate `eval`/`benchmarks` and `agent_loop` to the public primitives; delete the now-duplicated `_history_from_plan`/`observe_world` once callers move. **DoD:** benchmark + full suite green on the public API.
- **AP-4 — Example + docs.** `examples/byom_recovery.py` (both the primitives path and the `Agent` path) with the `MockModel`; an optional Ollama transport row + a documented local run; `docs/guide/recovery-in-your-agent.md` + a public API reference. **DoD:** example smoke test in CI (mock model); local path documented + CI-gated.
- **AP-5 — Public-API contract test + polish.** A test that pins the exact `cairn/__init__` surface (guards accidental breakage); CHANGELOG + trackers (M4 milestone README, ap-index, phase-tracking); confirm 0.x / no-publish governance notes. **DoD:** suite green; trackers updated; PR to master.

---

## Self-review

- **Spec coverage:** §4 contracts → Tasks 1–4; §4 Layer-2 primitives → Tasks 5–7; §5 public surface → Task 8; §8 abstraction proof → Task 7; §8 no-checkpoint path → Task 6; §4 backward-compat (no harness change) → enforced by "no change to agent_loop/eval" + full-suite green in Tasks 6–8. Layer-3 `Agent` (§4) and example/docs (§8) → AP-3/AP-4 (out of this slice, outlined).
- **Placeholder scan:** none — every code/test step has complete code and an exact command.
- **Type consistency:** `checkpoint`/`recover` signatures `(goal, history, world, store, ledger, ...)` are identical across Tasks 5–8; `Regrounded(history, resolutions, plan)`, `Checkpoint = ContinuationState`, `World.snapshot/restore/digest`, and `EffectLedger.current_offset` match the concrete classes read from source.
- **Governance:** 0.x, no publish; all seams injected (ADR-0007); benchmark stays green (ADR-0009 honesty preserved).
