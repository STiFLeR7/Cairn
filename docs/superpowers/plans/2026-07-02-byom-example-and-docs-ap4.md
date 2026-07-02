# AP-4 — BYOM Example + Docs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a runnable, offline, deterministic BYOM example (primitives path + Agent path + exactly-once effect) and the docs that teach an outside developer to add Re-grounding Recovery to *their own* agent — all on the public `cairn` API, with the example smoke-tested in CI and an opt-in local-model (Ollama) path documented but never run in CI.

**Architecture:** AP-4 adds *no recovery mechanism* — it consumes the surface AP-1/AP-2/AP-3 already shipped. It (a) finalizes two public reference-impl names (`FileCheckpointStore`, `FileEffectLedger`) so examples/docs never reach into `cairn.runtime.*`, (b) adds one example file with three deterministic demo functions the smoke test drives, (c) adds a guide + API reference under `docs/guide/`, and (d) adds a minimal GitHub Actions workflow that runs the suite (the smoke test rides along). Everything concrete (goal, model, effect) lives in the example, never the library (ADR-0007).

**Tech Stack:** Python 3.10+ (stdlib only — `urllib` for the optional Ollama transport), pytest (`pythonpath=["src"]`), GitHub Actions.

**Governance (in force):** 0.x, **no PyPI publish / no release / no announcement** (v1.0 hold intact — the CI workflow runs tests only, no publish steps). No hardcoded harness (ADR-0007). Honest scope (ADR-0009): docs state plainly that C1 is *not* confirmed; the library lets a user reproduce the evidence on their own model. Branch-per-phase: all AP-4 work on `milestone-4-ap4-example-docs`; master only via PR.

---

## File Structure

| File | Create/Modify | Responsibility |
|---|---|---|
| `src/cairn/__init__.py` | Modify | Export `FileCheckpointStore` / `FileEffectLedger` (aliases of the concrete `cairn.runtime.*` classes) so the public surface includes a usable store + ledger, not just their Protocols. |
| `tests/test_public_exports.py` | Create | Pin the two new reference-impl exports (identity + `__all__` membership). AP-5 later locks the *whole* surface; this guards AP-4's additions. |
| `examples/byom_recovery.py` | Create | Three deterministic demos on the public API: `demo_primitives` (bring-your-own-loop), `demo_agent` (batteries-included), `demo_effect_once` (torn effect → exactly-once). Plus a `main()` that prints, and an opt-in `_ollama_model()` real adapter (never called in CI). |
| `tests/test_example_byom.py` | Create | The CI smoke test: import the example by path and assert each mock demo's outcome (re-grounding, recovery tax = 1, exactly-once). |
| `docs/guide/recovery-in-your-agent.md` | Create | The narrative guide: both integration paths, the exactly-once effect contract, the local-model (Ollama) run, honest 0.x/claims scope. |
| `docs/guide/public-api-reference.md` | Create | Reference for every name in `cairn.__all__`: signature, purpose, one-liner. |
| `README.md` | Modify | One additive pointer to the guide + the new example (discoverability). |
| `.github/workflows/ci.yml` | Create | Minimal CI: run `python -m pytest -q` on 3.10 + 3.12. No publish/release steps (v1.0 hold). |

---

## Task 1: Public reference-impl exports (`FileCheckpointStore`, `FileEffectLedger`)

**Why:** `cairn.__init__` currently exports the **Protocols** `CheckpointStore`/`EffectLedger` (from `contract.py`) but not a concrete, usable store/ledger — so an example would have to `from cairn.runtime.checkpoint_store import CheckpointStore`, reaching past the public surface. The approved design spec §5 lists `FileCheckpointStore`/`FileEffectLedger` as public reference implementations. Alias them (avoids the name clash with the Protocols).

**Files:**
- Modify: `src/cairn/__init__.py`
- Test: `tests/test_public_exports.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_public_exports.py`:

```python
"""AP-4 guards the two reference-impl names it adds to the public surface.
(AP-5 will lock the *entire* cairn.__all__ surface with a broader contract test.)
"""

from cairn.runtime.checkpoint_store import CheckpointStore as _ConcreteStore
from cairn.runtime.effect_ledger import EffectLedger as _ConcreteLedger


def test_file_backed_store_and_ledger_are_public_aliases():
    import cairn

    # The public names are exactly the concrete runtime classes (no wrapper, no drift).
    assert cairn.FileCheckpointStore is _ConcreteStore
    assert cairn.FileEffectLedger is _ConcreteLedger


def test_file_backed_names_are_in_all():
    import cairn

    assert "FileCheckpointStore" in cairn.__all__
    assert "FileEffectLedger" in cairn.__all__


def test_public_store_and_ledger_construct_and_work(tmp_path):
    import cairn

    store = cairn.FileCheckpointStore(str(tmp_path / "ck"))
    ledger = cairn.FileEffectLedger(str(tmp_path / "e.jsonl"), "run")
    assert store.load_latest() is None          # empty store
    assert ledger.current_offset() == 0         # empty ledger
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_public_exports.py -q`
Expected: FAIL — `AttributeError: module 'cairn' has no attribute 'FileCheckpointStore'`.

