"""Concrete benchmark scenarios (the injected task/model wiring).

A scenario is a multi-step file-writing task driven by a deterministic scripted model —
enough structure to exercise recovery (multiple steps, completed work, an external effect)
while staying fully reproducible (ADR-0009).
"""

from __future__ import annotations

import os
from typing import Optional

from cairn.eval.chain import Chain, render_oracle_module
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

    def progress(self, workspace):
        # Work unit = one produced file (independent of how the model batches the writes).
        return sum(1 for n in self.names if os.path.isfile(os.path.join(workspace, n)))


# --- non-batchable sequential task (Milestone M2, AP-0043) ------------------
# A hash-chain task: step N+1's required input (the next token) only exists after step N
# calls the oracle, and the oracle advances at most once per process. A capable model cannot
# one-shot it (the M1 NO-GO root cause); a crash at step k leaves a genuine partial chain.


class ChainTask(Task):
    """Extend a salted hash-chain to length `n` by calling an injected `oracle` one step at a
    time. `setup` plants the oracle (bound to the secret `salt`); `is_complete` verifies the
    durable chain via the same salt, so progress cannot be faked without doing the work."""

    def __init__(self, n: int, salt: str):
        self.n = n
        self.salt = salt

    @property
    def goal(self):
        return (
            f"Extend a hash chain to length {self.n}. A Python module `oracle` is in your "
            "working directory. Each step: read the current token with `oracle.current()`, "
            "call `oracle.advance(<current token>)` to commit and obtain the next token, then "
            "print it. The oracle advances at most once per step, so you must take exactly one "
            f"step per action — you cannot finish in a single action. Repeat until "
            f"`oracle.pos()` reaches {self.n}."
        )

    def setup(self, workspace):
        with open(os.path.join(workspace, "oracle.py"), "w", encoding="utf-8") as f:
            f.write(render_oracle_module(self.salt))

    def is_complete(self, workspace):
        return Chain(self.salt, os.path.join(workspace, "chain_state.json")).is_complete(self.n)

    def progress(self, workspace):
        # Work unit = one committed chain link. The per-process guard pins one link per agent
        # action, so here work units and actions coincide exactly (the point of AP-0043/0044).
        return Chain(self.salt, os.path.join(workspace, "chain_state.json")).pos()


# The single, step-agnostic action a correct solver repeats: advance from the current token.
# It is identical every step (the oracle supplies the per-step value), so the scripted mock
# and the fake transport need no knowledge of the secret tokens.
CHAIN_STEP_CODE = "import oracle; print(oracle.advance(oracle.current()))"


def _chain_salt(n: int, tag: str = "chain") -> str:
    """A deterministic per-scenario secret (reproducible; no RNG — ADR-0009)."""
    return f"{tag}-{n}-secret"


def chain_scenario(n: int = 4, version: str = "mock", salt: Optional[str] = None) -> Scenario:
    salt = salt or _chain_salt(n)
    return Scenario(
        name=f"chain-{n}",
        n_steps=n,
        task_factory=lambda: ChainTask(n, salt),
        model_factory=lambda: ScriptableMockModel([Action(kind=CODE, code=CHAIN_STEP_CODE)] * n),
        model_version=version,
    )


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


def fake_chain_transport(n: int) -> Transport:
    """Offline stand-in for a real model on the chain task: emit the step-agnostic advance
    action until `n` steps are done, then finish. Stateless — it counts the rendered step
    headers, exactly as a correct one-step-at-a-time solver would proceed."""

    def transport(prompt: str) -> str:
        if prompt.count("--- step ") >= n:
            return "TASK_COMPLETE"
        return f"```python\n{CHAIN_STEP_CODE}\n```"

    return transport


def batching_chain_transport(n: int) -> Transport:
    """A model that *tries* to one-shot the chain in a single action — and cannot.

    The first action loops `advance` `n` times; the per-process guard raises on the 2nd call,
    so the action errors with only one token committed. Used to prove batching is impossible:
    the task stays incomplete (`pos == 1 < n`), so a crash at `k > 1` would have real progress
    to recover. The dual of :func:`fake_chain_transport`."""

    def transport(prompt: str) -> str:
        if prompt.count("--- step ") == 0:
            body = (
                "import oracle\n"
                "t = oracle.current()\n"
                f"for _ in range({n}):\n"
                "    t = oracle.advance(t)\n"
                "    print(t)"
            )
            return f"```python\n{body}\n```"
        return "TASK_COMPLETE"

    return transport


def live_chain_scenario(
    n: int = 4, transport: Optional[Transport] = None, *, version: str = "live-fake",
    salt: Optional[str] = None,
) -> Scenario:
    salt = salt or _chain_salt(n)
    transport = transport or fake_chain_transport(n)
    return Scenario(
        name=f"live-chain-{n}",
        n_steps=n,
        task_factory=lambda: ChainTask(n, salt),
        model_factory=lambda: LiveModelProvider(transport),
        model_version=version,
    )


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
