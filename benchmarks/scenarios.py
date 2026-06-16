"""Concrete benchmark scenarios (the injected task/model wiring).

A scenario is a multi-step file-writing task driven by a deterministic scripted model —
enough structure to exercise recovery (multiple steps, completed work, an external effect)
while staying fully reproducible (ADR-0009).
"""

from __future__ import annotations

import os
from typing import Optional

from cairn.eval.scenario import EffectSpec, Scenario
from cairn.live_controls import Budget, record_to
from cairn.model import CODE, Action
from cairn.model_live import LiveModelProvider, Transport, anthropic_transport, openrouter_transport
from cairn.model_mock import ScriptableMockModel
from cairn.task import Task


class MultiFileTask(Task):
    def __init__(self, names):
        self.names = names

    @property
    def goal(self):
        return "create files: " + ", ".join(self.names)

    def is_complete(self, workspace):
        return all(os.path.isfile(os.path.join(workspace, n)) for n in self.names)


def _names(n, prefix="step"):
    return [f"{prefix}{i}.txt" for i in range(n)]


def _script(names):
    return [Action(kind=CODE, code=f"open({n!r},'w').write({n!r})") for n in names]


def multi_file_scenario(n: int = 4, version: str = "mock", prefix: str = "step") -> Scenario:
    names = _names(n, prefix)
    return Scenario(
        name=f"multifile-{n}",
        n_steps=n,
        task_factory=lambda: MultiFileTask(names),
        model_factory=lambda: ScriptableMockModel(_script(names)),
        model_version=version,
    )


def effectful_scenario(n: int = 4, effect_step: int = 2, version: str = "mock") -> Scenario:
    names = _names(n)
    return Scenario(
        name=f"effectful-{n}@{effect_step}",
        n_steps=n,
        task_factory=lambda: MultiFileTask(names),
        model_factory=lambda: ScriptableMockModel(_script(names)),
        model_version=version,
        effect=EffectSpec(key="send-report", at_step=effect_step),
    )


# --- live-pipeline wiring (Milestone M1, AP-0040) ---------------------------
# The same scenarios driven through LiveModelProvider + an injected transport, so the
# live study runner is identical offline (fake transport) and live (anthropic_transport).


def fake_multifile_transport(names) -> Transport:
    """A deterministic, offline stand-in for a real model on the multi-file task.

    Stateless: it infers how many steps are already done from the rendered prompt
    (`render_prompt` emits one ``--- step N ---`` header per history entry) and returns a
    fenced code block creating the next file, or ``TASK_COMPLETE``. This is exactly what a
    real model is *expected* to do — swap in :func:`build_live_transport` to find out
    whether it actually does, with no other change to the runner.
    """

    def transport(prompt: str) -> str:
        done = prompt.count("--- step ")
        if done >= len(names):
            return "TASK_COMPLETE"
        target = names[done]
        return f"```python\nopen({target!r}, 'w').write({target!r})\n```"

    return transport


def batching_multifile_transport(names) -> Transport:
    """A deterministic model that creates **all** files in a single action, then finishes.

    The dual of :func:`fake_multifile_transport`: it mimics a capable real model that
    one-shots a batchable task (as `openrouter/owl-alpha` did live), so a crash injected at
    step `k > 0` never fires. Used to verify the benchmark **detects a non-injected (vacuous)
    failure** rather than silently scoring it as a recovery.
    """

    def transport(prompt: str) -> str:
        if prompt.count("--- step ") == 0:
            body = "\n".join(f"open({n!r}, 'w').write({n!r})" for n in names)
            return f"```python\n{body}\n```"
        return "TASK_COMPLETE"

    return transport


def live_multi_file_scenario(
    n: int = 4, transport: Optional[Transport] = None, *, version: str = "live-fake", prefix: str = "step"
) -> Scenario:
    names = _names(n, prefix)
    transport = transport or fake_multifile_transport(names)
    return Scenario(
        name=f"live-multifile-{n}",
        n_steps=n,
        task_factory=lambda: MultiFileTask(names),
        model_factory=lambda: LiveModelProvider(transport),
        model_version=version,
    )


def live_effectful_scenario(
    n: int = 4, effect_step: int = 2, transport: Optional[Transport] = None, *, version: str = "live-fake"
) -> Scenario:
    names = _names(n)
    transport = transport or fake_multifile_transport(names)
    return Scenario(
        name=f"live-effectful-{n}@{effect_step}",
        n_steps=n,
        task_factory=lambda: MultiFileTask(names),
        model_factory=lambda: LiveModelProvider(transport),
        model_version=version,
        effect=EffectSpec(key="send-report", at_step=effect_step),
    )


def build_live_transport(
    model: str,
    *,
    provider: str = "anthropic",
    api_key_env: Optional[str] = None,
    transcript_path: Optional[str] = None,
    max_calls: Optional[int] = None,
    max_chars: Optional[int] = None,
) -> Transport:
    """Construct the REAL transport for a live run (AP-0040, **GATED**).

    ``provider`` selects a bundled factory: ``"anthropic"`` (needs ``ANTHROPIC_API_KEY`` +
    the ``cairn[live]`` extra) or ``"openrouter"`` (OpenAI-compatible, stdlib-only; needs an
    OpenRouter key). The base transport is wrapped with a transcript recorder (so the run
    replays offline afterwards) and a :class:`Budget` ceiling (so it cannot run away on
    cost). Calling this without a key raises ``LiveModelConfigError`` — the live path is
    wired but **inert** until explicitly enabled with a key and an approved spend.
    """
    kw = {"api_key_env": api_key_env} if api_key_env else {}
    if provider == "anthropic":
        transport = anthropic_transport(model=model, **kw)
    elif provider == "openrouter":
        transport = openrouter_transport(model=model, **kw)
    else:
        raise ValueError(f"unknown provider {provider!r} (expected 'anthropic' or 'openrouter')")
    if transcript_path:
        transport = record_to(transport, transcript_path, model_version=model)
    if max_calls is not None or max_chars is not None:
        transport = Budget(max_calls=max_calls, max_chars=max_chars).wrap(transport)
    return transport
