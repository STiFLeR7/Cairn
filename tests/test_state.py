from cairn.state import ContinuationState, Decision, Intent, PlanStep


def test_continuation_state_roundtrips():
    s = ContinuationState()
    s.durable_core.intent = Intent("root goal", "active subgoal")
    s.durable_core.plan = [PlanStep("s1", "do a thing", "done", ["s0"])]
    s.durable_core.decisions = [Decision("d1", "x is true", "because", ruled_out=True)]
    s.durable_core.world.snapshot_id = "snap_3"
    s.durable_core.effects_ref.offset = 7

    d = s.to_dict()
    s2 = ContinuationState.from_dict(d)

    assert s2.durable_core.intent.root_goal == "root goal"
    assert s2.durable_core.plan[0].status == "done"
    assert s2.durable_core.decisions[0].ruled_out is True
    assert s2.durable_core.world.snapshot_id == "snap_3"
    assert s2.durable_core.effects_ref.offset == 7
    assert s2.to_dict() == d  # full round-trip


def test_json_roundtrip():
    s = ContinuationState()
    s.durable_core.intent = Intent("g", "sg")
    assert ContinuationState.from_json(s.to_json()).to_dict() == s.to_dict()
