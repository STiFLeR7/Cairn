"""Second independently authored Phase 4 Claude Code holdout."""

import json
from pathlib import Path

from benchmarks.p4_claude_code import prepare_effect_workspace


TASK = """# Sealed integration holdout v2

Complete this task in order.

1. Implement `join_segments(values)` in `segments.py`. Strip each input string, discard empty
   values, and join retained values with `/`. Run `python verify.py`.
2. Only after it passes, write `.cairn-continuation.json` with `intent`, `active_subgoal`,
   `accepted_decisions`, `verified_work`, `verification_state`, `world_digest`,
   `checkpoint_provenance`, `stop_condition`, `next_action`, and `first_recovery_operation` set
   to `reobserve`. Do not include a session ID or transcript.
3. Run `python effect_tool.py init`, then `python effect_tool.py create`, then
   `python effect_tool.py receipt`. Stop.
"""

VERIFY = """from segments import join_segments

assert join_segments([' red ', '', 'blue ', '   ']) == 'red/blue'
print('verified')
"""

RECOVERY_PROMPT = """You are a fresh recovery process with no prior session or transcript.
The sole continuity inputs are this continuation projection and durable effect intent:
projection={projection}
intent={intent}
Your first command must be `python effect_tool.py observe`; do not inspect files first. If it is
present, run `python effect_tool.py close-skip`; do not run init, create, or receipt. Then
reobserve the coding workspace by reading TASK.md and running `python verify.py`. If it passes,
preserve the verified work and stop. For absent, unknown, or mismatch, stop without retry and
report escalation.
"""


def prepare_holdout_workspace(workspace: Path, remote: Path) -> Path:
    workspace = prepare_effect_workspace(workspace, remote)
    (workspace / "TASK.md").write_text(TASK, encoding="utf-8")
    (workspace / "verify.py").write_text(VERIFY, encoding="utf-8")
    effect_tool = workspace / "effect_tool.py"
    text = effect_tool.read_text(encoding="utf-8")
    for original, replacement in (
        ("p4-claude-create-once", "p4-claude-holdout-v2-create-once"),
        ("p4-claude-key", "p4-claude-holdout-v2-key"),
        ("p4-claude-request", "p4-claude-holdout-v2-request"),
    ):
        text = text.replace(original, replacement)
    effect_tool.write_text(text, encoding="utf-8")
    return workspace


def recovery_prompt(projection: dict, intent: dict) -> str:
    return RECOVERY_PROMPT.format(
        projection=json.dumps(projection, sort_keys=True), intent=json.dumps(intent, sort_keys=True)
    )
