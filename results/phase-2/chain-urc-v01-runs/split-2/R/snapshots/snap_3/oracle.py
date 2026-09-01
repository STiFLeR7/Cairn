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

_SALT = 'chain-6-neutral'
_STATE = 'chain_state.json'
_advanced = False


def _digest(label):
    return hashlib.sha256(f"{_SALT}:{label}".encode()).hexdigest()[:12]


def _load():
    if os.path.exists(_STATE):
        with open(_STATE, encoding="utf-8") as f:
            return json.load(f)
    return {"pos": 0, "tokens": [_digest("seed")]}


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
