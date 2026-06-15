"""Assembly — wire a harness from injected components.

`build_harness` hardcodes nothing: the model, sandbox, tools, storage dir, and limits
are all passed in (ADR-0007). Concrete tasks/models live in examples and tests, not here.
"""

from __future__ import annotations

import tempfile
from typing import Optional

from .harness.agent_loop import CodeHarness
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
) -> tuple[CodeHarness, LocalRuntime]:
    """Assemble a Code Harness + Local Runtime. `model` is required and injected."""
    base_dir = base_dir or tempfile.mkdtemp(prefix="cairn_")
    runtime = LocalRuntime(base_dir=base_dir, sandbox=sandbox)
    harness = CodeHarness(
        runtime=runtime,
        model=model,
        tools=tools or ToolRegistry(),
        model_version=model_version,
        max_steps=max_steps,
    )
    return harness, runtime
