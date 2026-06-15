"""AP-0025 — reconcile: torn-write detection, plan drift, danger-window surfacing."""

from cairn.harness.observe import ObservedWorld
from cairn.harness.reconcile import reconcile
from cairn.state import ContinuationState, PlanStep


def _state(digest, plan=None):
    s = ContinuationState()
    s.durable_core.world.digest = digest
    if plan:
        s.durable_core.plan = plan
    return s


def test_clean_when_world_matches_cairn():
    rp = reconcile(_state({"a.txt": "h1"}), ObservedWorld(digest={"a.txt": "h1"}))
    assert rp.clean
    assert rp.torn_files == [] and rp.lost_files == []


def test_detects_torn_and_lost_files():
    s = _state({"a.txt": "h1", "b.txt": "h2"})
    rp = reconcile(s, ObservedWorld(digest={"a.txt": "DIFFERENT"}))
    assert rp.torn_files == ["a.txt"]  # content diverged
    assert rp.lost_files == ["b.txt"]  # absent from the restored world
    assert not rp.clean


def test_plan_step_reopened_when_its_evidence_diverged():
    plan = [PlanStep(id="s0", description="write a.txt", status="done")]
    rp = reconcile(_state({"a.txt": "h1"}, plan), ObservedWorld(digest={"a.txt": "CHANGED"}))
    assert rp.plan[0].status == "pending"  # 'a.txt' in description → re-opened for redo


def test_surfaces_effect_danger_window():
    obs = ObservedWorld(
        digest={},
        effects_since=[
            {"type": "INTENT", "idempotency_key": "k", "tool_class": "check-before-retry", "seq": 0}
        ],
    )
    rp = reconcile(_state({}), obs)
    assert len(rp.danger_window) == 1
    assert rp.danger_window[0]["idempotency_key"] == "k"
