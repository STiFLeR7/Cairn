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
# Fallback for models that emit an XML-style tool call instead of a markdown fence
# (e.g. `<…_arg_value>CODE</…_arg_value>`). General over the wrapper tag — not a model id.
_TOOL_ARG_VALUE = re.compile(r"<[a-zA-Z0-9_]*arg_value>\s*(.*?)\s*</[a-zA-Z0-9_]*arg_value>", re.DOTALL)


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

    Priority:

      1. a fenced code block -> ``CODE``;
      2. an XML-style tool-call arg value -> ``CODE`` (some models emit tool calls);
      3. the finish sentinel -> ``FINISH``;
      4. an *unfenced* reply that nonetheless **compiles as Python** -> ``CODE`` (some
         models omit fences entirely — `compile()` distinguishes bare code from prose);
      5. otherwise ``FINISH`` flagged as unparseable — so a malformed reply ends the run
         rather than looping forever, recorded honestly in ``Action.result``.

    Steps 2 and 4 were added from live observations (a stealth model mixed fenced, XML
    tool-call, and bare-code outputs across steps); none of them is model-specific.
    """
    if not text:
        return Action(kind=FINISH, result="empty model reply")
    for pattern in (_CODE_FENCE, _TOOL_ARG_VALUE):
        match = pattern.search(text)
        if match:
            code = match.group(1).strip()
            if code:
                return Action(kind=CODE, code=code)
    # Unfenced reply. A model may bundle bare code with a trailing completion signal in the
    # same turn; prefer doing the action (completion then lands on the next turn). `compile()`
    # separates code from prose; the sentinel is stripped before the check.
    has_finish = bool(finish_sentinel) and finish_sentinel in text
    candidate = text.replace(finish_sentinel, "").strip() if has_finish else text.strip()
    if candidate and _looks_like_python(candidate):
        return Action(kind=CODE, code=candidate)
    if has_finish:
        return Action(kind=FINISH, result="model signaled completion")
    return Action(kind=FINISH, result="no code block or completion signal in reply")


def _looks_like_python(text: str) -> bool:
    """True if ``text`` parses as a Python module — used to accept unfenced code."""
    try:
        compile(text, "<live-reply>", "exec")
        return True
    except (SyntaxError, ValueError):
        return False


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


def openrouter_transport(
    *,
    model: str,
    system: str = DEFAULT_SYSTEM,
    max_tokens: int = 2048,
    temperature: float = 0.0,
    api_key: Optional[str] = None,
    api_key_env: str = "OPENROUTER_API_KEY",
    url: str = "https://openrouter.ai/api/v1/chat/completions",
    referer: str = "https://github.com/STiFLeR7/Cairn",
    title: str = "Cairn",
    timeout: float = 120.0,
    request: Optional[Callable[[dict], dict]] = None,
) -> Transport:
    """Build a :data:`Transport` over OpenRouter's OpenAI-compatible chat API.

    ``model`` is required and injected (a provider/model slug) — no model id is hardcoded.
    The key comes from ``api_key`` or ``$api_key_env``, never from source. The
    HTTP call uses only the standard library (no SDK / no new dependency); pass ``request``
    (a callable ``payload_dict -> response_dict``) to inject a fake in tests — so this
    factory is exercisable offline. This is a second instance of the ADR-0010 pattern
    (a vendor is just another ``*_transport`` factory; the harness is unchanged).
    """
    if request is None:
        key = api_key or os.environ.get(api_key_env)
        if not key:
            raise LiveModelConfigError(
                f"no API key: set ${api_key_env} or pass api_key= for openrouter_transport"
            )
        request = _urllib_json_poster(url, key, referer=referer, title=title, timeout=timeout)

    def complete(prompt: str) -> str:
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        return _content_from_chat(request(payload))

    return complete


def _urllib_json_poster(
    url: str, key: str, *, referer: str, title: str, timeout: float
) -> Callable[[dict], dict]:
    """A stdlib JSON POST-er (payload dict -> response dict) for OpenAI-compatible APIs."""
    import json
    import urllib.request

    def post(payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", f"Bearer {key}")
        req.add_header("Content-Type", "application/json")
        if referer:
            req.add_header("HTTP-Referer", referer)  # OpenRouter attribution headers
        if title:
            req.add_header("X-Title", title)
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # pragma: no cover - network
            return json.loads(resp.read().decode("utf-8"))

    return post


def _content_from_chat(data: dict) -> str:
    """Extract the assistant text from an OpenAI-compatible chat response."""
    if isinstance(data, dict) and data.get("error"):
        raise LiveModelConfigError(f"chat API error: {data['error']}")
    choices = (data or {}).get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return message.get("content") or ""
