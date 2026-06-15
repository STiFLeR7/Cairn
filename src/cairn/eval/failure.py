"""Failure-type taxonomy for the benchmark (AP-0028).

v1 realizes `CRASH` faithfully (process death at a step boundary, via the harness
`step_hook`/`crash_after` seam). The other types are *modeled* as a typed stop-at-`k`
in v1 — the recovery situation they create (durable state up to `k`, nothing after) is
what matters for measuring recovery, and the honest scope of this modeling is recorded
in ADR-0009.
"""

from __future__ import annotations

from enum import Enum


class FailureType(str, Enum):
    CRASH = "crash"
    CONTEXT_OVERFLOW = "context-overflow"
    TOOL_TIMEOUT = "tool-timeout"
    MODEL_ERROR = "model-error"


#: Faithfully realized in v1; the rest are modeled as stop-at-k (see ADR-0009).
FAITHFULLY_REALIZED = frozenset({FailureType.CRASH})


def is_faithful(ftype: FailureType) -> bool:
    return ftype in FAITHFULLY_REALIZED
