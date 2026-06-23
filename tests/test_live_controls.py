"""Tests for the live-run controls (AP-0039): transcript, replay, budget.

All offline: transports are plain functions; files use pytest's tmp_path.
"""

from __future__ import annotations

import pytest

from cairn.live_controls import (
    Budget,
    BudgetExceeded,
    ReplayMiss,
    budgeted,
    is_transient,
    load_transcript,
    prompt_key,
    record_to,
    replay_from_transcript,
    replay_transport,
    retrying,
)


def test_prompt_key_is_stable_and_content_addressed():
    assert prompt_key("abc") == prompt_key("abc")
    assert prompt_key("abc") != prompt_key("abd")


def test_record_to_writes_jsonl_roundtrip(tmp_path):
    path = tmp_path / "t" / "transcript.jsonl"  # nested dir is created
    transport = record_to(lambda p: f"reply::{p}", str(path), model_version="m-1")
    transport("p0")
    transport("p1")

    records = load_transcript(str(path))
    assert [r["index"] for r in records] == [0, 1]
    assert records[0]["prompt"] == "p0"
    assert records[0]["reply"] == "reply::p0"
    assert records[0]["model_version"] == "m-1"
    assert records[0]["prompt_key"] == prompt_key("p0")


def test_record_truncates_unless_append(tmp_path):
    path = str(tmp_path / "t.jsonl")
    record_to(lambda p: "a", path)("x")
    record_to(lambda p: "b", path)("y")  # append=False default → fresh file
    records = load_transcript(path)
    assert len(records) == 1 and records[0]["reply"] == "b"

    record_to(lambda p: "c", path, append=True)("z")
    assert len(load_transcript(path)) == 2


def test_replay_serves_recorded_replies_without_calling_underlying():
    records = [
        {"prompt_key": prompt_key("p0"), "reply": "r0"},
        {"prompt_key": prompt_key("p1"), "reply": "r1"},
    ]

    def must_not_run(prompt):  # fallback proves replay didn't fall through
        raise AssertionError("underlying transport was called during replay")

    replay = replay_transport(records, fallback=must_not_run)
    assert replay("p0") == "r0"
    assert replay("p1") == "r1"


def test_replay_miss_raises_without_fallback():
    replay = replay_transport([])
    with pytest.raises(ReplayMiss):
        replay("unseen")


def test_replay_miss_uses_fallback_when_given():
    replay = replay_transport([], fallback=lambda p: "live::" + p)
    assert replay("unseen") == "live::unseen"


def test_record_then_replay_is_deterministic_and_offline(tmp_path):
    path = str(tmp_path / "run.jsonl")
    calls = {"n": 0}

    def live(prompt):
        calls["n"] += 1
        return f"v{calls['n']}"

    recording = record_to(live, path)
    first = [recording("a"), recording("b")]
    assert calls["n"] == 2

    replay = replay_from_transcript(path)  # no fallback → must be fully covered
    assert [replay("a"), replay("b")] == first
    assert calls["n"] == 2  # underlying live transport never called again


def test_replay_preserves_order_for_a_repeated_prompt():
    records = [
        {"prompt_key": prompt_key("same"), "reply": "first"},
        {"prompt_key": prompt_key("same"), "reply": "second"},
    ]
    replay = replay_transport(records)
    assert [replay("same"), replay("same")] == ["first", "second"]


def test_budget_stops_after_max_calls():
    budget = Budget(max_calls=2)
    transport = budget.wrap(lambda p: "ok")
    assert transport("1") == "ok"
    assert transport("2") == "ok"
    with pytest.raises(BudgetExceeded):
        transport("3")
    assert budget.calls == 2


def test_budget_tracks_chars_and_stops():
    budget = Budget(max_chars=10)
    transport = budget.wrap(lambda p: p)  # reply echoes prompt
    transport("abcd")  # 4 + 4 = 8 chars
    with pytest.raises(BudgetExceeded):  # already at 8, ceiling 10 → next call blocked once exhausted
        for _ in range(5):
            transport("abcd")
    assert budget.chars >= 10


def test_budgeted_convenience_wrapper():
    transport = budgeted(lambda p: "x", max_calls=1)
    assert transport("a") == "x"
    with pytest.raises(BudgetExceeded):
        transport("b")


def test_controls_compose():
    # budget(record(replay)) — the canonical offline stack
    import tempfile, os

    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    try:
        records = [{"prompt_key": prompt_key("a"), "reply": "ra"}]
        stack = budgeted(record_to(replay_transport(records), path, model_version="replay"),
                         max_calls=5)
        assert stack("a") == "ra"
        assert load_transcript(path)[0]["reply"] == "ra"
    finally:
        os.remove(path)


# --- transient-failure retry (AP-0046) -------------------------------------------


def test_retrying_recovers_after_transient_failures():
    slept: list = []
    calls = {"i": 0}

    def flaky(prompt: str) -> str:
        calls["i"] += 1
        if calls["i"] < 3:
            raise RuntimeError("chat API error: {'message': 'Provider returned error', 'code': 400}")
        return "ok"

    transport = retrying(flaky, base_delay=0.1, sleep=slept.append)
    assert transport("p") == "ok"
    assert calls["i"] == 3            # failed twice, succeeded on the third
    assert len(slept) == 2           # one backoff per retry
    assert slept[1] > slept[0]       # exponential


def test_retrying_fails_fast_on_permanent_error():
    slept: list = []

    def auth_error(prompt: str) -> str:
        raise RuntimeError("HTTP Error 401: Unauthorized")

    transport = retrying(auth_error, sleep=slept.append)
    with pytest.raises(RuntimeError, match="401"):
        transport("p")
    assert slept == []               # not a transient error → no retries


def test_retrying_gives_up_after_max_retries():
    def always_429(prompt: str) -> str:
        raise RuntimeError("HTTP Error 429: Too Many Requests")

    transport = retrying(always_429, max_retries=2, sleep=lambda d: None)
    with pytest.raises(RuntimeError, match="429"):
        transport("p")


def test_is_transient_classification():
    assert is_transient(RuntimeError("HTTP Error 429: Too Many Requests"))
    assert is_transient(RuntimeError("Provider returned error code 400"))
    assert is_transient(RuntimeError("HTTP Error 503"))
    assert not is_transient(RuntimeError("HTTP Error 404: Not Found"))
    assert not is_transient(RuntimeError("HTTP Error 401: Unauthorized"))
