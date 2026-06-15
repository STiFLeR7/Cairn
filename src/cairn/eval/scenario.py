"""Scenario model + run helpers (AP-0028).

A `Scenario` is a reproducible recovery situation with everything injected (task, model,
optional external effect) — the eval framework hardcodes no concrete task/model (ADR-0007).
The standard external effect is modeled as appending a line to an *outbox* file kept beside
the workspace (so `restore_workspace` does not revert it — effects act on the external world).
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import Callable, Optional

from ..app import build_harness
from ..harness.agent_loop import RunResult
from ..harness.effects import CHECK_BEFORE_RETRY, EffectfulTool, perform_effect
from ..harness.failure import InjectedFailure, crash_after
from ..model import ModelProvider
from ..runtime.digest import world_digest
from ..task import Task
from .failure import FailureType


@dataclass
class EffectSpec:
    """An external irreversible effect performed during the run, at `at_step`."""

    key: str
    at_step: int
    tool_class: str = CHECK_BEFORE_RETRY


@dataclass
class Scenario:
    name: str
    n_steps: int
    task_factory: Callable[[], Task]
    model_factory: Callable[[], ModelProvider]
    model_version: str = "mock"
    effect: Optional[EffectSpec] = None


@dataclass
class RunOutcome:
    success: bool
    executed: int          # steps executed in this run (recovery cost when recovering)
    final_digest: dict
    outbox_count: int
    result: Optional[RunResult] = None


# --- external-effect model --------------------------------------------------
def outbox_path(base_dir: str) -> str:
    return os.path.join(base_dir, "outbox.txt")


def outbox_count(base_dir: str) -> int:
    p = outbox_path(base_dir)
    if not os.path.exists(p):
        return 0
    with open(p, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def _append_outbox(base_dir: str) -> None:
    with open(outbox_path(base_dir), "a", encoding="utf-8") as f:
        f.write("fired\n")


def effect_tool(scenario: Scenario, base_dir: str) -> EffectfulTool:
    return EffectfulTool(
        scenario.effect.key,
        scenario.effect.tool_class,
        run=lambda: _append_outbox(base_dir),
        verify=lambda: outbox_count(base_dir) > 0,
    )


# --- harness assembly -------------------------------------------------------
def harness_for(scenario: Scenario, base_dir: str):
    effects = {scenario.effect.key: effect_tool(scenario, base_dir)} if scenario.effect else None
    return build_harness(
        model=scenario.model_factory(),
        base_dir=base_dir,
        model_version=scenario.model_version,
        max_steps=scenario.n_steps + 2,
        effect_tools=effects,
    )


def wipe_workspace(rt) -> None:
    ws = rt.workspace_dir
    for name in os.listdir(ws):
        p = os.path.join(ws, name)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)


def _completed_effect_hook(scenario: Scenario, rt, base_dir: str):
    """Fire the effect (INTENT -> run -> COMPLETE) when the run reaches `at_step`."""
    spec = scenario.effect
    tool = effect_tool(scenario, base_dir)

    def hook(step: int) -> None:
        if step == spec.at_step:
            perform_effect(rt, tool, spec.key, step=step)

    return hook


def _torn_then_crash_hook(scenario: Scenario, rt, base_dir: str, k: int):
    """At step k: write INTENT durable, perform the external effect, then crash before
    COMPLETE — a realistic torn effect in the danger window (mirrors the Phase 4 e2e)."""
    spec = scenario.effect

    def do(step: int) -> None:
        rt.append_effect(spec.key, spec.key, spec.tool_class, step)  # INTENT durable (I1)
        _append_outbox(base_dir)                                     # effect executes
        # COMPLETE intentionally not written — the crash follows

    return crash_after(k, do=do)


# --- runs -------------------------------------------------------------------
def run_reference(scenario: Scenario, base_dir: str) -> RunOutcome:
    """The uninterrupted run — the fidelity yardstick."""
    h, rt = harness_for(scenario, base_dir)
    hook = _completed_effect_hook(scenario, rt, base_dir) if scenario.effect else None
    res = h.run(scenario.task_factory(), step_hook=hook)
    return RunOutcome(
        success=res.success,
        executed=res.steps,
        final_digest=world_digest(rt.workspace_dir),
        outbox_count=outbox_count(base_dir),
        result=res,
    )


def run_until_failure(scenario: Scenario, base_dir: str, k: int, ftype: FailureType = FailureType.CRASH):
    """Run with a failure injected at step `k`; leave the durable state on disk."""
    h, rt = harness_for(scenario, base_dir)
    if scenario.effect and scenario.effect.at_step == k:
        hook = _torn_then_crash_hook(scenario, rt, base_dir, k)
    else:
        hook = crash_after(k)
    try:
        h.run(scenario.task_factory(), step_hook=hook)
    except InjectedFailure:
        pass
    return rt
