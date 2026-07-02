# BYOM Recovery Library — Implementation Plan (M4, slice 2 / AP-3: opt-in Agent loop + de-dup)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the opt-in, batteries-included `Agent` loop built directly on the public `checkpoint()`/`recover()` primitives, make the bundled `LocalRuntime` actually satisfy the new `World`/`CheckpointStore`/`EffectLedger` protocols, and remove the one genuine code duplication (`_history_from_plan`) — all while the existing benchmark/eval/harness stay green as the regression guard.

**Architecture:** Approach A (extract validated core), slice 2. The primitives landed in slice 1. Here we (a) de-duplicate `agent_loop._history_from_plan` onto `recovery.regrounded_history`; (b) add additive protocol-alias methods to `LocalRuntime` so the spec's backward-compat claim is real and a `LocalRuntime` is usable as a `World`+store+ledger; (c) make the reference `Workspace` *executable* (it already snapshots/restores/digests); (d) add `cairn/agent.py` — a thin `Agent(model, world, *, store, ledger, ...)` with `.run(goal)` / `.resume(goal)` over the primitives, proven to work on a non-workspace executable world.

**Tech Stack:** Python 3.12, dataclasses, `typing.Protocol`, pytest (`pythonpath=["src"]`).

**Scope of THIS plan:** AP-3. AP-4 (example + docs) and AP-5 (public-API contract test + trackers/CHANGELOG + PR to master) remain their own plans.

