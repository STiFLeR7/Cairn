"""LiveModelProvider — adapt a real LLM to the ModelProvider seam (code-as-action).

The harness asks a model to act by proposing *code*. This adapter:

  1. renders ``(goal, history)`` into a text prompt,
  2. calls an **injected transport** (``prompt -> reply text``), and
  3. parses the reply into an :class:`Action` — a fenced code block becomes a
     ``CODE`` action; a completion sentinel becomes ``FINISH``.

No vendor, model id, or API key is hardcoded (ADR-0007 / ADR-0010): the transport is
injected, the prompt renderer and parser are overridable, and the one bundled factory
(:func:`anthropic_transport`) lazily imports an optional SDK and reads its key from the
environment — so importing this module, and running it in CI with a fake transport,
never needs the SDK or the network. Like ``ScriptableMockModel``, this is a *plugin*
behind the seam; the harness still only ever sees a ``ModelProvider``.
"""

from __future__ import annotations

import os
import re
from typing import Callable, Optional

from .model import CODE, FINISH, Action, StepRecord

# A transport turns a rendered prompt into the model's raw reply text. This is the
# single seam a real provider plugs into; tests pass a plain function.
Transport = Callable[[str], str]

DEFAULT_FINISH_SENTINEL = "TASK_COMPLETE"

DEFAULT_SYSTEM = (
    "You are a long-horizon coding agent that acts by writing Python code. "
    "On each turn, reply with EXACTLY ONE fenced Python code block that makes progress "
    "toward the goal; the code runs in a sandboxed working directory and its "
    "stdout/stderr/return code are fed back to you on the next turn. Do not explain "
    "outside the code block. When the goal is fully achieved, reply with exactly "
    f"{DEFAULT_FINISH_SENTINEL} and nothing else."
)

_CODE_FENCE = re.compile(r"```(?:[a-zA-Z0-9_+-]+)?\s*\n(.*?)```", re.DOTALL)


def render_prompt(goal: str, history: list[StepRecord]) -> str:
    """Render the goal + observed history into a user prompt. Overridable per provider."""
    lines = [f"GOAL:\n{goal}\n"]
    if history:
        lines.append("HISTORY (your prior actions and the observations they produced):")
        for rec in history:
            lines.append(f"\n--- step {rec.step} ---")
            if rec.action.kind == CODE and rec.action.code:
                lines.append("you ran:\n" + rec.action.code)
            lines.append(f"returncode: {rec.returncode}")
            if rec.stdout:
                lines.append("stdout:\n" + rec.stdout)
            if rec.stderr:
                lines.append("stderr:\n" + rec.stderr)
    else:
        lines.append("HISTORY: (none yet — this is the first step)")
    lines.append(
        "\nReply with the next single Python code block, or "
        f"{DEFAULT_FINISH_SENTINEL} if the goal is already complete."
    )
    return "\n".join(lines)


def parse_action(text: str, *, finish_sentinel: str = DEFAULT_FINISH_SENTINEL) -> Action:
    """Parse a model reply into an Action.

    Priority: a fenced code block -> ``CODE``; else the finish sentinel -> ``FINISH``;
    else ``FINISH`` flagged as unparseable — so a malformed reply ends the run rather
    than looping forever, and the reason is recorded honestly in ``Action.result``.
    """
    if not text:
        return Action(kind=FINISH, result="empty model reply")
    match = _CODE_FENCE.search(text)
    if match:
        code = match.group(1).strip()
        if code:
            return Action(kind=CODE, code=code)
    if finish_sentinel and finish_sentinel in text:
        return Action(kind=FINISH, result="model signaled completion")
    return Action(kind=FINISH, result="no code block or completion signal in reply")


class LiveModelProvider:
    """A ``ModelProvider`` backed by a real LLM via an injected transport.

    ``transport`` maps a rendered prompt to the model's raw reply text. ``render`` and
    ``parse`` default to the module functions but are injectable, so the prompt strategy
    and reply parsing are not hardcoded into the harness.
    """

    def __init__(
        self,
        transport: Transport,
        *,
        render: Callable[[str, list[StepRecord]], str] = render_prompt,
        parse: Optional[Callable[[str], Action]] = None,
        finish_sentinel: str = DEFAULT_FINISH_SENTINEL,
    ) -> None:
        self._transport = transport
        self._render = render
        self._finish_sentinel = finish_sentinel
        self._parse = parse or (lambda t: parse_action(t, finish_sentinel=finish_sentinel))

    def propose(self, goal: str, history: list[StepRecord]) -> Action:
        prompt = self._render(goal, history)
        reply = self._transport(prompt)
        return self._parse(reply)


class LiveModelConfigError(RuntimeError):
    """Raised when a live transport cannot be configured (missing key or SDK)."""


def anthropic_transport(
    *,
    model: str,
    system: str = DEFAULT_SYSTEM,
    max_tokens: int = 2048,
    temperature: float = 0.0,
    api_key: Optional[str] = None,
    api_key_env: str = "ANTHROPIC_API_KEY",
    client: Optional[object] = None,
) -> Transport:
    """Build a :data:`Transport` over the Anthropic Messages API.

    ``model`` is required and injected — no model id is hardcoded. The API key comes from
    ``api_key`` or the ``api_key_env`` environment variable, never from source. The
    ``anthropic`` SDK is an optional dependency imported lazily; pass ``client`` (any
    object exposing ``.messages.create(...)``) to inject a fake in tests — so this factory
    is exercisable without the SDK or the network.
    """
    if client is None:
        key = api_key or os.environ.get(api_key_env)
        if not key:
            raise LiveModelConfigError(
                f"no API key: set ${api_key_env} or pass api_key= (and install 'cairn[live]')"
            )
        try:
            import anthropic  # optional dependency
        except ImportError as exc:  # pragma: no cover - only without the SDK installed
            raise LiveModelConfigError(
                "the 'anthropic' package is required for anthropic_transport "
                "(install 'cairn[live]')"
            ) from exc
        client = anthropic.Anthropic(api_key=key)

    def complete(prompt: str) -> str:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return _text_from_message(message)

    return complete


def _text_from_message(message: object) -> str:
    """Join the text blocks of an Anthropic Messages response into one string."""
    content = getattr(message, "content", None)
    if content is None:
        return ""
    parts: list[str] = []
    for block in content:
        text = getattr(block, "text", None)
        if text is None and isinstance(block, dict):
            text = block.get("text")
        if text:
            parts.append(text)
    return "".join(parts)