- [ ] **Step 3: Add the exports**

In `src/cairn/__init__.py`, add these imports after the existing `from .worlds import Workspace` line:

```python
from .runtime.checkpoint_store import CheckpointStore as FileCheckpointStore
from .runtime.effect_ledger import EffectLedger as FileEffectLedger
```

And in `__all__`, add a new group right after the `# reference world` / `"Workspace",` entry:

```python
    # reference recovery infra (bundled; a dev does not implement these)
    "FileCheckpointStore", "FileEffectLedger",
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_public_exports.py -q`
Expected: PASS (3 tests).

- [ ] **Step 5: Run the full suite (no regressions)**

Run: `python -m pytest -q`
Expected: PASS (existing 131 + 3 new = 134).

- [ ] **Step 6: Commit**

```bash
git add src/cairn/__init__.py tests/test_public_exports.py
git commit -m "M4 AP-4: export FileCheckpointStore/FileEffectLedger (public reference infra)"
```

---

## Task 2: The BYOM example (`examples/byom_recovery.py`) + smoke test

**Files:**
- Create: `examples/byom_recovery.py`
- Test: `tests/test_example_byom.py`

**Design notes for the implementer:**
- The example imports ONLY the public surface (`import cairn` / `from cairn import ...`), except the kind constants `CODE`/`FINISH` and `ScriptableMockModel`, which come from `cairn.model` / `cairn.model_mock` (stable, example-facing helpers already used by the other examples).
- Each demo is a pure function taking a `base_dir` and returning a dict of assertable facts, so the smoke test drives them deterministically. `main()` calls all three and prints.
- The primitives demo executes actions via `world.execute(...)` (the bundled `Workspace` is executable) to keep it concrete; the point of the primitives path is that *you* own the loop and call `checkpoint`/`recover` yourself.
- The Ollama adapter is defined but only reachable from `main()` when `CAIRN_OLLAMA=1` is set; the smoke test never sets it, so CI never hits the network.

- [ ] **Step 1: Write the failing smoke test**

Create `tests/test_example_byom.py`:

```python
"""Smoke test for examples/byom_recovery.py — the CI-run, offline, mock-model path.

Loads the example by file path (examples/ is not an importable package) and asserts each
deterministic demo's outcome. The optional Ollama path is never exercised here (no network in CI).
"""

import importlib.util
import os

_EX = os.path.join(os.path.dirname(__file__), "..", "examples", "byom_recovery.py")
_spec = importlib.util.spec_from_file_location("byom_recovery", _EX)
byom = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(byom)


def test_primitives_demo_regrounds_and_finishes(tmp_path):
    out = byom.demo_primitives(str(tmp_path))
    assert out["regrounded"] == 1               # step 0 re-grounded from the cairn
    assert out["new_steps"] == 1                 # only the un-done step redone (not a cold restart of 2)
    assert out["files"] == ["a.txt", "b.txt"]    # the task got finished


def test_agent_demo_resumes_with_recovery_tax_one(tmp_path):
    out = byom.demo_agent(str(tmp_path))
    assert out["resumed"] is True                # took the recover() path
    assert out["recovery_tax"] == 1             # only one new step after resume
    assert out["finished"] is True
    assert out["files"] == ["a.txt", "b.txt"]


def test_effect_demo_is_exactly_once(tmp_path):
    out = byom.demo_effect_once(str(tmp_path))
    assert out["resolutions"] == [("send-1", "skip")]   # verify saw it done -> not re-executed
    assert out["outbox_lines_before"] == 1
    assert out["outbox_lines_after"] == 1               # no duplicate effect (claim C3)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_example_byom.py -q`
Expected: FAIL — `FileNotFoundError` / import error (the example file does not exist yet).

- [ ] **Step 3: Write the example**

Create `examples/byom_recovery.py`:

