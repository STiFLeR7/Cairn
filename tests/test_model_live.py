"""Tests for the live ModelProvider adapter (AP-0038).

All tests run offline: the transport is the only seam, so a plain function or an
injected fake client stands in for a real LLM. No network, no SDK required.
"""

from __future__ import annotations

import pytest

from cairn.model import CODE, FINISH, Action, ModelProvider, StepRecord
from cairn.model_live import (
    DEFAULT_FINISH_SENTINEL,
    LiveModelConfigError,
    LiveModelProvider,
    anthropic_transport,
    parse_action,
    render_prompt,
)


def test_live_provider_satisfies_modelprovider_protocol():
    provider = LiveModelProvider(transport=lambda p: "```python\nx = 1\n```")
    assert isinstance(provider, ModelProvider)


def test_propose_returns_code_action_from_fenced_block():
    provider = LiveModelProvider(
        transport=lambda p: "here you go:\n```python\nopen('a.txt', 'w').write('hi')\n```"
    )
    action = provider.propose("make a.txt", [])
    assert action.kind == CODE
    assert "a.txt" in action.code


def test_propose_returns_finish_on_sentinel():
    provider = LiveModelProvider(transport=lambda p: DEFAULT_FINISH_SENTINEL)
    assert provider.propose("done", []).kind == FINISH


def test_parse_prefers_code_over_sentinel():
    # If a reply carries both, the code wins: the model still has an action to take.
    action = parse_action("```\nprint(1)\n```\nTASK_COMPLETE")
    assert action.kind == CODE


def test_parse_malformed_reply_finishes_safely():
    action = parse_action("I think we are basically done, but no code here")
    assert action.kind == FINISH
    assert "no code" in action.result


def test_parse_empty_reply_finishes():
    assert parse_action("").kind == FINISH


def test_render_prompt_includes_goal_and_observations():
    history = [
        StepRecord(
            step=0,
            action=Action(kind=CODE, code="print('x')"),
            returncode=1,
            stderr="boom",
        )
    ]
    prompt = render_prompt("reach the goal", history)
    assert "reach the goal" in prompt
    assert "boom" in prompt
    assert "step 0" in prompt


def test_transport_receives_the_rendered_goal():
    seen = {}

    def fake(prompt: str) -> str:
        seen["prompt"] = prompt
        return "```python\npass\n```"

    LiveModelProvider(transport=fake).propose("unique-goal-token", [])
    assert "unique-goal-token" in seen["prompt"]


# --- anthropic_transport factory: injected fake client, no network/SDK -----------


class _FakeBlock:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeMessage:
    def __init__(self, text: str) -> None:
        self.content = [_FakeBlock(text)]


class _FakeMessages:
    def __init__(self, reply: str) -> None:
        self._reply = reply
        self.seen: dict = {}

    def create(self, **kwargs):
        self.seen = kwargs
        return _FakeMessage(self._reply)


class _FakeClient:
    def __init__(self, reply: str) -> None:
        self.messages = _FakeMessages(reply)


def test_anthropic_transport_with_injected_client():
    client = _FakeClient("```python\nopen('o', 'w')\n```")
    transport = anthropic_transport(model="claude-test-id", client=client)
    out = transport("hello prompt")

    assert "open('o'" in out
    assert client.messages.seen["model"] == "claude-test-id"  # model is injected, not hardcoded
    assert client.messages.seen["messages"][0]["content"] == "hello prompt"

    # end-to-end through the provider
    provider = LiveModelProvider(transport=transport)
    assert provider.propose("g", []).kind == CODE


def test_anthropic_transport_missing_key_raises():
    with pytest.raises(LiveModelConfigError):
        anthropic_transport(model="m", api_key=None, api_key_env="CAIRN_DEFINITELY_UNSET_KEY")
