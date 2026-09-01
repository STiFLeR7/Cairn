"""Direct OpenHands P5.1 capability control; not a Cairn adapter or workload."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import time
import uuid
from pathlib import Path

from openhands.sdk.agent import Agent
from openhands.sdk.context.condenser import LLMSummarizingCondenser
from openhands.sdk.conversation import Conversation
from openhands.sdk.llm import Message, MessageToolCall, TextContent
from openhands.sdk.testing import TestLLM
from openhands.sdk.tool import Tool
from openhands.tools.terminal import TerminalTool


CONVERSATION_ID = uuid.UUID("62afe2a8-3f9e-4a99-a166-b2b15f8d2741")
TOOL_CONVERSATION_ID = uuid.UUID("24c30ac1-a39f-4a5d-a168-32132a2d7893")
HOLD_CONVERSATION_ID = uuid.UUID("d15908f1-3be0-4b2d-8f05-041df63f8b90")


def agent() -> Agent:
    agent_llm = TestLLM.from_messages([], model="p5-openhands-agent-control")
    summary_llm = TestLLM.from_messages(
        [Message(role="assistant", content=[TextContent(text="P5 native condensation summary")])],
        model="p5-openhands-summary-control",
    )
    return Agent(
        llm=agent_llm,
        tools=[],
        include_default_tools=[],
        condenser=LLMSummarizingCondenser(llm=summary_llm, max_size=12, keep_first=4),
    )


def tool_agent() -> Agent:
    return Agent(
        llm=TestLLM.from_messages(
            [
                Message(
                    role="assistant",
                    content=[TextContent(text="")],
                    tool_calls=[
                        MessageToolCall(
                            id="call_p5_terminal_control",
                            name=TerminalTool.name,
                            arguments=json.dumps(
                                {"command": "echo P5_OPENHANDS_TOOL_EVENT > p5_openhands_tool_marker.txt"}
                            ),
                            origin="completion",
                        )
                    ],
                ),
                Message(role="assistant", content=[TextContent(text="P5 tool control complete")]),
            ],
            model="p5-openhands-tool-control",
        ),
        tools=[Tool(name=TerminalTool.name)],
        include_default_tools=[],
    )
def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def conversation(root: Path, selected_agent: Agent | None = None, conversation_id: uuid.UUID = CONVERSATION_ID):
    return Conversation(
        agent=selected_agent or agent(),
        workspace=root / "workspace",
        persistence_dir=root / "persistence",
        conversation_id=conversation_id,
        visualizer=None,
        delete_on_close=False,
    )


def snapshot(host) -> dict[str, object]:
    events = host.state.events
    view = host.state.view.events
    return {
        "event_count": len(events),
        "event_types": [type(event).__name__ for event in events],
        "view_count": len(view),
        "view_types": [type(event).__name__ for event in view],
        "view_digest": digest([str(event) for event in view]),
    }


def write(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def create_and_compact(root: Path) -> dict[str, object]:
    host = conversation(root)
    try:
        for number in range(16):
            host.send_message(f"P5 OpenHands native capability control message {number}")
        before = snapshot(host)
        host.condense()
        after = snapshot(host)
        return {
            "mode": "create-and-compact",
            "pid": os.getpid(),
            "sdk_version": importlib.metadata.version("openhands-sdk"),
            "conversation_id": str(CONVERSATION_ID),
            "before": before,
            "after": after,
            "native_condensation_event": "Condensation" in after["event_types"],
            "active_view_changed": before["view_digest"] != after["view_digest"],
        }
    finally:
        host.close()


def resume(root: Path, conversation_id: uuid.UUID = CONVERSATION_ID) -> dict[str, object]:
    host = conversation(root, conversation_id=conversation_id)
    try:
        state = snapshot(host)
        return {
            "mode": "fresh-process-resume",
            "pid": os.getpid(),
            "sdk_version": importlib.metadata.version("openhands-sdk"),
            "conversation_id": str(conversation_id),
            "state": state,
            "expected_durable_event": "Condensation" if conversation_id == CONVERSATION_ID else "MessageEvent",
            "expected_durable_event_preserved": (
                "Condensation" if conversation_id == CONVERSATION_ID else "MessageEvent"
            ) in state["event_types"],
        }
    finally:
        host.close()


def tool(root: Path) -> dict[str, object]:
    host = conversation(root, selected_agent=tool_agent(), conversation_id=TOOL_CONVERSATION_ID)
    try:
        host.send_message("Create the requested marker through the terminal tool.")
        host.run()
        state = snapshot(host)
        marker = root / "workspace" / "p5_openhands_tool_marker.txt"
        action_index = state["event_types"].index("ActionEvent")
        observation_index = state["event_types"].index("ObservationEvent")
        return {
            "mode": "native-tool-event-control",
            "pid": os.getpid(),
            "sdk_version": importlib.metadata.version("openhands-sdk"),
            "conversation_id": str(TOOL_CONVERSATION_ID),
            "state": state,
            "action_before_observation": action_index < observation_index,
            "workspace_marker": {
                "exists": marker.exists(),
                "content": marker.read_text(encoding="utf-8").strip() if marker.exists() else None,
            },
        }
    finally:
        host.close()


def hold(root: Path, output: Path) -> None:
    host = conversation(root, conversation_id=HOLD_CONVERSATION_ID)
    try:
        host.send_message("P5 OpenHands crash-control durable event")
        ready = {
            "mode": "crash-control-ready",
            "pid": os.getpid(),
            "conversation_id": str(HOLD_CONVERSATION_ID),
            "state": snapshot(host),
        }
        write(output, ready)
        print(json.dumps(ready, sort_keys=True), flush=True)
        time.sleep(300)
    finally:
        host.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("create", "resume", "tool", "hold"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--conversation-id", choices=("default", "hold"), default="default")
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=True)
    if args.mode == "hold":
        hold(args.root, args.output)
        return
    result = {
        "create": create_and_compact,
        "resume": lambda root: resume(root, HOLD_CONVERSATION_ID if args.conversation_id == "hold" else CONVERSATION_ID),
        "tool": tool,
    }[args.mode](args.root)
    write(args.output, result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