```python
"""Bring-Your-Own-Model recovery, end to end — using the public `cairn` API only.

Three self-contained demos on a deterministic mock model (no paid API, no network):

  demo_primitives  — you keep your OWN loop; you call checkpoint()/recover() yourself.
  demo_agent       — the batteries-included Agent loop does it for you.
  demo_effect_once — a torn side-effect (INTENT written, crash before COMPLETE) is
                     resolved exactly-once on recover() (claim C3).

Run from the repo root:

    python examples/byom_recovery.py

Everything concrete (the goal, the scripted model, the effect) is wired *here*; the library
hardcodes none of it (ADR-0007). To use YOUR model, replace ScriptableMockModel with any object
exposing `propose(goal, history) -> Action`; see _ollama_model() for a real local-model adapter
(opt-in via CAIRN_OLLAMA=1; never used by the smoke test / CI).
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))  # run without PYTHONPATH

from cairn import (
    Action,
    EffectfulTool,
    StepRecord,
    Agent,
    FileCheckpointStore,
    FileEffectLedger,
    Workspace,
    checkpoint,
    recover,
)
from cairn.model import CODE, FINISH
from cairn.model_mock import ScriptableMockModel

GOAL = "create a.txt then b.txt"
SCRIPT = [
    Action(kind=CODE, code="open('a.txt','w').write('1')"),
    Action(kind=CODE, code="open('b.txt','w').write('2')"),
    Action(kind=FINISH, result="done"),
]


def demo_primitives(base_dir: str) -> dict:
    """Bring your own loop: propose -> apply -> checkpoint; crash; recover; continue."""
    ws = os.path.join(base_dir, "ws")
    os.makedirs(ws, exist_ok=True)
    snaps = os.path.join(base_dir, "snaps")
    ck = os.path.join(base_dir, "ck")
    ej = os.path.join(base_dir, "e.jsonl")
    model = ScriptableMockModel(SCRIPT)

    # --- your loop, run exactly one step, then "crash" -------------------------
    world = Workspace(ws, snaps)
    store = FileCheckpointStore(ck)
    ledger = FileEffectLedger(ej, "run")
    history: list[StepRecord] = []
    action = model.propose(GOAL, history)
    world.execute(action.code)                 # apply with YOUR tools (Workspace is executable)
    history.append(StepRecord(step=0, action=action, returncode=0))
    checkpoint(GOAL, history, world, store, ledger, step=0)
    # crash here: a.txt written + checkpointed; b.txt not yet.

    # --- fresh objects over the SAME durable dirs; recover re-grounds ----------
    world2 = Workspace(ws, snaps)
    store2 = FileCheckpointStore(ck)
    ledger2 = FileEffectLedger(ej, "run")
    rg = recover(world2, store2, ledger2)
    history = list(rg.history)                  # step 0 re-grounded from the cairn (not replayed)

    new_steps = 0
    for step in range(len(history), len(SCRIPT)):
        action = model.propose(GOAL, history)
        if action.kind == FINISH:
            break
        world2.execute(action.code)
        history.append(StepRecord(step=step, action=action, returncode=0))
        checkpoint(GOAL, history, world2, store2, ledger2, step=step)
        new_steps += 1

    return {
        "regrounded": len(rg.history),
        "new_steps": new_steps,
        "files": sorted(f for f in os.listdir(ws) if f.endswith(".txt")),
    }


def demo_agent(base_dir: str) -> dict:
    """Batteries-included: Agent.run() then, after a crash, Agent.resume()."""
    ws = os.path.join(base_dir, "ws")
    os.makedirs(ws, exist_ok=True)
    snaps = os.path.join(base_dir, "snaps")
    ck = os.path.join(base_dir, "ck")
    ej = os.path.join(base_dir, "e.jsonl")

    # Run one step then "crash" (max_steps=1 stops after one execute).
    a1 = Agent(
        ScriptableMockModel(SCRIPT), Workspace(ws, snaps),
        store=FileCheckpointStore(ck), ledger=FileEffectLedger(ej, "run"), max_steps=1,
    )
    a1.run(GOAL)

    # Fresh Agent over the SAME durable dirs -> resume re-grounds and finishes.
    a2 = Agent(
        ScriptableMockModel(SCRIPT), Workspace(ws, snaps),
        store=FileCheckpointStore(ck), ledger=FileEffectLedger(ej, "run"), max_steps=10,
    )
    run = a2.resume(GOAL)
    return {
        "resumed": run.resumed,
        "recovery_tax": run.recovery_tax,
        "finished": run.finished,
        "files": sorted(f for f in os.listdir(ws) if f.endswith(".txt")),
    }


def demo_effect_once(base_dir: str) -> dict:
    """A torn side-effect is resolved exactly-once on recover() (WAL danger window, C3)."""
    ws = os.path.join(base_dir, "ws")
    os.makedirs(ws, exist_ok=True)
    snaps = os.path.join(base_dir, "snaps")
    ck = os.path.join(base_dir, "ck")
    ej = os.path.join(base_dir, "e.jsonl")
    outbox = os.path.join(base_dir, "outbox.txt")   # the external world (NOT the workspace)

    world = Workspace(ws, snaps)
    store = FileCheckpointStore(ck)
    ledger = FileEffectLedger(ej, "run")

    # A normal step, checkpointed (so recover() has a cairn to load).
    action = Action(kind=CODE, code="open('a.txt','w').write('1')")
    world.execute(action.code)
    checkpoint(GOAL, [StepRecord(step=0, action=action, returncode=0)], world, store, ledger, step=0)

    # The effect: write INTENT durably FIRST, do the side-effect, then "crash" (no COMPLETE).
    ledger.append_effect("send_report", "send-1", "check-before-retry", step=1)
    with open(outbox, "a", encoding="utf-8") as f:
        f.write("sent\n")                            # effect happened; crash before complete_effect
    lines_before = _lines(outbox)

    # Recover in fresh objects: the danger window is resolved exactly-once (verify -> skip).
    tool = EffectfulTool(
        "send_report", "check-before-retry",
        run=lambda: open(outbox, "a", encoding="utf-8").write("sent\n"),
        verify=lambda: os.path.exists(outbox) and os.path.getsize(outbox) > 0,
    )
    rg = recover(
        Workspace(ws, snaps), FileCheckpointStore(ck), FileEffectLedger(ej, "run"),
        effect_tools={"send-1": tool},
    )
    return {
        "resolutions": [(r.key, r.action) for r in rg.resolutions],
        "outbox_lines_before": lines_before,
        "outbox_lines_after": _lines(outbox),        # unchanged -> effect happened exactly once
    }


def _lines(path: str) -> int:
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def _ollama_model(model_name: str = "llama3.2"):
    """A real local-model adapter (Ollama) — opt-in; NEVER used by the smoke test / CI.

    Requires a running Ollama (`ollama serve`) and only the stdlib (urllib). Returns an object
    with `propose(goal, history) -> Action`, matching cairn's Model seam. This is deliberately
    naive: it asks the model to reply with ONE line of Python (or `FINISH`). Real apps do their
    own prompt engineering and parsing — the recovery machinery is unchanged either way.
    """
    import json
    import urllib.request

    def propose(goal, history):
        done = "\n".join(f"- {h.action.code}" for h in history) or "(none yet)"
        prompt = (
            f"You are driving a shell-less Python agent toward this goal:\n{goal}\n\n"
            f"Steps done so far:\n{done}\n\n"
            "Reply with EXACTLY ONE line of Python for the next step, or the single word "
            "FINISH if the goal is met. No prose, no code fences."
        )
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=json.dumps({"model": model_name, "prompt": prompt, "stream": False}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            text = json.loads(resp.read())["response"]
        return _parse_action(text)

    return type("OllamaModel", (), {"propose": staticmethod(propose)})()


def _parse_action(text: str) -> Action:
    """Map raw model text to an Action (naive: first non-empty line; FINISH ends the run)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    first = lines[0] if lines else "FINISH"
    if first.upper().startswith("FINISH"):
        return Action(kind=FINISH, result=first)
    return Action(kind=CODE, code=first)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="cairn_byom_") as base:
        p = demo_primitives(os.path.join(base, "primitives"))
        print(f"[primitives] regrounded={p['regrounded']} new_steps={p['new_steps']} files={p['files']}")

        a = demo_agent(os.path.join(base, "agent"))
        print(f"[agent]      resumed={a['resumed']} recovery_tax={a['recovery_tax']} "
              f"finished={a['finished']} files={a['files']}")

        e = demo_effect_once(os.path.join(base, "effect"))
        print(f"[effect]     resolutions={e['resolutions']} "
              f"outbox_before={e['outbox_lines_before']} outbox_after={e['outbox_lines_after']} "
              f"(exactly once)")

    if os.environ.get("CAIRN_OLLAMA") == "1":
        # Opt-in real-model run — requires `ollama serve`. Never invoked by CI.
        with tempfile.TemporaryDirectory(prefix="cairn_byom_ollama_") as base:
            ws = os.path.join(base, "ws"); os.makedirs(ws)
            agent = Agent(
                _ollama_model(), Workspace(ws, os.path.join(base, "snaps")),
                store=FileCheckpointStore(os.path.join(base, "ck")),
                ledger=FileEffectLedger(os.path.join(base, "e.jsonl"), "run"),
                max_steps=6,
            )
            run = agent.run(GOAL)
            print(f"[ollama]     finished={run.finished} steps={run.steps} "
                  f"files={sorted(os.listdir(ws))}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the smoke test to verify it passes**

Run: `python -m pytest tests/test_example_byom.py -q`
Expected: PASS (3 tests).

- [ ] **Step 5: Run the example directly (human-visible sanity)**

Run: `python examples/byom_recovery.py`
Expected: three lines printed —
```
[primitives] regrounded=1 new_steps=1 files=['a.txt', 'b.txt']
[agent]      resumed=True recovery_tax=1 finished=True files=['a.txt', 'b.txt']
[effect]     resolutions=[('send-1', 'skip')] outbox_before=1 outbox_after=1 (exactly once)
```
(No `[ollama]` line unless `CAIRN_OLLAMA=1`.)

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS (134 + 3 = 137).

- [ ] **Step 7: Commit**

```bash
git add examples/byom_recovery.py tests/test_example_byom.py
git commit -m "M4 AP-4: BYOM example (primitives + Agent + exactly-once effect) + CI smoke test"
```

---

## Task 3: The guide (`docs/guide/recovery-in-your-agent.md`) + README pointer

**Files:**
- Create: `docs/guide/recovery-in-your-agent.md`
- Modify: `README.md`

- [ ] **Step 1: Write the guide**

Create `docs/guide/recovery-in-your-agent.md` with this content:

````markdown
# Recovery in your own agent (BYOM)

Cairn is a **bring-your-own-model** recovery library. You keep your model, your keys, and your
tools; Cairn adds **crash-recovery** to your agent through *Re-grounding Recovery (RGR)* — on
resume it loads the last checkpoint, restores your world, re-observes reality, reconciles the
step that was in flight, resolves any half-finished side-effect **exactly once**, and re-grounds
a compact history so your model continues instead of starting over.

> **Status (honest scope).** Cairn is **0.x** and not published. In the deterministic reference
> harness, RGR beats cold restart and the effect WAL yields zero duplicate effects. The headline
> claim (RGR beats cold restart on a *live* model, "C1") is **not yet confirmed** — it awaits a
> powered live-LLM study. This library exists partly so you can reproduce the evidence on *your*
> model. See [`docs/research/claims-registry.md`](../research/claims-registry.md).

## Install

Cairn isn't on PyPI (0.x). Use it from a checkout:

```bash
git clone https://github.com/STiFLeR7/Cairn && cd Cairn
pip install -e ".[dev]"     # or: PYTHONPATH=src python your_script.py
```

## The two seams you bring

- **A `Model`** — any object with `propose(goal, history) -> Action`. Cairn ships
  `ScriptableMockModel` for tests/examples; a real local adapter (Ollama) is shown below.
- **A `World`** — the observable, snapshottable thing your agent acts on. Cairn ships
  `Workspace` (a local filesystem workspace). For the `Agent` loop the World must also be
  *executable* (`execute(code) -> ExecResult`); `Workspace` is.

Recovery infrastructure (`FileCheckpointStore`, `FileEffectLedger`) is bundled — you don't
implement it.

## Path A — keep your own loop (primitives)

Call `checkpoint(...)` after each step; call `recover(...)` after a crash and continue from the
history it returns:

```python
from cairn import (Action, StepRecord, Workspace,
                   FileCheckpointStore, FileEffectLedger, checkpoint, recover)

