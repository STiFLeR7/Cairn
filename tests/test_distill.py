"""AP-0023 — unified distillation engine (claim C2: identical core, tail differs)."""

from cairn.harness.distill import CHECKPOINT, COMPACT, distill
from cairn.model import CODE, Action, StepRecord


def _hist():
    return [
        StepRecord(step=0, action=Action(CODE, code="write a.txt"), returncode=0, stdout="ok"),
        StepRecord(step=1, action=Action(CODE, code="boom"), returncode=1, stderr="err"),
    ]


def test_durable_core_identical_across_modes():
    h = _hist()
    c = distill("goal", h, mode=COMPACT, step=1)
    k = distill("goal", h, mode=CHECKPOINT, step=1)
    assert c.durable_core == k.durable_core  # C2: same sufficient statistic
    assert c.elastic_tail != k.elastic_tail  # only the tail differs


def test_tail_pruned_vs_frozen():
    h = [
        StepRecord(step=i, action=Action(CODE, code=f"s{i}"), returncode=0, stdout=str(i))
        for i in range(6)
    ]
    c = distill("g", h, mode=COMPACT, step=5)
    k = distill("g", h, mode=CHECKPOINT, step=5)
    assert len(c.elastic_tail.recent_steps) <= 1  # pruned (live agent re-derives)
    assert len(k.elastic_tail.recent_steps) == 5  # frozen last N verbatim
    assert c.elastic_tail.scratch is not None
    assert k.elastic_tail.scratch is None


def test_failed_step_becomes_ruled_out_and_blocked():
    k = distill("g", _hist(), mode=CHECKPOINT, step=1)
    decisions = {d.id: d for d in k.durable_core.decisions}
    assert decisions["d1"].ruled_out is True
    assert decisions["d0"].ruled_out is False
    plan = {p.id: p for p in k.durable_core.plan}
    assert plan["s0"].status == "done"
    assert plan["s1"].status == "blocked"


def test_world_digest_populated_and_stable(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "f.txt").write_text("hello", encoding="utf-8")
    k1 = distill("g", [], mode=CHECKPOINT, step=0, workspace_dir=str(ws))
    k2 = distill("g", [], mode=CHECKPOINT, step=0, workspace_dir=str(ws))
    assert "f.txt" in k1.durable_core.world.digest
    assert k1.durable_core.world.digest == k2.durable_core.world.digest  # stable


def test_unknown_mode_raises():
    try:
        distill("g", [], mode="nonsense", step=0)
        assert False, "expected ValueError"
    except ValueError:
        pass
