"""Concrete benchmark scenarios (the injected task/model wiring).

A scenario is a multi-step file-writing task driven by a deterministic scripted model —
enough structure to exercise recovery (multiple steps, completed work, an external effect)
while staying fully reproducible (ADR-0009).
"""

from __future__ import annotations

import os

from cairn.eval.scenario import EffectSpec, Scenario
from cairn.model import CODE, Action
from cairn.model_mock import ScriptableMockModel
from cairn.task import Task


class MultiFileTask(Task):
    def __init__(self, names):
        self.names = names

    @property
    def goal(self):
        return "create files: " + ", ".join(self.names)

    def is_complete(self, workspace):
        return all(os.path.isfile(os.path.join(workspace, n)) for n in self.names)


def _names(n, prefix="step"):
    return [f"{prefix}{i}.txt" for i in range(n)]


def _script(names):
    return [Action(kind=CODE, code=f"open({n!r},'w').write({n!r})") for n in names]


def multi_file_scenario(n: int = 4, version: str = "mock", prefix: str = "step") -> Scenario:
    names = _names(n, prefix)
    return Scenario(
        name=f"multifile-{n}",
        n_steps=n,
        task_factory=lambda: MultiFileTask(names),
        model_factory=lambda: ScriptableMockModel(_script(names)),
        model_version=version,
    )


def effectful_scenario(n: int = 4, effect_step: int = 2, version: str = "mock") -> Scenario:
    names = _names(n)
    return Scenario(
        name=f"effectful-{n}@{effect_step}",
        n_steps=n,
        task_factory=lambda: MultiFileTask(names),
        model_factory=lambda: ScriptableMockModel(_script(names)),
        model_version=version,
        effect=EffectSpec(key="send-report", at_step=effect_step),
    )
