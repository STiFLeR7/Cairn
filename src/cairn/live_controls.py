"""Determinism, cost & reproducibility controls for live-LLM runs (AP-0039).

A live model is non-deterministic and metered. These wrappers turn any ``Transport``
(``prompt -> reply text``; see :mod:`cairn.model_live`) into one that is:

  * **auditable** — every prompt/reply is appended to a JSONL transcript (:func:`record_to`),
  * **re-runnable** — a recorded run replays from its transcript with no network
    (:func:`replay_transport` / :func:`replay_from_transcript`), and
  * **bounded** — a :class:`Budget` stops a run before it exceeds a call/char ceiling.

They compose, outermost-first::

    guarded = budget.wrap(record_to(replay_from_transcript(path, fallback=live), out))

Nothing here performs network I/O itself; the wrapped transport does (or, in replay,
does not). Determinism on the *live* path comes from the transport's ``temperature``
(default ``0.0`` in :func:`cairn.model_live.anthropic_transport`); determinism on the
*replay* path comes from the recorded transcript, independent of the model.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections import defaultdict, deque
from typing import Callable, Optional, Sequence

from .model_live import Transport


def prompt_key(prompt: str) -> str:
    """Stable content key for a prompt (sha256 hex) — the replay cache key."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


# --- transcript recording --------------------------------------------------------


def record_to(
    transport: Transport,
    path: str,
    *,
    model_version: str = "",
    append: bool = False,
) -> Transport:
    """Wrap ``transport`` so every call appends a JSONL record to ``path``.

    Each line is ``{index, model_version, prompt_key, prompt, reply}``. With
    ``append=False`` the file is truncated once at wrap time, so a fresh run starts a
    fresh transcript. The reply is passed through unchanged.
    """
    path = os.fspath(path)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    if not append:
        open(path, "w", encoding="utf-8").close()
    counter = {"i": 0}

    def recording(prompt: str) -> str:
        reply = transport(prompt)
        record = {
            "index": counter["i"],
            "model_version": model_version,
            "prompt_key": prompt_key(prompt),
            "prompt": prompt,
            "reply": reply,
        }
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        counter["i"] += 1
        return reply

    return recording


def load_transcript(path: str) -> list[dict]:
    """Read a JSONL transcript written by :func:`record_to`."""
    records: list[dict] = []
    with open(os.fspath(path), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# --- replay (offline re-run) -----------------------------------------------------


class ReplayMiss(KeyError):
    """Raised when a prompt has no recorded reply and no fallback is configured."""


def replay_transport(
    records: Sequence[dict],
    *,
    fallback: Optional[Transport] = None,
) -> Transport:
    """Build a ``Transport`` that returns recorded replies, no network.

    Replies are keyed by ``prompt_key`` and served FIFO per key (so a prompt that
    recurs across repetitions replays in recorded order). On a miss it calls
    ``fallback`` if given, else raises :class:`ReplayMiss`.
    """
    queues: dict[str, deque] = defaultdict(deque)
    for record in records:
        queues[record["prompt_key"]].append(record["reply"])

    def replay(prompt: str) -> str:
        key = prompt_key(prompt)
        queue = queues.get(key)
        if queue:
            return queue.popleft()
        if fallback is not None:
            return fallback(prompt)
        raise ReplayMiss(f"no recorded reply for prompt key {key[:12]}…")

    return replay


def replay_from_transcript(path: str, *, fallback: Optional[Transport] = None) -> Transport:
    """Convenience: :func:`replay_transport` over a transcript file."""
    return replay_transport(load_transcript(path), fallback=fallback)


# --- cost / budget guard ---------------------------------------------------------


class BudgetExceeded(RuntimeError):
    """Raised when a run hits its configured call or character ceiling."""


class Budget:
    """A cost guard over a transport.

    Tracks the number of calls and the cumulative characters of prompts + replies.
    A run is stopped (``BudgetExceeded``) *before* a call that would start beyond an
    exhausted ceiling — so a study cannot run away on cost. ``max_chars`` is a coarse,
    tokenizer-free proxy for spend; document the conversion when reporting a study.
    """

    def __init__(self, *, max_calls: Optional[int] = None, max_chars: Optional[int] = None) -> None:
        self.max_calls = max_calls
        self.max_chars = max_chars
        self.calls = 0
        self.chars = 0

    def wrap(self, transport: Transport) -> Transport:
        def guarded(prompt: str) -> str:
            if self.max_calls is not None and self.calls >= self.max_calls:
                raise BudgetExceeded(f"call budget exhausted ({self.max_calls} calls)")
            if self.max_chars is not None and self.chars >= self.max_chars:
                raise BudgetExceeded(f"char budget exhausted ({self.max_chars} chars)")
            reply = transport(prompt)
            self.calls += 1
            self.chars += len(prompt) + len(reply)
            return reply

        return guarded


def budgeted(
    transport: Transport,
    *,
    max_calls: Optional[int] = None,
    max_chars: Optional[int] = None,
) -> Transport:
    """Convenience wrapper returning a budget-guarded transport (state discarded)."""
    return Budget(max_calls=max_calls, max_chars=max_chars).wrap(transport)


# --- transient-failure retry -----------------------------------------------------

_TRANSIENT_MARKERS = (
    "429", "500", "502", "503", "504",
    "provider returned error", "timed out", "timeout",
    "temporarily", "overloaded", "rate limit", "rate-limit",
)


def is_transient(exc: Exception) -> bool:
    """Heuristic: does this look like a *retryable* live-API failure?

    Matches rate limits (429), 5xx, a stealth/free model's intermittent "Provider returned
    error", and timeouts. Permanent errors — 401/403 auth, 404 unknown model, a malformed
    request — are deliberately NOT matched, so they fail fast instead of burning retries.
    """
    s = str(exc).lower()
    return any(m in s for m in _TRANSIENT_MARKERS)


def retrying(
    transport: Transport,
    *,
    max_retries: int = 4,
    base_delay: float = 1.0,
    max_delay: float = 20.0,
    sleep: Callable[[float], None] = time.sleep,
    transient: Callable[[Exception], bool] = is_transient,
) -> Transport:
    """Wrap a transport to retry *transient* failures with exponential backoff.

    A live study makes many calls; a free/stealth model intermittently returns 429s or
    "Provider returned error" 400s (owl-alpha did, mid-study). Without this, one hiccup aborts
    the whole run. Only transient-looking errors are retried (see :func:`is_transient`);
    permanent ones re-raise immediately. After ``max_retries`` transient failures the last
    error propagates. ``sleep`` is injected for testing. Wrap this *innermost* (closest to the
    real transport) so a recorded transcript captures only the successful reply per call.
    """

    def wrapped(prompt: str) -> str:
        attempt = 0
        while True:
            try:
                return transport(prompt)
            except Exception as exc:  # noqa: BLE001 — re-raised unless transient with budget left
                if attempt >= max_retries or not transient(exc):
                    raise
                sleep(min(max_delay, base_delay * (2 ** attempt)))
                attempt += 1

    return wrapped
