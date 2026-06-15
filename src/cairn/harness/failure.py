"""Failure injection — a generic lifecycle hook, not a baked-in crash flag (ADR-0008).

The agent loop exposes an optional ``step_hook(step)`` callback. Tests and demos wire it to
raise ``InjectedFailure`` after a chosen step to simulate a crash; production code can use the
same seam for telemetry. Nothing failure-specific lives in the harness itself.
"""

from __future__ import annotations

from typing import Callable, Optional


class InjectedFailure(RuntimeError):
    """A deliberate, test/demo-induced crash at a step boundary."""


def crash_after(k: int, *, do: Optional[Callable[[int], None]] = None) -> Callable[[int], None]:
    """Return a ``step_hook`` that runs ``do(step)`` (if given) then raises after step ``k``.

    ``do`` lets a test perform an in-flight side effect (e.g. an effect whose COMPLETE never
    lands) at the moment of the crash, producing a realistic effect danger window.
    """

    def hook(step: int) -> None:
        if step == k:
            if do is not None:
                do(step)
            raise InjectedFailure(f"injected failure after step {k}")

    return hook
