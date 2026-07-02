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