world  = Workspace("ws", "snaps")
store  = FileCheckpointStore("ck")
ledger = FileEffectLedger("effects.jsonl", "run")

history = []
for step, action in enumerate(your_actions):
    world.execute(action.code)                 # apply with YOUR tools
    history.append(StepRecord(step=step, action=action, returncode=0))
    checkpoint(goal, history, world, store, ledger, step=step)

# ... process dies mid-run ...

rg = recover(world, store, ledger)             # load -> restore -> re-observe -> reconcile
history = list(rg.history)                      # re-grounded prior steps (summaries, not replay)
# continue your loop from `history`
```

`recover()` with **no checkpoint** returns an empty history (start fresh). The `goal` is *not* a
parameter to `recover` — it is carried inside the loaded checkpoint.

## Path B — batteries-included (`Agent`)

Same mechanism, none of the loop:

```python
from cairn import Agent, Workspace, FileCheckpointStore, FileEffectLedger

agent = Agent(your_model, Workspace("ws", "snaps"),
              store=FileCheckpointStore("ck"),
              ledger=FileEffectLedger("effects.jsonl", "run"))

run = agent.run(goal)        # checkpoints every executed step
# ... crash ...
run = agent.resume(goal)     # re-grounds via recover(), then finishes
print(run.resumed, run.recovery_tax, run.finished)
```

`recovery_tax` is the number of steps executed *after* resume — the cost of recovery vs. a cold
restart that would redo everything. `Agent` has no task oracle: it reports whether the model
finished and hands back the full history + last checkpoint so you apply your own success test.

## Side-effects, exactly once

An irreversible effect (send an email, charge a card) must survive a crash *between* "it
happened" and "we recorded that it happened". Wrap it as an `EffectfulTool` and register its
intent in the ledger **before** acting; on resume, `recover(effect_tools=...)` resolves the
danger window:

```python
from cairn import EffectfulTool