**Branch:** `milestone-4-byom-library` (already checked out; PR #10 open — this slice extends it).

---

## Deliberate, documented deviation from the AP-3 outline

The slice-1 plan's AP-3 outline said "re-point `CodeHarness` onto Layer 2 + `World`" and "delete the now-duplicated `_history_from_plan`/`observe_world`". After reading the code, **two honest scope adjustments** (ADR-0009 — preserve the green regression guard; do not churn validated paths for cosmetics):

1. **`_history_from_plan` IS removed** (it is byte-for-byte duplicate logic of `recovery.regrounded_history`). ✅ done in Task 1.
2. **`observe_world` is KEPT, and `CodeHarness.resume` is NOT force-migrated onto `recover()`.** Reason: `CodeHarness.resume` interleaves `_setup_task_env(task, cwd)` *between* `restore` and `observe` (a `Task` concern). `recover()` is deliberately task-agnostic and does `restore`→`observe` atomically, so delegating would reorder fixture-planting after observation and could change reconcile/digest results — risking the green benchmark for no user-facing gain. `observe_world` (filesystem-cwd-aware, harness layer) and `observe` (generic, primitives layer) coexist *by layer*, not as duplication. The user-facing deliverable — a usable opt-in loop on the primitives — is delivered as the new `Agent`, not as a refactor of the internal harness.

This is recorded in the plan so the spec is updated to match in AP-5.

---

## File Structure

- **Modify** `src/cairn/harness/agent_loop.py` — import `regrounded_history` from `..recovery`; delete the local `_history_from_plan`; drop now-unused imports (`Action`, `CODE`, `PlanStep`).
- **Modify** `src/cairn/recovery.py` — update the stale `# NOTE` comment (the dup is unified now).
- **Modify** `src/cairn/runtime/local_runtime.py` — add additive `World`/`EffectLedger` alias methods (`snapshot`, `restore`, `digest`, `current_offset`) delegating to the existing `*_workspace`/`current_effect_offset`/`world_digest`. No behavior change.
- **Modify** `src/cairn/worlds/workspace.py` — add `execute(code, cwd=None)` (injected sandbox + interpreter, defaults like `LocalRuntime`) so a `Workspace` is an *executable* World for the `Agent`.
- **Create** `src/cairn/agent.py` — `Agent`, `AgentRun`. The opt-in loop on the primitives.
- **Modify** `src/cairn/__init__.py` — re-export `Agent`, `AgentRun`.
- **Create** `tests/test_agent.py` — `Agent.run` completes; `Agent.resume` round-trip + no-checkpoint path; the non-workspace executable `FakeWorld` proof.
- **Modify** `tests/test_world_contracts.py` — `LocalRuntime` satisfies the three protocols; `Workspace.execute` runs code.

---

## Task 1: De-duplicate `_history_from_plan` onto `recovery.regrounded_history`

**Files:**
- Modify: `src/cairn/harness/agent_loop.py`
- Modify: `src/cairn/recovery.py`
- Test: `tests/test_recovery_primitives.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_recovery_primitives.py
def test_agent_loop_reuses_the_public_regrounded_history():
    # The harness must not keep its own copy of the re-grounding logic; it uses the primitive.
    from cairn.harness import agent_loop
    from cairn import recovery

    assert not hasattr(agent_loop, "_history_from_plan"), "duplicate logic still present"
    assert agent_loop.regrounded_history is recovery.regrounded_history
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_recovery_primitives.py::test_agent_loop_reuses_the_public_regrounded_history -q`
Expected: FAIL — `_history_from_plan` still present / `agent_loop.regrounded_history` missing.

- [ ] **Step 3: Edit `agent_loop.py`**

In `src/cairn/harness/agent_loop.py`:

Change the model import (line 20) from:
```python
from ..model import CODE, FINISH, Action, ModelProvider, StepRecord
```
to (drop `CODE`, `Action` — only used by the deleted function):
```python
from ..model import FINISH, ModelProvider, StepRecord
```

Change the state import (line 21) from:
```python
from ..state import ContinuationState, PlanStep
```
to (drop `PlanStep`):
```python
from ..state import ContinuationState
```

Add this import next to the other `.` harness imports (after the `from .reconcile import ResumePlan, reconcile` line):
```python
from ..recovery import regrounded_history
```

Replace the resume body line:
```python
        history = _history_from_plan(plan.plan)
```
with:
```python
        history = regrounded_history(plan.plan)
```

Delete the entire `_history_from_plan` function at the bottom of the file (the `def _history_from_plan(plan: list[PlanStep]) -> list[StepRecord]:` block and its docstring/body).

- [ ] **Step 4: Update the stale NOTE in `recovery.py`**

In `src/cairn/recovery.py`, replace the line:
```python
# NOTE: harness/agent_loop.py has a private copy (_history_from_plan); unified onto this in AP-3.
```
with:
```python
# NOTE: harness/agent_loop.py imports this directly (the single source of re-grounding logic).
```

- [ ] **Step 5: Run the new test + full suite**

Run: `python -m pytest tests/test_recovery_primitives.py::test_agent_loop_reuses_the_public_regrounded_history -q && python -m pytest -q`
Expected: PASS — the identity test passes and the **entire existing suite stays green** (proves the de-dup is behavior-preserving; the benchmark/eval still recover identically).

- [ ] **Step 6: Commit**

```bash
git add src/cairn/harness/agent_loop.py src/cairn/recovery.py tests/test_recovery_primitives.py
git commit -m "M4 AP-3: de-dup agent_loop history re-grounding onto recovery.regrounded_history"
```

---

## Task 2: `LocalRuntime` satisfies `World` / `CheckpointStore` / `EffectLedger`

**Files:**
- Modify: `src/cairn/runtime/local_runtime.py`
- Test: `tests/test_world_contracts.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_world_contracts.py
from cairn.runtime.local_runtime import LocalRuntime


def test_local_runtime_satisfies_the_byom_protocols(tmp_path):
    rt = LocalRuntime(str(tmp_path / "rt"))
    assert isinstance(rt, WorldProto)
    assert isinstance(rt, CheckpointStoreProto)
    assert isinstance(rt, EffectLedgerProto)


def test_local_runtime_world_aliases_round_trip(tmp_path):
    rt = LocalRuntime(str(tmp_path / "rt"))
    from pathlib import Path
    Path(rt.workspace_dir, "a.txt").write_text("one", encoding="utf-8")
    snap = rt.snapshot()                       # alias of snapshot_workspace
    d1 = rt.digest(); assert "a.txt" in d1      # alias of world_digest(workspace_dir)
    Path(rt.workspace_dir, "a.txt").write_text("two", encoding="utf-8")
    rt.restore(snap)                            # alias of restore_workspace
    assert rt.digest() == d1
    assert rt.current_offset() == rt.current_effect_offset()  # ledger alias
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_world_contracts.py::test_local_runtime_satisfies_the_byom_protocols -q`
Expected: FAIL — `LocalRuntime` is not an instance of `World` (no `snapshot`/`restore`/`digest`).

- [ ] **Step 3: Add the alias methods**

In `src/cairn/runtime/local_runtime.py`, add `from .digest import world_digest` to the imports (alongside the other `.` imports). Then add these methods to `LocalRuntime` (place them after `restore_workspace`, before the checkpoint-store section):

```python
    # --- World protocol aliases (cairn.contract.World) -----------------------
    # The Runtime IS a World: these forward to the workspace methods so a LocalRuntime
    # can be passed straight into the BYOM primitives (checkpoint/recover) and the Agent.
    def snapshot(self) -> str:
        return self.snapshot_workspace()

    def restore(self, snap_id: str) -> None:
        self.restore_workspace(snap_id)

    def digest(self) -> dict:
        return world_digest(self.workspace_dir)
```

And add this method after `current_effect_offset` (so it satisfies `EffectLedger.current_offset`):

```python
    # --- EffectLedger protocol alias (cairn.contract.EffectLedger) -----------
    def current_offset(self) -> int:
        return self.current_effect_offset()
```

- [ ] **Step 4: Run test + full suite**

Run: `python -m pytest tests/test_world_contracts.py -q && python -m pytest -q`
Expected: PASS — protocol conformance holds and nothing regresses (additive only).

- [ ] **Step 5: Commit**

```bash
git add src/cairn/runtime/local_runtime.py tests/test_world_contracts.py
git commit -m "M4 AP-3: LocalRuntime satisfies World/CheckpointStore/EffectLedger (additive aliases)"
```

---

## Task 3: Make `Workspace` executable (`execute`)

**Files:**
- Modify: `src/cairn/worlds/workspace.py`
- Test: `tests/test_world_contracts.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_world_contracts.py
def test_workspace_executes_code_in_its_dir(tmp_path):
    ws_dir = tmp_path / "ws"; ws_dir.mkdir()
    w = Workspace(str(ws_dir), str(tmp_path / "snaps"))
    res = w.execute("open('made.txt', 'w').write('hi')")
    assert res.returncode == 0
    assert (ws_dir / "made.txt").read_text(encoding="utf-8") == "hi"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_world_contracts.py::test_workspace_executes_code_in_its_dir -q`
Expected: FAIL — `Workspace` has no attribute `execute`.

- [ ] **Step 3: Add execution to `Workspace`**

Rewrite `src/cairn/worlds/workspace.py` to add an injected sandbox + interpreter (defaults mirror `LocalRuntime`) and an `execute` method. Full file:

```python
"""Workspace — the reference filesystem World (snapshot/restore + content digest).

Wraps the proven runtime pieces (`WorkspaceManager` + `world_digest`) behind the public
`World` seam, so the recovery primitives treat the filesystem like any other World. It is
ALSO executable (`execute`) so the opt-in `Agent` loop can run code actions against it; the
sandbox and interpreter are injected (ADR-0007), defaulting to a local subprocess.
"""

from __future__ import annotations

import sys
from typing import Optional, Sequence

from ..runtime.digest import world_digest
from ..runtime.sandbox_local import LocalSubprocessSandbox
from ..runtime.workspace import WorkspaceManager
from ..sandbox import ExecResult, Sandbox


class Workspace:
    def __init__(
        self,
        workspace_dir: str,
        snapshots_dir: str,
        sandbox: Optional[Sandbox] = None,
        interpreter: Optional[str] = None,
    ) -> None:
        self.workspace_dir = workspace_dir
        self._wm = WorkspaceManager(workspace_dir, snapshots_dir)
        self.sandbox: Sandbox = sandbox or LocalSubprocessSandbox()
        self.interpreter = interpreter or sys.executable

    # --- World seam (snapshot / restore / digest) ----------------------------
    def snapshot(self) -> str:
        return self._wm.snapshot()

    def restore(self, snap_id: str) -> None:
        self._wm.restore(snap_id)

    def digest(self) -> dict:
        return world_digest(self.workspace_dir)

    # --- executable World (used by the opt-in Agent loop) --------------------
    def execute(self, code: str, cwd: Optional[str] = None) -> ExecResult:
        argv: Sequence[str] = [self.interpreter, "-c", code]
        return self.sandbox.run(argv, cwd=cwd or self.workspace_dir)
```

- [ ] **Step 4: Run test + full suite**

Run: `python -m pytest tests/test_world_contracts.py -q && python -m pytest -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/cairn/worlds/workspace.py tests/test_world_contracts.py
git commit -m "M4 AP-3: Workspace is an executable World (injected sandbox + interpreter)"
```

---

## Task 4: The opt-in `Agent` loop — `run(goal)`

**Files:**
- Create: `src/cairn/agent.py`
- Test: `tests/test_agent.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_agent.py
from cairn.agent import Agent, AgentRun
from cairn.model import Action, CODE, FINISH
from cairn.model_mock import ScriptableMockModel
from cairn.runtime.checkpoint_store import CheckpointStore
from cairn.runtime.effect_ledger import EffectLedger
from cairn.worlds import Workspace


def _agent(tmp_path, script):
    ws_dir = tmp_path / "ws"; ws_dir.mkdir()
    world = Workspace(str(ws_dir), str(tmp_path / "snaps"))
    store = CheckpointStore(str(tmp_path / "ck"))
    ledger = EffectLedger(str(tmp_path / "e.jsonl"), "run")
    model = ScriptableMockModel(script)
    return ws_dir, Agent(model, world, store=store, ledger=ledger, max_steps=10)


def test_agent_run_executes_the_script_and_checkpoints(tmp_path):
    script = [
        Action(kind=CODE, code="open('a.txt','w').write('1')"),
        Action(kind=CODE, code="open('b.txt','w').write('2')"),
        Action(kind=FINISH, result="done"),
    ]
    ws_dir, agent = _agent(tmp_path, script)
    run = agent.run("make a and b")
    assert isinstance(run, AgentRun)
    assert run.finished is True            # model emitted FINISH
    assert run.steps == 2                  # two code actions executed
    assert run.checkpoints == 2            # one checkpoint per executed step
    assert (ws_dir / "a.txt").exists() and (ws_dir / "b.txt").exists()
    assert run.final_state is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_agent.py::test_agent_run_executes_the_script_and_checkpoints -q`
Expected: FAIL — `No module named 'cairn.agent'`.

- [ ] **Step 3: Implement `agent.py` (run + types)**

```python
# src/cairn/agent.py
"""The opt-in, batteries-included Agent loop — built on the public recovery primitives.

`Agent` is the turnkey path for a dev who wants recovery without writing their own loop:
bring a `Model` and a `World` (the bundled `Workspace`, or your own executable world) and
call `.run(goal)`; after a crash, `.resume(goal)` re-grounds via `recover()` and continues.

The loop itself is deliberately tiny — propose -> execute -> record -> checkpoint — because
all the recovery intelligence lives in the primitives (`checkpoint`/`recover`). Everything is
injected (model, world, store, ledger, effect tools); nothing is hardcoded (ADR-0007).

A `World` used by the Agent must additionally be *executable* (expose `execute(code, cwd=None)
-> ExecResult`); the bundled `Workspace` is. The Agent does not judge task success (it has no
task oracle) — it reports whether the model finished and hands back the full history + the last
checkpoint so the caller applies their own success criterion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional

from .model import FINISH, ModelProvider, StepRecord
from .recovery import Checkpoint, checkpoint, recover
from .harness.effects import EffectfulTool, Resolution


@dataclass
class AgentRun:
    """The outcome of `Agent.run`/`Agent.resume`."""

    finished: bool                                  # model emitted FINISH (vs hit max_steps)
    steps: int                                      # steps executed in THIS call
    checkpoints: int                                # checkpoints written in THIS call
    history: list = field(default_factory=list)     # full StepRecord history (re-grounded + new)
    final_state: Optional[Checkpoint] = None
    resumed: bool = False
    recovery_tax: Optional[int] = None              # steps executed after resume (None for run)
    resolutions: list = field(default_factory=list)


class Agent:
    def __init__(
        self,
        model: ModelProvider,
        world,
        *,
        store,
        ledger,
        effect_tools: Optional[Mapping[str, EffectfulTool]] = None,
        max_steps: int = 20,
        escalate: bool = True,
        model_version: str = "byom",
        harness_version: str = "",
    ) -> None:
        self.model = model
        self.world = world
        self.store = store
        self.ledger = ledger
        self.effect_tools: Mapping[str, EffectfulTool] = effect_tools or {}
        self.max_steps = max_steps
        self.escalate = escalate
        self.model_version = model_version
        self.harness_version = harness_version

    def run(self, goal: str) -> AgentRun:
        """Drive the goal from scratch, checkpointing each executed step."""
        return self._loop(goal, [], start=0, resumed=False, resolutions=[])

    def resume(self, goal: str) -> AgentRun:
        """Re-ground from the latest checkpoint (RGR), then continue the loop.

        With no durable checkpoint, falls back to a fresh `run` (mirrors the primitives).
        """
        rg = recover(
            self.world, self.store, self.ledger,
            effect_tools=self.effect_tools, escalate=self.escalate,
        )
        if rg.plan is None:  # nothing to resume from
            return self.run(goal)
        return self._loop(
            goal, list(rg.history), start=len(rg.history),
            resumed=True, resolutions=rg.resolutions,
        )

    def _loop(self, goal, history, *, start, resumed, resolutions) -> AgentRun:
        executed = 0
        checkpoints = 0
        final_state: Optional[Checkpoint] = None
        finished = False
        for step in range(start, self.max_steps):
            action = self.model.propose(goal, history)
            if action.kind == FINISH:
                finished = True
                break
            res = self.world.execute(action.code)
            history.append(
                StepRecord(
                    step=step, action=action,
                    returncode=res.returncode, stdout=res.stdout, stderr=res.stderr,
                )
            )
            executed += 1
            final_state = checkpoint(
                goal, history, self.world, self.store, self.ledger, step=step,
                model_version=self.model_version, harness_version=self.harness_version,
            )
            checkpoints += 1
        return AgentRun(
            finished=finished,
            steps=executed,
            checkpoints=checkpoints,
            history=history,
            final_state=final_state,
            resumed=resumed,
            recovery_tax=executed if resumed else None,
            resolutions=list(resolutions),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_agent.py::test_agent_run_executes_the_script_and_checkpoints -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/cairn/agent.py tests/test_agent.py
git commit -m "M4 AP-3: opt-in Agent loop (run) on the recovery primitives"
```

---

## Task 5: `Agent.resume` — round-trip and no-checkpoint path

**Files:**
- Test: `tests/test_agent.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_agent.py
def test_agent_resume_with_no_checkpoint_starts_fresh(tmp_path):
    script = [Action(kind=CODE, code="open('a.txt','w').write('1')"), Action(kind=FINISH)]
    ws_dir, agent = _agent(tmp_path, script)
    run = agent.resume("make a")          # no checkpoint yet -> behaves like run
    assert run.resumed is False
    assert (ws_dir / "a.txt").exists()


def test_agent_resume_regrounds_and_continues_after_a_crash(tmp_path):
    # Step 0 runs and checkpoints; then we simulate a crash (new Agent, same dirs) and resume.
    ws_dir = tmp_path / "ws"; ws_dir.mkdir()
    snaps = str(tmp_path / "snaps"); ck = str(tmp_path / "ck"); ej = str(tmp_path / "e.jsonl")

    def fresh_world():
        return Workspace(str(ws_dir), snaps)

    script = [
        Action(kind=CODE, code="open('a.txt','w').write('1')"),
        Action(kind=CODE, code="open('b.txt','w').write('2')"),
        Action(kind=FINISH),
    ]
    # First Agent: run only the first step, then "crash" (max_steps=1 stops after one execute).
    a1 = Agent(ScriptableMockModel(script), fresh_world(),
               store=CheckpointStore(ck), ledger=EffectLedger(ej, "run"), max_steps=1)
    r1 = a1.run("make a then b")
    assert r1.steps == 1 and (ws_dir / "a.txt").exists() and not (ws_dir / "b.txt").exists()

    # Recovery Agent: fresh objects pointing at the SAME durable dirs; resume re-grounds step 0.
    a2 = Agent(ScriptableMockModel(script), fresh_world(),
               store=CheckpointStore(ck), ledger=EffectLedger(ej, "run"), max_steps=10)
    r2 = a2.resume("make a then b")
    assert r2.resumed is True
    assert len(r2.history) >= 2                     # step 0 re-grounded + step 1 executed
    assert r2.recovery_tax == 1                     # only ONE new step needed (not a full restart)
    assert (ws_dir / "b.txt").exists()              # the task got finished
    assert r2.finished is True
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest tests/test_agent.py -q`
Expected: PASS — `resume` already implemented in Task 4. (If the crash-resume test fails, the likely cause is the model picking the wrong next action: the `ScriptableMockModel` indexes by `len(history)`, and `resume` seeds history with the one re-grounded step, so `propose` returns `script[1]` — the `b.txt` action. Confirm `regrounded_history` yields exactly the done steps.)

- [ ] **Step 3: (No new impl expected — resume landed in Task 4.)**

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_agent.py
git commit -m "M4 AP-3: lock Agent.resume contract (re-ground round-trip + no-checkpoint path)"
```

---

## Task 6: `Agent` works on a non-workspace executable World (abstraction proof)

**Files:**
- Test: `tests/test_agent.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_agent.py
class _ExecResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode; self.stdout = stdout; self.stderr = stderr


class ExecFakeWorld:
    """An in-memory, NON-filesystem executable World — proves the Agent isn't workspace-bound.

    `execute` interprets a tiny 'k=v' command language by mutating in-memory state.
    """

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

    def execute(self, code: str, cwd=None) -> _ExecResult:
        k, _, v = code.partition("=")
        self.state[k.strip()] = v.strip()
        return _ExecResult()


def test_agent_recovers_on_a_non_workspace_world(tmp_path):
    world = ExecFakeWorld()
    store = CheckpointStore(str(tmp_path / "ck"))
    ledger = EffectLedger(str(tmp_path / "e.jsonl"), "run")
    script = [
        Action(kind=CODE, code="x=1"),
        Action(kind=CODE, code="y=2"),
        Action(kind=FINISH),
    ]
    # Run step 0 then "crash".
    a1 = Agent(ScriptableMockModel(script), world,
               store=store, ledger=ledger, max_steps=1)
    a1.run("set x then y")
    assert world.state == {"x": "1"}

    # Corrupt in-memory state, then recover + continue with a fresh Agent on the SAME world+dirs.
    world.state = {"x": "CORRUPT"}
    a2 = Agent(ScriptableMockModel(script), world,
               store=CheckpointStore(str(tmp_path / "ck")),
               ledger=EffectLedger(str(tmp_path / "e.jsonl"), "run"), max_steps=10)
    run = a2.resume("set x then y")

    assert world.state == {"x": "1", "y": "2"}      # restored from snapshot, then y set
    assert run.recovery_tax == 1                    # only the un-done step was redone
    assert run.finished is True
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_agent.py::test_agent_recovers_on_a_non_workspace_world -q`
Expected: PASS — proves the opt-in loop, not just the primitives, generalizes beyond the filesystem.

- [ ] **Step 3: (No new impl — validates Tasks 3–5 on a custom World.)**

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_agent.py
git commit -m "M4 AP-3: abstraction proof — Agent loop recovers a non-workspace executable World"
```

---

## Task 7: Re-export `Agent` / `AgentRun` from `cairn`

**Files:**
- Modify: `src/cairn/__init__.py`
- Test: `tests/test_agent.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_agent.py
def test_agent_is_public_api():
    import cairn
    assert hasattr(cairn, "Agent") and hasattr(cairn, "AgentRun")
    assert "Agent" in cairn.__all__ and "AgentRun" in cairn.__all__
    # the whole public surface still imports cleanly
    for name in cairn.__all__:
        assert hasattr(cairn, name), f"cairn.{name} declared in __all__ but missing"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_agent.py::test_agent_is_public_api -q`
Expected: FAIL — `cairn.Agent` missing.

- [ ] **Step 3: Add the re-exports**

In `src/cairn/__init__.py`, add after the `from .worlds import Workspace` line:
```python
from .agent import Agent, AgentRun
```

In the `__all__` list, replace the trailing section:
```python
    # reference world
    "Workspace",
]
```
with:
```python
    # reference world
    "Workspace",
    # opt-in loop
    "Agent", "AgentRun",
]
```

- [ ] **Step 4: Run test + full suite**

Run: `python -m pytest -q`
Expected: PASS (entire suite, including `test_agent.py`, `test_world_contracts.py`, `test_recovery_primitives.py`, and the unchanged benchmark/eval/harness tests).

- [ ] **Step 5: Commit**

```bash
git add src/cairn/__init__.py tests/test_agent.py
git commit -m "M4 AP-3: re-export Agent + AgentRun from cairn (public opt-in loop)"
```

---

## AP-3 done — definition of done

- `python -m pytest -q` green: existing benchmark/eval/harness suite + `test_world_contracts.py` + `test_recovery_primitives.py` + new `test_agent.py`.
- `import cairn; cairn.Agent(model, world, store=..., ledger=...).run(goal)/.resume(goal)` works for the bundled `Workspace` **and** a custom non-workspace executable World.
- `LocalRuntime` now genuinely `isinstance` of `World`/`CheckpointStore`/`EffectLedger` (spec §4 backward-compat made real).
- The one real duplication (`_history_from_plan`) is gone; the harness re-grounds via the public `regrounded_history` primitive.
- No behavior change to `agent_loop`/eval/benchmark recovery paths (regression guard intact, ADR-0009).

---

## Remaining milestone (separate plans — outline only)

- **AP-4 — Example + docs.** `examples/byom_recovery.py` (primitives path **and** `Agent` path) with `ScriptableMockModel`; an optional Ollama transport row + a documented local run; `docs/guide/recovery-in-your-agent.md` + a public API reference. **DoD:** example smoke test in CI (mock model); local path documented + CI-gated.
- **AP-5 — Public-API contract test + polish.** A test pinning the exact `cairn/__init__` surface (guards accidental breakage); CHANGELOG + trackers (M4 README, ap-index, phase-tracking); **update the design spec §9 to record the AP-3 scope deviation** (`observe_world` retained; `recover()` has no `goal` param); confirm 0.x / no-publish governance. **DoD:** suite green; trackers updated; PR #10 finalized to master.

---

## Self-review

- **Spec coverage:** §4 Layer-3 `Agent` → Tasks 4–6; §4 "Agent needs an executable World" → Task 3; §4 backward-compat ("LocalRuntime implements all three protocols") → Task 2; §5 public surface (`Agent`) → Task 7; §8 abstraction proof (loop level) → Task 6; de-dup of duplicated logic → Task 1. The outline's `observe_world` deletion and `CodeHarness` internal re-point are **deliberately not done** (documented deviation above; preserves the green regression guard — ADR-0009 — and AP-5 updates the spec to match).
- **Placeholder scan:** none — every code/test step carries complete code and an exact command.
- **Type consistency:** `Agent(model, world, *, store, ledger, effect_tools=None, max_steps=20, escalate=True, ...)` and `AgentRun(finished, steps, checkpoints, history, final_state, resumed, recovery_tax, resolutions)` are used identically across Tasks 4–7. `checkpoint(goal, history, world, store, ledger, *, step, model_version, harness_version)` and `recover(world, store, ledger, *, effect_tools, escalate)` match the slice-1 signatures (read from `src/cairn/recovery.py`). `Workspace(workspace_dir, snapshots_dir, sandbox=None, interpreter=None)` extends the slice-1 ctor compatibly (new params are optional). `ExecResult` has `.returncode/.stdout/.stderr` (matches `cairn.sandbox.ExecResult`).
- **Import-cycle check:** `agent_loop` importing `..recovery` is safe — `recovery` imports only leaf harness modules (`distill`/`effects`/`observe`/`reconcile`) + `model`/`state`, none of which import `agent_loop`. `agent.py` imports `recovery` + `model` + `harness.effects`; no module imports `agent`, so no cycle.
- **Governance:** 0.x, no publish; all seams injected (ADR-0007); benchmark stays green (ADR-0009 honesty preserved); deviation from the outline is recorded, not silent.
