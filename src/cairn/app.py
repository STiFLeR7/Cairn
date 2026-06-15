"""Assembly — wire a harness from injected components.

`build_harness` hardcodes nothing: the model, sandbox, tools, storage dir, and limits
are all passed in (ADR-0007). Concrete tasks/models live in examples and tests, not here.
"""

from __future__ import annotations

import tempfile
from typing import Mapping, Optional

from .harness.agent_loop import CodeHarness
from .harness.effects import EffectfulTool
from .model import ModelProvider
from .runtime import LocalRuntime
from .sandbox import Sandbox
from .tools import ToolRegistry


def build_harness(
    *,
    model: ModelProvider,
    base_dir: Optional[str] = None,
    sandbox: Optional[Sandbox] = None,
    tools: Optional[ToolRegistry] = None,
    model_version: str = "mock",
    max_steps: int = 20,
    effect_tools: Optional[Mapping[str, EffectfulTool]] = None,
    escalate_never_retry: bool = True,
) -> tuple[CodeHarness, LocalRuntime]:
    """Assemble a Code Harness + Local Runtime. `model` is required and injected.

    Pass the same `base_dir` to a second call to obtain a *fresh* harness over existing
    durable state — that is the resume case (`harness.resume(task)`).
    """
    base_dir = base_dir or tempfile.mkdtemp(prefix="cairn_")
    runtime = LocalRuntime(base_dir=base_dir, sandbox=sandbox)
    harness = CodeHarness(
        runtime=runtime,
        model=model,
        tools=tools or ToolRegistry(),
        model_version=model_version,
        max_steps=max_steps,
        effect_tools=effect_tools,
        escalate_never_retry=escalate_never_retry,
    )
    return harness, runtime