ledger.append_effect("send_report", "send-1", "check-before-retry", step=step)  # INTENT first
do_the_send()                                                                    # then the effect
# crash before we can mark it complete ...

tool = EffectfulTool("send_report", "check-before-retry",
                     run=do_the_send,
                     verify=lambda: report_already_sent())   # True iff it already happened
rg = recover(world, store, ledger, effect_tools={"send-1": tool})
# verify() -> True  =>  Resolution(action="skip"): the effect is NOT re-executed (no duplicate)
```

Tool classes: `safe-to-retry` (redo), `check-before-retry` (verify then redo-or-skip),
`never-retry` (escalate — a human decides). See
[`docs/design/effect-safety-protocol.md`](../design/effect-safety-protocol.md).

## Run it

The full, runnable version of all three snippets is
[`examples/byom_recovery.py`](../../examples/byom_recovery.py):

```bash
python examples/byom_recovery.py
```

It uses a deterministic mock model — no API key, no network — and is exercised in CI.

## Use a real local model (Ollama)

`examples/byom_recovery.py` includes `_ollama_model()`, a stdlib-only adapter that satisfies the
`Model` seam by calling a local [Ollama](https://ollama.com) server. It is **opt-in** and never
runs in CI (no network there). To try it:

```bash
ollama serve &            # in another shell
ollama pull llama3.2
CAIRN_OLLAMA=1 python examples/byom_recovery.py
```

Swapping `ScriptableMockModel` for `_ollama_model()` is the whole point of BYOM: the recovery
machinery is identical — only the model changed. Reproduce the recovery-vs-cold-restart
comparison on your own model and report what you find.

## What's next

- Full names and signatures: [public API reference](public-api-reference.md).
- Why re-grounding (not replay): [`docs/concepts/recovery-fidelity.md`](../concepts/recovery-fidelity.md).
````

- [ ] **Step 2: Add a discoverability pointer to the README**

In `README.md`, inside the `## Project status` fenced code block (the one listing `python -m pytest`, `python examples/recovery_demo.py`, ...), add one line:

