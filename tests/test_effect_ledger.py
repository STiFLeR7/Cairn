from cairn.runtime.effect_ledger import COMPLETE, INTENT, EffectLedger


def test_append_only_and_monotonic_offsets(tmp_path):
    led = EffectLedger(str(tmp_path / "effects.jsonl"))
    assert led.current_offset() == 0

    o0 = led.append_effect("send_email#1", "k1", "check-before-retry", step=1)
    o1 = led.append_effect("post#2", "k2", "never-retry", step=2)
    assert (o0, o1) == (0, 1)
    assert led.current_offset() == 2

    led.complete_effect("k1")
    assert led.current_offset() == 3

    recs = led.list_effects_since(0)
    assert [r["seq"] for r in recs] == [0, 1, 2]
    assert recs[0]["type"] == INTENT
    assert recs[0]["idempotency_key"] == "k1"
    assert recs[2]["type"] == COMPLETE


def test_list_since_offset(tmp_path):
    led = EffectLedger(str(tmp_path / "e.jsonl"))
    for i in range(5):
        led.append_effect(f"a{i}", f"k{i}")
    assert [r["seq"] for r in led.list_effects_since(3)] == [3, 4]
