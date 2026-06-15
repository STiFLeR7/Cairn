"""AP-0026 — effect-safety: write-ahead + danger-window resolution (claim C3)."""

from cairn.harness.effects import (
    CHECK_BEFORE_RETRY,
    NEVER_RETRY,
    SAFE_TO_RETRY,
    EffectfulTool,
    EscalationRequired,
    danger_window,
    perform_effect,
    resolve_danger_window,
)


class FakeRuntime:
    def __init__(self):
        self.appended = []
        self.completed = []

    def append_effect(self, intent, key, tool_class="never-retry", step=0):
        self.appended.append((intent, key, tool_class, step))
        return len(self.appended) - 1

    def complete_effect(self, key):
        self.completed.append(key)


def _recs(*triples):
    return [
        {"type": t, "idempotency_key": k, "tool_class": c, "seq": i}
        for i, (t, k, c) in enumerate(triples)
    ]


def test_danger_window_is_open_intents_only():
    recs = _recs(
        ("INTENT", "k1", CHECK_BEFORE_RETRY),
        ("COMPLETE", "k1", ""),
        ("INTENT", "k2", NEVER_RETRY),
    )
    assert [r["idempotency_key"] for r in danger_window(recs)] == ["k2"]


def test_perform_effect_writes_intent_then_complete():
    rt = FakeRuntime()
    ran = []
    tool = EffectfulTool("send", CHECK_BEFORE_RETRY, run=lambda: ran.append("x"))
    perform_effect(rt, tool, "k", step=3)
    assert rt.appended == [("send", "k", CHECK_BEFORE_RETRY, 3)]  # INTENT first (I1)
    assert ran == ["x"]
    assert rt.completed == ["k"]  # COMPLETE after success


def test_check_before_retry_skips_when_already_done():
    rt = FakeRuntime()
    ran = []
    tool = EffectfulTool("send", CHECK_BEFORE_RETRY, run=lambda: ran.append(1), verify=lambda: True)
    res = resolve_danger_window(_recs(("INTENT", "k", CHECK_BEFORE_RETRY)), {"k": tool}, rt)
    assert res[0].action == "skip"
    assert ran == []  # NOT re-executed → no duplicate effect (C3)
    assert rt.completed == ["k"]  # leaves the danger window


def test_check_before_retry_redoes_when_not_done():
    rt = FakeRuntime()
    ran = []
    tool = EffectfulTool("send", CHECK_BEFORE_RETRY, run=lambda: ran.append(1), verify=lambda: False)
    res = resolve_danger_window(_recs(("INTENT", "k", CHECK_BEFORE_RETRY)), {"k": tool}, rt)
    assert res[0].action == "redo"
    assert ran == [1] and rt.completed == ["k"]


def test_safe_to_retry_redoes():
    rt = FakeRuntime()
    ran = []
    tool = EffectfulTool("calc", SAFE_TO_RETRY, run=lambda: ran.append(1))
    res = resolve_danger_window(_recs(("INTENT", "k", SAFE_TO_RETRY)), {"k": tool}, rt)
    assert res[0].action == "redo" and ran == [1]


def test_never_retry_escalates_and_is_not_retried():
    rt = FakeRuntime()
    try:
        resolve_danger_window(_recs(("INTENT", "k", NEVER_RETRY)), {}, rt)
        assert False, "expected EscalationRequired"
    except EscalationRequired as e:
        assert e.resolution.action == "escalate"
    assert rt.completed == []  # never auto-completed or retried


def test_never_retry_can_return_resolution_when_escalation_disabled():
    rt = FakeRuntime()
    res = resolve_danger_window(_recs(("INTENT", "k", NEVER_RETRY)), {}, rt, escalate=False)
    assert res[0].action == "escalate"