```bash
python examples/byom_recovery.py     # BYOM: add crash-recovery to YOUR agent (mock model, offline)
```

And immediately **after** that code block's closing ``` , add this paragraph:

```markdown
**Adding recovery to your own agent?** See the BYOM guide —
[docs/guide/recovery-in-your-agent.md](docs/guide/recovery-in-your-agent.md) — for the
primitives path, the `Agent` loop, exactly-once effects, and a local-model (Ollama) run.
```

(Leave the stale Phase-5 status numbers alone; the tracker/status refresh is AP-5's job.)

- [ ] **Step 3: Verify links resolve**

Run: `python -m pytest -q`  (docs change: confirm nothing broke — still 137)
Manually confirm the relative paths in the guide exist:
- `../research/claims-registry.md`, `../design/effect-safety-protocol.md`,
  `../concepts/recovery-fidelity.md`, `../../examples/byom_recovery.py`, `public-api-reference.md`.

Run: `ls docs/research/claims-registry.md docs/design/effect-safety-protocol.md docs/concepts/recovery-fidelity.md examples/byom_recovery.py`
Expected: all four exist (the fifth, `public-api-reference.md`, is created in Task 4 — note it here and verify at the end of Task 4).

- [ ] **Step 4: Commit**

```bash
git add docs/guide/recovery-in-your-agent.md README.md
git commit -m "M4 AP-4: BYOM guide (recovery in your own agent) + README pointer"
```

---

## Task 4: Public API reference (`docs/guide/public-api-reference.md`)

**Files:**
- Create: `docs/guide/public-api-reference.md`

- [ ] **Step 1: Write the reference**

Create `docs/guide/public-api-reference.md`. It documents exactly the names in `cairn.__all__`
(as of AP-4). The implementer MUST open `src/cairn/__init__.py` and confirm the list matches
before committing (if a name differs, fix the doc, not the code).

````markdown
# Public API reference

Everything below is re-exported from the top-level `cairn` package (`from cairn import ...`).
Cairn is **0.x**; this surface is stabilizing but not frozen until v1.0 (held — see the
[claims registry](../research/claims-registry.md)).

## Types

| Name | What it is |
|---|---|
| `Action` | One proposed step: `Action(kind, code="", result="")`. `kind` is `"code"` or `"finish"`. |
| `StepRecord` | An executed step: `StepRecord(step, action, returncode=0, stdout="", stderr="")`. The unit of `history`. |
| `Checkpoint` | A durable checkpoint (the "cairn"). Transparent alias of the internal `ContinuationState`. |
| `Regrounded` | Result of `recover()`: `.history`, `.resolutions`, `.plan` (`plan is None` ⇒ no checkpoint). |
| `Resolution` | What recovery did to one effect: `.key`, `.tool_class`, `.action` (`"redo"`/`"skip"`/`"escalate"`), `.detail`. |
| `ResumePlan` | The reconciled resume plan (torn-step + danger window) produced during `recover()`. |
| `AgentRun` | Outcome of `Agent.run`/`.resume`: `.finished`, `.steps`, `.checkpoints`, `.history`, `.final_state`, `.resumed`, `.recovery_tax`, `.resolutions`. |

## Contracts (Protocols you implement or accept)

| Name | Method surface |
|---|---|
| `World` | `snapshot() -> str`, `restore(snap_id) -> None`, `digest() -> dict`. (The `Agent` loop also needs `execute(code, cwd=None) -> ExecResult`.) |
| `CheckpointStore` | `checkpoint(state, snap_id, effect_offset) -> str`, `load_latest() -> tuple | None`. |
| `EffectLedger` | `append_effect(intent, key, tool_class, step)`, `complete_effect(key)`, `current_offset() -> int`, `list_effects_since(offset)`. |

## Effect safety

| Name | What it is |
|---|---|
| `EffectfulTool` | An injected irreversible effect: `EffectfulTool(name, tool_class, run=None, verify=None)`. |
| `EscalationRequired` | Raised when a `never-retry` effect is found in the danger window (unless `escalate=False`). |

## Reference implementations (bundled)

| Name | What it is |
|---|---|
| `Workspace` | A local-filesystem `World` (also executable). `Workspace(workspace_dir, snapshots_dir, sandbox=None, interpreter=None)`. |
| `FileCheckpointStore` | File-backed `CheckpointStore`. `FileCheckpointStore(ckpt_dir)`. |
| `FileEffectLedger` | Append-only file-backed `EffectLedger`. `FileEffectLedger(path, ledger_id="default")`. |

## Primitives (bring your own loop)

**`checkpoint(goal, history, world, store, ledger, *, step, model_version="", harness_version="") -> Checkpoint`**
Distill `history` into a cairn, snapshot the world, and persist atomically. Returns the durable
`Checkpoint`.

**`recover(world, store, ledger, *, effect_tools=None, escalate=True) -> Regrounded`**
The full RGR protocol: load latest checkpoint → `world.restore` → re-observe → reconcile the torn
step → resolve the effect danger window (exactly-once) → re-ground a minimal history. No durable
checkpoint ⇒ empty history (start fresh). The goal is carried in the checkpoint, not passed here.

**`regrounded_history(plan_steps) -> list[StepRecord]`**
Low-level helper: reconstruct a minimal history from a checkpoint's *done* steps (faithful
summaries, ~80 chars each — re-grounding, not byte-exact replay). Used internally by `recover()`.

