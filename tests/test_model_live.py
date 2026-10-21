"""Tests for the live ModelProvider adapter (AP-0038).

All tests run offline: the transport is the only seam, so a plain function or an
injected fake client stands in for a real LLM. No network, no SDK required.
"""

from __future__ import annotations

import subprocess
import time

import pytest

from cairn.model import CODE, FINISH, Action, ModelProvider, StepRecord
from cairn.model_live import (
    DEFAULT_FINISH_SENTINEL,
    LiveModelConfigError,
    LiveModelProvider,
    claude_code_transport,
    codex_cli_transport,
    anthropic_transport,
    openai_chat_transport,
    openrouter_transport,
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


def test_parse_extracts_code_from_xml_tool_call():
    # Some models emit an XML-style tool call instead of a markdown fence (observed live).
    reply = (
        "<longcat_tool_call>python_code\n"
        "<longcat_arg_key>code</longcat_arg_key>\n"
        "<longcat_arg_value>with open('a.txt','w') as f:\n    f.write('')</longcat_arg_value>\n"
        "</longcat_tool_call>"
    )
    action = parse_action(reply)
    assert action.kind == CODE
    assert "open('a.txt'" in action.code


def test_parse_extracts_code_from_json_terminal_action():
    # Nemotron emits this OpenAI-style action envelope rather than a Markdown fence.
    action = parse_action('{"action":"python","code":"open(\'a.txt\', \'w\').write(\'ok\')"}')
    assert action.kind == CODE
    assert "a.txt" in action.code


def test_parse_extracts_code_from_json_code_only_action():
    action = parse_action('{"code":"open(\'a.txt\', \'w\').write(\'ok\')"}')
    assert action.kind == CODE
    assert "a.txt" in action.code


def test_parse_translates_json_read_file_action():
    action = parse_action('{"action":"read_file","path":"project.py"}')
    assert action.kind == CODE
    assert "Path('project.py').read_text()" in action.code


def test_parse_translates_json_edit_file_action():
    action = parse_action(
        '{"action":"edit_file","file_path":"project.py","from":"old","to":"new"}'
    )
    assert action.kind == CODE
    assert "source.replace(old, new, 1)" in action.code


def test_parse_translates_nested_json_write_file_action():
    action = parse_action(
        '{"action":{"name":"write_file","args":{"path":"project.py","content":"next"}}}'
    )
    assert action.kind == CODE
    assert "Path('project.py').write_text('next')" in action.code


def test_parse_accepts_unfenced_code_that_compiles():
    # Observed live: a model emitted bare Python with no fence on some steps.
    action = parse_action("with open('b.txt','w') as f:\n    f.write('')")
    assert action.kind == CODE
    assert "b.txt" in action.code


def test_parse_bare_code_with_trailing_sentinel_does_the_action():
    # Observed live: a model emitted bare code AND a trailing TASK_COMPLETE in one turn.
    action = parse_action("with open('b.txt','w') as f:\n    f.write('')\n\nTASK_COMPLETE")
    assert action.kind == CODE
    assert "b.txt" in action.code


def test_parse_pure_sentinel_still_finishes():
    assert parse_action("TASK_COMPLETE").kind == FINISH


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


# --- openrouter_transport factory: injected fake request, no network -------------


def test_openrouter_transport_with_injected_request():
    captured = {}

    def fake_request(payload: dict) -> dict:
        captured["payload"] = payload
        return {"choices": [{"message": {"content": "```python\nopen('o','w')\n```"}}]}

    transport = openrouter_transport(model="openrouter/owl-alpha", request=fake_request)
    out = transport("hello prompt")

    assert "open('o'" in out
    assert captured["payload"]["model"] == "openrouter/owl-alpha"  # injected, not hardcoded
    assert captured["payload"]["messages"][-1]["content"] == "hello prompt"
    assert captured["payload"]["temperature"] == 0.0  # determinism lever

    provider = LiveModelProvider(transport=transport)
    assert provider.propose("g", []).kind == CODE


def test_openrouter_transport_surfaces_api_error():
    transport = openrouter_transport(
        model="m", request=lambda payload: {"error": {"message": "rate limited"}}
    )
    with pytest.raises(LiveModelConfigError):
        transport("p")


def test_openrouter_transport_missing_key_raises():
    with pytest.raises(LiveModelConfigError):
        openrouter_transport(model="m", api_key=None, api_key_env="CAIRN_DEFINITELY_UNSET_KEY")


# --- generic OpenAI-compatible transport: any router is the same factory (AP-0049) -----


def test_openai_chat_transport_is_endpoint_agnostic():
    captured = {}

    def fake_request(payload: dict) -> dict:
        captured["payload"] = payload
        return {"choices": [{"message": {"content": "TASK_COMPLETE"}}]}

    # Groq / ZenMux / OpenRouter are all THIS factory with a different url + key env.
    transport = openai_chat_transport(
        model="llama-3.3-70b-versatile",
        url="https://api.groq.com/openai/v1/chat/completions",
        api_key_env="GROQ_API_KEY",
        request=fake_request,
    )
    assert transport("p").strip() == "TASK_COMPLETE"
    assert captured["payload"]["model"] == "llama-3.3-70b-versatile"  # injected, not hardcoded
    assert captured["payload"]["temperature"] == 0.0


def test_openai_chat_transport_includes_an_explicit_extra_body():
    captured = {}

    def fake_request(payload: dict) -> dict:
        captured["payload"] = payload
        return {"choices": [{"message": {"content": "TASK_COMPLETE"}}]}

    transport = openai_chat_transport(
        model="m", url="https://example.test/chat", api_key_env="UNUSED",
        extra_body={"chat_template_kwargs": {"force_nonempty_content": True}},
        request=fake_request,
    )
    transport("p")
    assert captured["payload"]["chat_template_kwargs"]["force_nonempty_content"] is True


def test_openai_chat_transport_enforces_a_total_request_deadline():
    def stalled_request(_: dict) -> dict:
        time.sleep(0.2)
        return {"choices": [{"message": {"content": "TASK_COMPLETE"}}]}

    transport = openai_chat_transport(
        model="m", url="https://example.test/chat", api_key_env="UNUSED",
        timeout=0.01, request=stalled_request,
    )
    with pytest.raises(LiveModelConfigError, match="timed out"):
        transport("p")


def test_claude_code_transport_is_no_tools_and_returns_its_result():
    captured = {}

    class Result:
        returncode = 0
        stderr = ""
        stdout = '{"is_error": false, "result": "```python\\nprint(1)\\n```"}'

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return Result()

    transport = claude_code_transport(model="haiku", run=fake_run)
    assert transport("prompt") == "```python\nprint(1)\n```"
    assert captured["args"][:6] == [
        "claude", "-p", "--safe-mode", "--no-session-persistence", "--tools", "",
    ]
    assert "--system-prompt" in captured["args"]
    assert "low" in captured["args"]
    assert "--json-schema" in captured["args"]
    assert captured["args"][captured["args"].index("--model") + 1] == "haiku"
    assert captured["kwargs"]["timeout"] == 90.0


def test_parse_action_accepts_bare_python_after_a_reasoning_trace():
    action = parse_action("reasoning</think>\nprint('next action')")
    assert action.kind == CODE
    assert action.code == "print('next action')"


def test_parse_action_discards_a_hallucinated_terminal_result_after_bare_python():
    action = parse_action("print('next action')\nreturncode: 0")
    assert action.kind == CODE
    assert action.code == "print('next action')"


def test_openai_chat_transport_missing_key_raises():
    with pytest.raises(LiveModelConfigError):
        openai_chat_transport(
            model="m", url="https://example/api/v1/chat/completions",
            api_key_env="CAIRN_DEFINITELY_UNSET_KEY",
        )


def test_build_live_transport_routes_known_providers_and_rejects_unknown(monkeypatch):
    import benchmarks.scenarios as scenarios
    from benchmarks.scenarios import OPENAI_COMPATIBLE_PROVIDERS, build_live_transport

    assert {"openrouter", "groq", "zenmux"} <= set(OPENAI_COMPATIBLE_PROVIDERS)
    assert OPENAI_COMPATIBLE_PROVIDERS["openrouter"]["key_env"] == "OPENROUTER_API_KEY"
    # Inert without a key: each OpenAI-compatible provider raises on its own key env.
    for provider, cfg in OPENAI_COMPATIBLE_PROVIDERS.items():
        monkeypatch.delenv(cfg["key_env"], raising=False)
        with pytest.raises(LiveModelConfigError):
            build_live_transport("some/model", provider=provider)
    captured = []
    monkeypatch.setattr(
        scenarios, "claude_code_transport",
        lambda **kwargs: captured.append(kwargs) or (lambda _prompt: "TASK_COMPLETE"),
    )
    assert build_live_transport("haiku", provider="claude_code")("p") == "TASK_COMPLETE"
    assert captured == [{"model": "haiku"}]
    # An unknown provider is a clear configuration error, not a silent default.
    with pytest.raises(ValueError, match="unknown provider"):
        build_live_transport("m", provider="not-a-provider")


def test_nim_coding_payload_is_limited_to_documented_models(monkeypatch):
    import benchmarks.scenarios as scenarios

    captured = []
    monkeypatch.setattr(
        scenarios,
        "openai_chat_transport",
        lambda **kwargs: captured.append(kwargs) or (lambda _prompt: "TASK_COMPLETE"),
    )
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "test-key")

    scenarios.build_live_transport("nvidia/nemotron-3-super-120b-a12b", provider="nvidia_nim")
    scenarios.build_live_transport("nvidia/nemotron-3.5-lightning-30b-a3b", provider="nvidia_nim")

    assert captured[0]["extra_body"] == {"chat_template_kwargs": {"force_nonempty_content": True}}
    assert captured[1]["extra_body"] is None


