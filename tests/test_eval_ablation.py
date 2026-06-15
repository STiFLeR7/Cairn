"""AP-0031 / C5 — ablating the cairn locates the fidelity cliff."""

from benchmarks.scenarios import multi_file_scenario
from cairn.eval.ablation import ablate, run_ablation
from cairn.state import ContinuationState, Decision, PlanStep


def test_ablate_drops_named_component():
    s = ContinuationState()
    s.durable_core.plan = [PlanStep(id="s0", description="x", status="done")]
    s.durable_core.decisions = [Decision(id="d0", decision="x", ruled_out=True),
                                Decision(id="d1", decision="y", ruled_out=False)]
    s.durable_core.world.digest = {"a": "h"}

    assert ablate(s, "plan").durable_core.plan == []
    assert ablate(s, "world_digest").durable_core.world.digest == {}
    assert all(not d.ruled_out for d in ablate(s, "ruled_out").durable_core.decisions)
    # ablation is non-destructive to the original
    assert s.durable_core.plan != []


def test_c5_plan_is_necessary_digest_is_slack(tmp_path):
    scenario = multi_file_scenario(n=4)
    counter = {"i": 0}

    def base_factory():
        counter["i"] += 1
        return str(tmp_path / f"b{counter['i']}")

    full = run_ablation(scenario, k=2, drop=None, base_factory=base_factory)
    no_plan = run_ablation(scenario, k=2, drop="plan", base_factory=base_factory)
    no_digest = run_ablation(scenario, k=2, drop="world_digest", base_factory=base_factory)

    # Dropping the plan removes the agent's record of completed work → it redoes everything
    # (a fidelity cliff: recovery tax up, no-regression collapses).
    assert no_plan.recovery_tax > full.recovery_tax
    assert no_plan.no_regression < full.no_regression
    # Dropping the world digest is slack here — recovery is unaffected.
    assert no_digest.recovery_tax == full.recovery_tax
    assert no_digest.no_regression == full.no_regression
