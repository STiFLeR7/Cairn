"""Sequential-chain oracle — a primitive for *non-batchable* recovery tasks (AP-0043).

Motivation (Milestone M1 NO-GO): the multi-file benchmark task was *batchable* — a capable
model created every file in a single action and finished before the injected crash, so no
failure ever fired and recovery could not be measured. This primitive removes that escape
hatch.

A chain advances one token at a time. `advance(token)` checks the caller holds the *current*
token, computes the secret successor, commits it to durable state, and returns it — but **at
most once per process**. Because the harness runs each agent step in a fresh subprocess
(`python -c ...`), the per-process guard means extending a length-`n` chain requires `n`
separate steps. A single batched action therefore *cannot* complete the task, and a crash at
step `k` leaves a genuine partial chain (`pos == k`) that recovery must re-ground from.

The successor is a salted digest, so durable progress cannot be fabricated without performing
the steps (or recomputing the digest, which needs the salt). **Threat model:** a *cooperative*
capable model following the stated protocol — not an adversary who reverse-engineers the
oracle source to forge state. This is the right model for a recovery benchmark: we measure
whether re-grounding beats cold-restart when the task is done the intended way, one step at a
time.

Nothing here is wired into the harness; it is an injected building block (ADR-0007). The
concrete task that uses it lives in `benchmarks/scenarios.py`.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field

DEFAULT_STATE = "chain_state.json"


def _digest(salt: str, label: str) -> str:
    return hashlib.sha256(f"{salt}:{label}".encode()).hexdigest()[:12]


def seed_token(salt: str) -> str:
    """The chain's starting token (position 0)."""
    return _digest(salt, "seed")


def next_token(salt: str, token: str) -> str:
    """The secret successor of `token` — knowable only by applying the salted transform."""
    return _digest(salt, token)


def expected_tokens(salt: str, n: int) -> list[str]:
    """The full sequence a correct length-`n` run must produce: seed + `n` successors."""
    toks = [seed_token(salt)]
    for _ in range(n):
        toks.append(next_token(salt, toks[-1]))
    return toks


class ChainViolation(RuntimeError):
    """A single process tried to advance more than once, or from a non-current token.

    The first is the *batching block* — the reason a one-shot action cannot finish the task.
    The second guards against skipping ahead.
    """


@dataclass
class Chain:
    """A durable hash-chain advanced one step per process.

    `salt` is the per-task secret transform; `state_path` is the durable progress file
    (relative to the process cwd, i.e. the workspace, by default). A new `Chain` is created
    per import — and modules are imported once per process — so `_advanced` resets each step.
    """

    salt: str
    state_path: str = DEFAULT_STATE
    _advanced: bool = field(default=False, init=False, repr=False)

    def _load(self) -> dict:
        if os.path.exists(self.state_path):
            with open(self.state_path, encoding="utf-8") as f:
                return json.load(f)
        return {"pos": 0, "tokens": [seed_token(self.salt)]}

    def current(self) -> str:
        """The latest committed token (the seed if no step has run yet)."""
        return self._load()["tokens"][-1]

    def pos(self) -> int:
        """How many steps have been committed so far (0..n)."""
        return self._load()["pos"]

    def advance(self, token: str) -> str:
        """Commit and return the next token. Raises `ChainViolation` on a 2nd call this
        process (the batching block) or if `token` is not the current token."""
        if self._advanced:
            raise ChainViolation("chain: only one advance per step — start a new step")
        st = self._load()
        if token != st["tokens"][-1]:
            raise ChainViolation("chain: advance from the current token (use current())")
        self._advanced = True
        nxt = next_token(self.salt, token)
        st["tokens"].append(nxt)
        st["pos"] += 1
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(st, f)
        os.replace(tmp, self.state_path)  # atomic commit
        return nxt

    def is_complete(self, n: int) -> bool:
        """True iff `n` steps are committed and every token matches the salted transform.

        The token check means durable state cannot be faked by writing `pos = n` with
        arbitrary tokens — the successors must actually be the oracle's (which needs the salt).
        """
        st = self._load()
        return st["pos"] >= n and st["tokens"] == expected_tokens(self.salt, n)


_ORACLE_TEMPLATE = '''\
"""Auto-generated chain oracle (AP-0043) - do not edit. ASCII + stdlib only.

Black-box stateful tool for a non-batchable sequential task. Each step: read the current
token with current() and pass it to advance(token) to commit and obtain the next token.
advance() succeeds at most once per process (the module-level _advanced guard, reset on each
fresh `python -c` step), so the chain extends one step per action - a single batched action
cannot finish it. The transform is inlined (the harness subprocess has no `cairn` on its
path) and mirrors cairn.eval.chain exactly; a correct end-to-end run is the agreement check.
"""
import hashlib
import json
import os

_SALT = {salt!r}
_STATE = {state_path!r}
_advanced = False


def _digest(label):
    return hashlib.sha256(f"{{_SALT}}:{{label}}".encode()).hexdigest()[:12]


def _load():
    if os.path.exists(_STATE):
        with open(_STATE, encoding="utf-8") as f:
            return json.load(f)
    return {{"pos": 0, "tokens": [_digest("seed")]}}


def current():
    return _load()["tokens"][-1]


def pos():
    return _load()["pos"]


def advance(token):
    global _advanced
    if _advanced:
        raise RuntimeError("chain: only one advance per step - start a new step")
    st = _load()
    if token != st["tokens"][-1]:
        raise RuntimeError("chain: advance from the current token (use current())")
    _advanced = True
    nxt = _digest(token)
    st["tokens"].append(nxt)
    st["pos"] += 1
    tmp = _STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f)
    os.replace(tmp, _STATE)
    return nxt
'''


def render_oracle_module(salt: str, state_path: str = DEFAULT_STATE) -> str:
    """Source for the `oracle` module planted into a task workspace, bound to `salt`.

    The salt lives here (the planted module), never in the goal text — so a cooperative model
    uses `advance` as a black box and cannot precompute the chain. The module is stdlib-only so
    it imports cleanly in the harness subprocess; it mirrors :class:`Chain` exactly.
    """
    return _ORACLE_TEMPLATE.format(salt=salt, state_path=state_path)
