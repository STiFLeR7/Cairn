"""Effect-safety: write-ahead effects + resume-time danger-window resolution.

Implements the effect-safety protocol (ADR-0006) and the mechanism behind claim C3:
a resumed agent must not re-execute an irreversible effect. Effects are wrapped
INTENT -> run -> COMPLETE (invariant I1). On resume, every ``INTENT``-without-``COMPLETE``
key is the *danger window* and is resolved by the policy for its tool class.

Effects are injected callables in v1 (no real network/email client is assumed), keeping
recovery deterministic and testable while honoring the no-hardcoded-harness rule (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

# Tool classes (from the tool-effect taxonomy, AP-0012 / AP-0018).
SAFE_TO_RETRY = "safe-to-retry"
CHECK_BEFORE_RETRY = "check-before-retry"
NEVER_RETRY = "never-retry"


@dataclass
class EffectfulTool:
    """An injected irreversible effect.

    ``run`` performs the side effect; ``verify`` (for ``check-before-retry``) returns
    True iff the effect has *already* happened, so resume can skip instead of duplicate.
    """

    name: str
    tool_class: str
    run: Optional[Callable[[], Any]] = None
    verify: Optional[Callable[[], bool]] = None


@dataclass
class Resolution:
    key: str
    tool_class: str
    action: str  # "redo" | "skip" | "escalate"
    detail: str = ""


class EscalationRequired(Exception):
    """Raised when a ``never-retry`` effect is found in the danger window."""

    def __init__(self, resolution: "Resolution") -> None:
        super().__init__(
            f"never-retry effect {resolution.key!r} in danger window — human decision required"
        )
        self.resolution = resolution


def perform_effect(
    runtime,
    tool: EffectfulTool,
    key: str,
    *,
    intent: Optional[str] = None,
    step: int = 0,
) -> Any:
    """Write-ahead an effect: INTENT durable first (I1), run, then COMPLETE on success."""
    runtime.append_effect(intent or tool.name, key, tool.tool_class, step)
    result = tool.run() if tool.run else None
    runtime.complete_effect(key)
    return result


def danger_window(records: list[dict]) -> list[dict]:
    """The INTENT records with no matching COMPLETE, in ledger order (the danger window)."""
    open_intents: dict[str, dict] = {}
    order: list[str] = []
    for rec in records:
        key = rec.get("idempotency_key", "")
        if rec.get("type") == "INTENT":
            if key not in open_intents:
                order.append(key)
            open_intents[key] = rec
        elif rec.get("type") == "COMPLETE":
            open_intents.pop(key, None)
    return [open_intents[k] for k in order if k in open_intents]


def resolve_danger_window(
    records: list[dict],
    tools: Mapping[str, EffectfulTool],
    runtime,
    *,
    escalate: bool = True,
) -> list[Resolution]:
    """Resolve every danger-window key by the policy for its tool class.

    ``safe-to-retry`` redoes; ``check-before-retry`` verifies then redoes-or-skips (no
    duplicate — claim C3); ``never-retry`` escalates (raises ``EscalationRequired`` when
    ``escalate`` is True, else returns an ``escalate`` Resolution and is **not** retried).
    A COMPLETE is written after resolution so the key leaves the danger window.
    """
    resolutions: list[Resolution] = []
    for rec in danger_window(records):
        key = rec.get("idempotency_key", "")
        tool = tools.get(key)
        cls = rec.get("tool_class") or (tool.tool_class if tool else NEVER_RETRY)

        if cls == SAFE_TO_RETRY:
            if tool and tool.run:
                tool.run()
            runtime.complete_effect(key)
            resolutions.append(Resolution(key, cls, "redo", "idempotent — re-executed"))

        elif cls == CHECK_BEFORE_RETRY:
            already = bool(tool.verify()) if (tool and tool.verify) else False
            if already:
                runtime.complete_effect(key)
                resolutions.append(
                    Resolution(key, cls, "skip", "verify: already done — not re-executed")
                )
            else:
                if tool and tool.run:
                    tool.run()
                runtime.complete_effect(key)
                resolutions.append(
                    Resolution(key, cls, "redo", "verify: not done — re-executed")
                )

        else:  # NEVER_RETRY (and any unknown class — conservative default)
            res = Resolution(key, NEVER_RETRY, "escalate", "non-idempotent, unqueryable")
            if escalate:
                raise EscalationRequired(res)
            resolutions.append(res)

    return resolutions
