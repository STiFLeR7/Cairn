"""Tool and ToolRegistry — the injected set of tools available to the agent.

The registry is a generic container; it carries no built-in tools. Whatever tools a
deployment wants are registered into it (no hardcoded toolset — ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional


@dataclass
class Tool:
    name: str
    description: str = ""
    run: Optional[Callable[..., str]] = None


class ToolRegistry:
    def __init__(self, tools: Iterable[Tool] = ()) -> None:
        self._tools: dict[str, Tool] = {}
        for t in tools:
            self.register(t)

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def names(self) -> list[str]:
        return list(self._tools)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
