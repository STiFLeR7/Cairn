"""Re-observe the world on resume — step 2 of RGR ("re-observe before re-act").

After the Runtime restores the workspace, the Code Harness reads the *actual* world (the
workspace digest + the effect ledger since the checkpoint offset) before deciding anything.
This is what separates re-grounding from "restore bytes and charge ahead".
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..runtime.digest import world_digest


@dataclass
class ObservedWorld:
    """What the agent actually sees after restore — the ground truth for reconciliation."""

    digest: dict[str, str] = field(default_factory=dict)
    effects_since: list[dict] = field(default_factory=list)
    workspace_dir: str = ""


def observe_world(runtime, since_offset: int, workspace_dir: str = "") -> ObservedWorld:
    """Read the restored workspace digest and the effects since the checkpoint offset."""
    wd = workspace_dir or getattr(runtime, "workspace_dir", "")
    return ObservedWorld(
        digest=world_digest(wd),
        effects_since=list(runtime.list_effects_since(since_offset)),
        workspace_dir=wd,
    )
