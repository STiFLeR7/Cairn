"""Sealed P2.4 queue-policy fixture, registered without changing Cairn core."""

from __future__ import annotations

import json
import runpy
from pathlib import Path

from cairn.eval import recoverybench


NAME = "p24_queue_policy"
_AUTHOR_OUTPUT = Path(__file__).resolve().parents[1] / "results" / "phase-2" / "p24-author-output-opencode.json"
_CASES = json.loads(_AUTHOR_OUTPUT.read_text(encoding="utf-8"))["acceptance_cases"]


def _source(*, priority: bool, retry: bool, dispatch: bool, batches: bool) -> str:
    return "\n\n".join(
        (
            "def priority_band(priority: int) -> int:\n"
            + ("    return 0 if priority >= 80 else 1 if priority >= 50 else 2 if priority >= 20 else 3 if priority >= 0 else 4" if priority else "    ..."),
            "def retry_schedule(attempt: int) -> list[int]:\n"
            + ("    return [2 ** index for index in range(attempt)]" if retry else "    ..."),
            "def dispatchable_ids(tasks: dict[str, str]) -> list[str]:\n"
            + ("    return sorted(task_id for task_id, state in tasks.items() if state in {'ready', 'queued'})" if dispatch else "    ..."),
            "def partition_batches(ids: list[str], batch_size: int) -> list[list[str]]:\n"
            + ("    return [ids[index:index + batch_size] for index in range(0, len(ids), batch_size)]" if batches else "    ..."),
        )
    ) + "\n"


STEPS = (
    _source(priority=True, retry=False, dispatch=False, batches=False),
    _source(priority=True, retry=True, dispatch=False, batches=False),
    _source(priority=True, retry=True, dispatch=True, batches=False),
    _source(priority=True, retry=True, dispatch=True, batches=True),
)


def _function_passes(project: dict, name: str) -> bool:
    try:
        return all(project[name](*case["args"]) == case["expected"] for case in _CASES if case["function"] == name)
    except Exception:
        return False


def ordered_progress(root: Path) -> int:
    try:
        project = runpy.run_path(str(root / "project.py"))
    except Exception:
        return 0
    progress = 0
    for name in ("priority_band", "retry_schedule", "dispatchable_ids", "partition_batches"):
        if not _function_passes(project, name):
            return progress
        progress += 1
    return progress


def register_fixture() -> None:
    recoverybench._PROGRESS[NAME] = ordered_progress
    recoverybench._FIXTURE_STEPS[NAME] = STEPS
