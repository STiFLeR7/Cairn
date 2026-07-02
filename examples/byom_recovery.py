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