## Opt-in loop (batteries-included)

**`Agent(model, world, *, store, ledger, effect_tools=None, max_steps=20, escalate=True, model_version="byom", harness_version="")`**
- `run(goal) -> AgentRun` — drive from scratch, checkpointing each executed step.
- `resume(goal) -> AgentRun` — re-ground via `recover()` and continue; falls back to `run` when
  there is no checkpoint.

## Version

`cairn.__version__` — the package version (currently `0.x`).
````

- [ ] **Step 2: Verify the reference matches the actual surface**

Run:
```bash
PYTHONPATH=src python -c "import cairn; print(sorted(cairn.__all__))"
```
Confirm every non-`__version__` name in the printed list appears in the reference table above,
and no documented name is absent from `__all__`. Fix the doc to match if needed.

- [ ] **Step 3: Verify the Task 3 forward-link now resolves**

Run: `ls docs/guide/public-api-reference.md`
Expected: exists (the guide's `public-api-reference.md` link now resolves).

- [ ] **Step 4: Commit**

```bash
git add docs/guide/public-api-reference.md
git commit -m "M4 AP-4: public API reference (cairn.__all__ surface)"
```

---

## Task 5: Minimal CI (`.github/workflows/ci.yml`)

**Why:** The AP-4 DoD requires the example smoke test to run **in CI**. The repo has no workflow
yet. Add a minimal one that runs the suite (the smoke test rides along) on the supported Pythons.
**No publish/release/tag steps** — the v1.0 hold and "outward action needs approval" rule stand.

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [master, "milestone-*", "phase-*"]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install (dev extras)
        run: pip install -e ".[dev]"
      - name: Run test suite (includes the BYOM example smoke test)
        run: python -m pytest -q
```

- [ ] **Step 2: Validate the workflow is well-formed YAML**

Run:
```bash
python -c "import yaml, sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('ci.yml OK')"
```
Expected: `ci.yml OK`. (If PyYAML isn't installed, install it just for this check:
`pip install pyyaml` — it is a dev-only convenience, not a project dependency.)

- [ ] **Step 3: Confirm the local suite still passes (what CI will run)**

Run: `python -m pytest -q`
Expected: PASS (137).

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "M4 AP-4: minimal CI (pytest on 3.10/3.12; runs the BYOM smoke test)"
```

---

## Final review (after all tasks)

Dispatch a holistic reviewer over the whole AP-4 diff (`git diff master...HEAD`). Confirm:
- **Public-API only** in the example/guide (no `cairn.runtime.*` reach-through except the aliased exports).
- **No secrets / no `.env`** touched; CI has no publish/release/tag steps (v1.0 hold intact).
- **Honest scope** present in the guide (C1 not confirmed; reproduce-on-your-model framing).
- **Smoke test runs offline** (no network); Ollama path is opt-in and unreferenced by tests.
- Full suite green (137); example prints the expected three lines.
- ADR-0007 respected (goal/model/effect wired in the example, never the library).

Then use **superpowers:finishing-a-development-branch** to open the PR to `master`
(Option 2 — push + PR; do not self-merge without the maintainer review the user runs).

## Self-review (author checklist — done at plan-write time)

1. **Spec coverage (design §9 item 4 + §8):** example both paths ✅ (Task 2 `demo_primitives`+`demo_agent`); exactly-once effect ✅ (`demo_effect_once`); mock-model CI smoke test ✅ (Task 2 + Task 5); Ollama documented + CI-gated ✅ (example `_ollama_model` + guide + never in tests); "Recovery in your own agent" guide ✅ (Task 3); public API reference ✅ (Task 4). DoD "example smoke test in CI" ✅ (Task 5 runs pytest). DoD "local path documented + CI-gated" ✅.
2. **Placeholder scan:** no TBDs; every code/doc block is complete and copy-runnable. The Ollama adapter is fully defined (`_parse_action` included), documented as naive rather than left blank.
3. **Type/name consistency:** `FileCheckpointStore`/`FileEffectLedger` are the concrete `CheckpointStore`/`EffectLedger` from `cairn.runtime.*` (verified against the code); `Action(kind, code, result)`, `StepRecord(step, action, returncode)`, `EffectfulTool(name, tool_class, run, verify)`, `recover(world, store, ledger, *, effect_tools, escalate)`, `Agent(..., store=, ledger=, max_steps=)`, `append_effect(intent, key, tool_class, step)` all match the current signatures. `recover()` takes **no** `goal` (design-spec §5's `recover(goal, ...)` is superseded by the AP-2/AP-3 implementation — recorded as the AP-3 deviation; AP-5 updates the spec).
4. **Scope discipline:** AP-4 adds no recovery mechanism and does not touch validated paths; the only `src/` change is two additive aliased exports needed for a public-surface-only example. CHANGELOG + tracker/status refresh are explicitly deferred to AP-5.
5. **Governance:** CI workflow runs tests only (no publish/release/tag); 0.x and v1.0 hold untouched; ADR-0007/0009 honored; branch-per-phase (all on `milestone-4-ap4-example-docs`, PR to master).
