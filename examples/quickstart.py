"""Quickstart: assemble a harness and run a baseline task end-to-end.

Run from the repo root:

    PYTHONPATH=src python examples/quickstart.py

Everything concrete (the task, the scripted model) is wired *here*, in the example —
the library hardcodes none of it.
"""

from cairn.app import build_harness
from cairn.model import CODE, Action
from cairn.model_mock import ScriptableMockModel
from cairn.tasks import CreateFileTask


def main() -> None:
    task = CreateFileTask("out.txt", "hello cairn")
    # The scripted model emits code-as-action; swap this for a real ModelProvider plugin.
    model = ScriptableMockModel([Action(kind=CODE, code="open('out.txt','w').write('hello cairn')")])

    harness, runtime = build_harness(model=model)
    result = harness.run(task)

    print(f"success={result.success} steps={result.steps} checkpoints={result.checkpoints}")
    latest = runtime.load_latest()
    if latest:
        state, snap, offset = latest
        print(f"latest checkpoint: snap={snap} effect_offset={offset} "
              f"goal={state.durable_core.intent.root_goal!r}")


if __name__ == "__main__":
    main()