@pytest.fixture(autouse=True)
def _fake_codex_home(tmp_path, monkeypatch):
    """Point the Codex home source at a tmp dir holding a fake auth.json (never the user's)."""
    home = tmp_path / "codex-home-source"
    home.mkdir()
    (home / "auth.json").write_text('{"fake": true}', encoding="utf-8")
    (home / "AGENTS.md").write_text("user instructions that must not leak", encoding="utf-8")
    (home / "hooks.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(home))
    return home


def _codex_fake(reply: str | None, *, returncode: int = 0, stderr: str = "model: gpt-test\n"):
    captured = {}

    class Result:
        pass

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        out = args[args.index("-o") + 1]
        if reply is not None:
            with open(out, "w", encoding="utf-8") as f:
                f.write(reply)
        r = Result()
        r.returncode, r.stderr, r.stdout = returncode, stderr, ""
        return r

    return fake_run, captured


def test_codex_cli_transport_is_sandboxed_and_returns_reply(monkeypatch):
    monkeypatch.setattr("cairn.model_live.shutil.which", lambda c: None)
    fake_run, captured = _codex_fake('{"action": "python", "code": "print(1)"}')
    transport = codex_cli_transport(run=fake_run)
    assert transport("prompt") == '{"action": "python", "code": "print(1)"}'
    args = captured["args"]
    assert args[:4] == ["codex", "exec", "--ephemeral", "--skip-git-repo-check"]
    assert args[args.index("-s") + 1] == "read-only"
    assert "--output-schema" in args and "-m" not in args
    assert args[-1] == "-"
    assert "prompt" in captured["kwargs"]["input"]
    assert captured["kwargs"]["timeout"] == 120.0
    assert transport.observed_models == {"gpt-test"}


def test_codex_cli_transport_passes_model(monkeypatch):
    monkeypatch.setattr("cairn.model_live.shutil.which", lambda c: None)
    fake_run, captured = _codex_fake('{"action": "python", "code": "x"}')
    codex_cli_transport(model="gpt-x", run=fake_run)("p")
    assert captured["args"][captured["args"].index("-m") + 1] == "gpt-x"


def test_codex_cli_transport_resolves_windows_shim(monkeypatch):
    shim = r"C:\npm\codex.cmd"
    monkeypatch.setattr("cairn.model_live.shutil.which", lambda c: shim)
    fake_run, captured = _codex_fake('{"action": "python", "code": "x"}')
    codex_cli_transport(run=fake_run)("p")
    assert captured["args"][0] == shim
    assert captured["kwargs"]["encoding"] == "utf-8"


def test_codex_cli_transport_errors_are_config_errors(monkeypatch):
    monkeypatch.setattr("cairn.model_live.shutil.which", lambda c: None)
    for reply, code in [(None, 0), ("   ", 0), ('{"action": "python", "code": "x"}', 2)]:
        fake_run, _ = _codex_fake(reply, returncode=code)
        with pytest.raises(LiveModelConfigError):
            codex_cli_transport(run=fake_run)("p")

    def missing(*a, **k):
        raise FileNotFoundError("codex")

    with pytest.raises(LiveModelConfigError, match="not found"):
        codex_cli_transport(run=missing)("p")

    def slow(*a, **k):
        raise subprocess.TimeoutExpired("codex", 1)

    with pytest.raises(LiveModelConfigError, match="timed out"):
        codex_cli_transport(run=slow)("p")


def test_build_live_transport_routes_codex_cli(monkeypatch):
    import benchmarks.scenarios as scenarios
    from benchmarks.scenarios import build_live_transport

    captured = []
    monkeypatch.setattr(
        scenarios, "codex_cli_transport",
        lambda **kwargs: captured.append(kwargs) or (lambda _prompt: "TASK_COMPLETE"),
    )
    assert build_live_transport("default", provider="codex_cli")("p") == "TASK_COMPLETE"
    assert captured == [{"model": None}]


def test_build_live_transport_keeps_observed_models(monkeypatch):
    import benchmarks.scenarios as scenarios
    from benchmarks.scenarios import build_live_transport

    def base(_prompt):
        return "TASK_COMPLETE"

    base.observed_models = {"gpt-x"}
    monkeypatch.setattr(scenarios, "codex_cli_transport", lambda **kwargs: base)
    assert build_live_transport("default", provider="codex_cli").observed_models == {"gpt-x"}


def test_codex_cli_transport_isolates_codex_home_and_pins_effort(monkeypatch, _fake_codex_home):
    import os

    monkeypatch.setattr("cairn.model_live.shutil.which", lambda c: None)
    seen = []
    fake_run, captured = _codex_fake('{"action": "python", "code": "x"}')

    def spying_run(args, **kwargs):
        home = kwargs["env"]["CODEX_HOME"]
        seen.append((home, sorted(os.listdir(home))))
        return fake_run(args, **kwargs)

    transport = codex_cli_transport(run=spying_run, codex_home_source=str(_fake_codex_home))
    transport("p")
    transport("p")
    home, files = seen[0]
    assert files == ["auth.json"]
    assert home != str(_fake_codex_home)
    assert seen[1][0] == home  # one isolated home reused for later calls
    with open(os.path.join(home, "auth.json"), encoding="utf-8") as f:
        assert f.read() == '{"fake": true}'
    args = captured["args"]
    assert "--ignore-user-config" in args
    assert args[args.index("-c") + 1] == 'model_reasoning_effort="medium"'
    assert captured["kwargs"]["env"]["PATH"] == os.environ["PATH"]  # rest of the env inherited


def test_codex_cli_transport_default_home_source_is_codex_home_env(monkeypatch, _fake_codex_home):
    import os

    monkeypatch.setattr("cairn.model_live.shutil.which", lambda c: None)
    fake_run, captured = _codex_fake('{"action": "python", "code": "x"}')
    codex_cli_transport(run=fake_run, reasoning_effort=None)("p")
    home = captured["kwargs"]["env"]["CODEX_HOME"]
    assert home != str(_fake_codex_home) and os.listdir(home) == ["auth.json"]
    assert "-c" not in captured["args"]


def test_codex_cli_transport_without_auth_is_a_config_error(monkeypatch, tmp_path):
    monkeypatch.setattr("cairn.model_live.shutil.which", lambda c: None)
    fake_run, _ = _codex_fake('{"action": "python", "code": "x"}')
    empty = tmp_path / "empty-home"
    empty.mkdir()
    with pytest.raises(LiveModelConfigError, match="Codex auth not found"):
        codex_cli_transport(run=fake_run, codex_home_source=str(empty))("p")


def test_run_tree_killing_enforces_timeout():
    import sys

    from cairn.model_live import _run_tree_killing

    start = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        _run_tree_killing([sys.executable, "-c", "import time; time.sleep(30)"], input="",
                          timeout=1, env=None, encoding="utf-8")
    assert time.monotonic() - start < 15


def test_run_tree_killing_returns_completed_process():
    import sys

    from cairn.model_live import _run_tree_killing

    r = _run_tree_killing([sys.executable, "-c", "import sys; print(sys.stdin.read().upper())"],
                          input="hi", timeout=30, env=None, encoding="utf-8")
    assert r.returncode == 0 and r.stdout.strip() == "HI"


def test_claude_code_transport_records_observed_models():
    class Result:
        returncode = 0
        stderr = ""
        stdout = '{"is_error": false, "result": "x", "modelUsage": {"claude-sonnet-x": {}}}'

    transport = claude_code_transport(model="sonnet", run=lambda args, **kw: Result())
    assert transport.observed_models == set()
    transport("p")
    assert transport.observed_models == {"claude-sonnet-x"}


def test_build_live_transport_pins_codex_reasoning_effort_only_when_given(monkeypatch):
    import benchmarks.scenarios as scenarios
    from benchmarks.scenarios import build_live_transport

    captured = []
    monkeypatch.setattr(scenarios, "codex_cli_transport",
                        lambda **kwargs: captured.append(kwargs) or (lambda _prompt: "TASK_COMPLETE"))
    monkeypatch.setattr(scenarios, "claude_code_transport",
                        lambda **kwargs: captured.append(kwargs) or (lambda _prompt: "TASK_COMPLETE"))
    build_live_transport("gpt-6-sol", provider="codex_cli", reasoning_effort="medium")
    build_live_transport("sonnet", provider="claude_code", reasoning_effort="medium")
    assert captured == [{"model": "gpt-6-sol", "reasoning_effort": "medium"}, {"model": "sonnet"}]


def test_build_live_transport_counts_base_calls_and_errors(monkeypatch):
    import benchmarks.scenarios as scenarios
    from benchmarks.scenarios import build_live_transport

    replies = iter([RuntimeError("429 rate limit"), "TASK_COMPLETE"])

    def base(_prompt):
        r = next(replies)
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr(scenarios, "claude_code_transport", lambda **kwargs: base)
    t = build_live_transport("sonnet", provider="claude_code", max_calls=10)
    assert t.call_stats == {"calls": 0, "errors": 0}
    assert t("p") == "TASK_COMPLETE"
    assert t.call_stats == {"calls": 2, "errors": 1}  # the retried attempt is counted
