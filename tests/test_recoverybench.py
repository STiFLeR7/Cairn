import pytest
import json
from copy import deepcopy

import cairn.eval.recoverybench as recoverybench

from cairn.eval.recoverybench import (
    LivePilotEvidence,
    LiveRunConfig,
    LiveRunFailure,
    deterministic_summary,
    live_pilot_evidence,
    load_fixture,
    normalize_record,
    normalized_records_equal,
    phase_1_verdict,
    run_deterministic_matrix,
    run_control_step,
    run_live_step,
    run_paired_control,
    run_live_matrix,
    write_records,
)
from cairn.model_live import LiveModelProvider
from cairn.runtime.checkpoint_store import CheckpointStore
from cairn.runtime.effect_ledger import EffectLedger
from cairn.worlds import TerminalWorld
from cairn.eval.phase2 import diagnose_phase_one_records
from cairn.eval.phase2 import freeze_phase_one_controls
from cairn.eval.phase2 import compacted_continuation
from cairn.eval.phase2 import ablated_continuation
from cairn.eval.phase2 import run_live_urc
from cairn.eval.phase2 import capture_live_urc
from cairn.eval.phase2 import summarize_urc_records
from cairn.eval.phase2 import matrix_cells
from cairn.model import Action, StepRecord, CODE
from cairn.harness.distill import CHECKPOINT, distill
from cairn.state import VerificationItem
from benchmarks.phase2 import write_control_freeze


def test_repository_fixture_advances_one_verified_work_unit(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)

    assert fixture.progress(root) == 0

    fixture.apply_control_action(root, 0)

    assert fixture.progress(root) == 1
    assert not fixture.verify(root).passed


def test_phase_two_holdout_fixture_has_four_independent_verified_units(tmp_path):
    fixture = load_fixture("phase2_holdout")
    root = fixture.copy_to(tmp_path)

    for step in range(fixture.work_units):
        fixture.apply_control_action(root, step)
        assert fixture.progress(root) == step + 1

    assert fixture.verify(root).passed


@pytest.mark.parametrize("name", ["bugfix", "config", "tests", "followup"])
def test_repository_fixture_final_verifier_accepts_sequential_control_trace(tmp_path, name):
    fixture = load_fixture(name)
    root = fixture.copy_to(tmp_path)

    for step in range(fixture.work_units):
        fixture.apply_control_action(root, step)

    assert fixture.verify(root).passed


def test_repository_fixture_rejects_out_of_order_control_action(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)

    with pytest.raises(ValueError, match="sequentially"):
        fixture.apply_control_action(root, 1)


def test_repository_fixture_rejects_opaque_multi_unit_jump(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)

    (root / "project.py").write_text(fixture.steps[-1], encoding="utf-8")

    assert fixture.single_unit_advance(0, root) is False


def test_bugfix_verifier_accepts_semantically_equivalent_repository_edits(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)
    (root / "project.py").write_text(
        "VERSION = '1.0'\n\n"
        "def add(left, right):\n    return sum((left, right))\n\n"
        "def multiply(left, right):\n    return left * right\n",
        encoding="utf-8",
    )

    assert fixture.progress(root) == fixture.work_units
    assert fixture.verify(root).passed


@pytest.mark.parametrize("name", ["config", "tests", "followup"])
def test_fixture_verifier_does_not_require_an_exact_source_snapshot(tmp_path, name):
    fixture = load_fixture(name)
    root = fixture.copy_to(tmp_path)
    (root / "project.py").write_text(fixture.steps[-1] + "\n# equivalent formatting\n", encoding="utf-8")

    assert fixture.progress(root) == fixture.work_units
    assert fixture.verify(root).passed


def test_verified_terminal_step_emits_a_loadable_clean_checkpoint(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)
    world = TerminalWorld(str(root), str(tmp_path / "snapshots"))
    store = CheckpointStore(str(tmp_path / "checkpoints"))
    ledger = EffectLedger(str(tmp_path / "effects.jsonl"), "phase-1")

    receipt = run_control_step(
        "fix the repository", fixture, world, store, ledger, run_id="run-1", step=0,
    )

    assert receipt.run_id == "run-1"
    assert receipt.checkpoint_id == "ckpt_0"
    assert receipt.work_units == 1
    assert receipt.digest == world.digest()
    assert receipt.provenance == {"harness_version": "recoverybench.v0.2", "model_version": "control"}
    loaded = store.load_latest()
    assert loaded is not None
    assert loaded[0].durable_core.world.digest == receipt.digest


def test_clean_checkpoint_carries_all_prior_verified_actions(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)
    world = TerminalWorld(str(root), str(tmp_path / "snapshots"))
    store = CheckpointStore(str(tmp_path / "checkpoints"))
    ledger = EffectLedger(str(tmp_path / "effects.jsonl"), "phase-1")
    history = []

    run_control_step("fix the repository", fixture, world, store, ledger, run_id="run-1", step=0, history=history)
    run_control_step("fix the repository", fixture, world, store, ledger, run_id="run-1", step=1, history=history)

    loaded = store.load_latest()
    assert loaded is not None
    assert len(history) == 2
    assert [step.status for step in loaded[0].durable_core.plan] == ["done", "done"]


def test_failed_terminal_command_never_emits_clean_checkpoint(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)
    world = TerminalWorld(str(root), str(tmp_path / "snapshots"))
    store = CheckpointStore(str(tmp_path / "checkpoints"))
    ledger = EffectLedger(str(tmp_path / "effects.jsonl"), "phase-1")

    with pytest.raises(ValueError, match="command_failed"):
        run_control_step(
            "fix the repository", fixture, world, store, ledger,
            run_id="run-1", step=0, command="exit 9",
        )

    assert store.load_latest() is None


def test_opaque_multi_unit_terminal_change_never_emits_clean_checkpoint(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)
    world = TerminalWorld(str(root), str(tmp_path / "snapshots"))
    store = CheckpointStore(str(tmp_path / "checkpoints"))
    ledger = EffectLedger(str(tmp_path / "effects.jsonl"), "phase-1")

    with pytest.raises(ValueError, match="unverified_progress"):
        run_control_step(
            "fix the repository", fixture, world, store, ledger,
            run_id="run-1", step=0, command=fixture.control_command(fixture.work_units - 1),
        )

    assert store.load_latest() is None


def test_live_terminal_adapter_checkpoints_only_a_verified_single_repository_edit(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)
    world = TerminalWorld(str(root), str(tmp_path / "snapshots"))
    store = CheckpointStore(str(tmp_path / "checkpoints"))
    ledger = EffectLedger(str(tmp_path / "effects.jsonl"), "phase-1")
    provider = LiveModelProvider(lambda _prompt: "```python\nfrom pathlib import Path\np = Path('project.py')\np.write_text(p.read_text().replace('return a - b', 'return a + b', 1))\n```")
    history = []

    receipt = run_live_step(
        "fix the repository", fixture, world, store, ledger, provider,
        run_id="live-1", step=0, history=history, model_version="fake/live",
    )

    assert receipt.work_units == 1
    assert receipt.provenance["model_version"] == "fake/live"
    assert history[0].action.code.startswith("from pathlib")
    assert store.load_latest() is not None


def test_live_terminal_adapter_allows_read_only_inspection_before_a_verified_edit(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)
    world = TerminalWorld(str(root), str(tmp_path / "snapshots"))
    store = CheckpointStore(str(tmp_path / "checkpoints"))
    ledger = EffectLedger(str(tmp_path / "effects.jsonl"), "phase-1")

    def transport(prompt):
        if "HISTORY: (none yet" in prompt:
            return "```python\nfrom pathlib import Path\nprint(Path('README.md').read_text())\n```"
        return "```python\nfrom pathlib import Path\np = Path('project.py')\np.write_text(p.read_text().replace('return a - b', 'return a + b', 1))\n```"

    history = []
    receipt = run_live_step(
        "fix the repository", fixture, world, store, ledger, LiveModelProvider(transport),
        run_id="live-1", step=0, history=history, model_version="fake/live",
    )

    assert receipt.work_units == 1
    assert len(history) == 1
    assert "return a + b" in history[0].action.code


def test_live_terminal_adapter_rejects_an_unverified_mutation(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)
    world = TerminalWorld(str(root), str(tmp_path / "snapshots"))
    store = CheckpointStore(str(tmp_path / "checkpoints"))
    ledger = EffectLedger(str(tmp_path / "effects.jsonl"), "phase-1")
    provider = LiveModelProvider(
        lambda _prompt: "```python\nfrom pathlib import Path\nPath('note.txt').write_text('not task progress')\n```"
    )

    with pytest.raises(ValueError, match="unverified_mutation"):
        run_live_step(
            "fix the repository", fixture, world, store, ledger, provider,
            run_id="live-1", step=0, history=[], model_version="fake/live",
        )

    assert store.load_latest() is None


def test_live_terminal_adapter_lets_the_model_correct_a_non_mutating_command_error(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)
    world = TerminalWorld(str(root), str(tmp_path / "snapshots"))
    store = CheckpointStore(str(tmp_path / "checkpoints"))
    ledger = EffectLedger(str(tmp_path / "effects.jsonl"), "phase-1")

    def transport(prompt):
        if "HISTORY: (none yet" in prompt:
            return "```python\nthis is not valid python\n```"
        return "```python\nfrom pathlib import Path\np = Path('project.py')\np.write_text(p.read_text().replace('return a - b', 'return a + b', 1))\n```"

    history = []
    receipt = run_live_step(
        "fix the repository", fixture, world, store, ledger, LiveModelProvider(transport),
        run_id="live-1", step=0, history=history, model_version="fake/live",
    )

    assert receipt.work_units == 1
    assert len(history) == 1


def test_live_terminal_adapter_rejects_a_multi_unit_edit_without_checkpoint(tmp_path):
    fixture = load_fixture("bugfix")
    root = fixture.copy_to(tmp_path)
    world = TerminalWorld(str(root), str(tmp_path / "snapshots"))
    store = CheckpointStore(str(tmp_path / "checkpoints"))
    ledger = EffectLedger(str(tmp_path / "effects.jsonl"), "phase-1")
    provider = LiveModelProvider(
        lambda _prompt: "```python\nfrom pathlib import Path\nPath('project.py').write_text(\"VERSION = '1.0'\\n\\ndef add(a, b):\\n    return a + b\\n\\ndef multiply(a, b):\\n    return a * b\\n\")\n```"
    )

    with pytest.raises(ValueError, match="unverified_progress"):
        run_live_step(
            "fix the repository", fixture, world, store, ledger, provider,
            run_id="live-1", step=0, history=[], model_version="fake/live",
        )

    assert store.load_latest() is None


def test_paired_control_record_carries_required_recovery_evidence(tmp_path):
    record = run_paired_control(tmp_path, "bugfix", fault_step=1).to_record()

    assert record["schema_version"] == "recoverybench.v0.1"
    assert record["fixture"] == {"name": "bugfix", "version": "2"}
    assert record["failure"]["fired"] is True
    assert record["checkpoint"]["checkpoint_id"]
    assert record["checkpoint"]["digest"]
    assert record["baseline"]["digest"] == record["recovery"]["digest"]
    assert record["fidelity"]["no_regression"] == 1.0


def test_deterministic_matrix_writes_only_complete_fired_records(tmp_path):
    records = [
        result.to_record()
        for result in run_deterministic_matrix(tmp_path / "new-output-parent" / "runs", repeats=1)
    ]
    output = tmp_path / "records.jsonl"
    write_records(records, output)

    assert len(records) == 11
    assert len(output.read_text(encoding="utf-8").splitlines()) == 11
    assert all(record["failure"]["fired"] for record in records)
    assert deterministic_summary(records) == {
        "total": 11,
        "valid": 11,
        "invalid": 0,
        "task_success": 1.0,
        "artifact_equivalence": 1.0,
        "no_regression": 1.0,
    }
    assert normalized_records_equal(output, output)


def test_record_normalization_ignores_only_process_and_run_identity(tmp_path):
    record = run_paired_control(tmp_path, "bugfix", fault_step=1).to_record()
    different_run = deepcopy(record)
    different_run["failure"]["worker_pid"] += 1
    different_run["checkpoint"]["run_id"] = "different-run"
    different_run["failure"]["checkpoint"]["run_id"] = "different-run"
    different_run["baseline"]["worker_pid"] += 1
    different_run["recovery"]["worker_pid"] += 1

    assert normalize_record(record) == normalize_record(different_run)


def test_phase_one_verdict_rejects_deterministic_evidence_without_live_pilot(tmp_path):
    records = [run_paired_control(tmp_path, "bugfix", fault_step=1).to_record()]

    verdict = phase_1_verdict(records, live=None, artifacts_published=True, adapter_adopted=True)

    assert not verdict.passed
    assert verdict.deterministic_cells_pass
    assert verdict.deterministic_fidelity
    assert verdict.durable_failure_receipts
    assert not verdict.live_sample_size
    assert not verdict.live_fidelity


def test_phase_one_verdict_requires_all_seven_locked_criteria(tmp_path):
    records = [run_paired_control(tmp_path, "bugfix", fault_step=1).to_record()]
    live = LivePilotEvidence(
        valid_fired_pairs=40,
        model_configurations=("model-a", "model-b"),
        recovered_success=0.90,
        baseline_success=0.95,
        effect_duplicates=0,
        external_models=True,
    )

    verdict = phase_1_verdict(records, live=live, artifacts_published=True, adapter_adopted=True)

    assert verdict.passed


def test_fake_live_records_cannot_count_as_external_live_evidence(tmp_path):
    record = run_paired_control(tmp_path, "bugfix", fault_step=1).to_record()
    records = []
    for model in ("fake/a", "fake/b"):
        for _ in range(22):
            live = deepcopy(record)
            live["live"] = {"provider": "fake", "model": model}
            records.append(live)

    evidence = live_pilot_evidence(records)

    assert len(records) == 44
    assert evidence.valid_fired_pairs == 44
    assert evidence.model_configurations == ("fake:fake/a", "fake:fake/b")
    assert not evidence.external_models


def test_live_matrix_records_every_fault_cell_with_its_model_configuration(tmp_path, monkeypatch):
    paired = run_paired_control(tmp_path / "control", "bugfix", fault_step=1)
    monkeypatch.setattr(recoverybench, "run_paired_live", lambda *_args: paired)

    records = run_live_matrix(
        tmp_path / "live", [LiveRunConfig(provider="fake", model="fake/a")], repeats=1,
    )

    assert len(records) == 11
    assert all(record["live"] == {"provider": "fake", "model": "fake/a"} for record in records)


def test_live_matrix_preserves_failures_instead_of_scoring_only_successes(tmp_path, monkeypatch):
    def fail(*_args):
        raise LiveRunFailure("resume", tmp_path / "failed-run", "resume failed")

    monkeypatch.setattr(recoverybench, "run_paired_live", fail)
    records = run_live_matrix(
        tmp_path / "live", [LiveRunConfig(provider="fake", model="fake/a")], repeats=1,
    )

    evidence = live_pilot_evidence(records)

    assert len(records) == 11
    assert all(record["invalid"]["stage"] == "resume" for record in records)
    assert evidence.valid_fired_pairs == 0
    assert evidence.baseline_success == 1.0
    assert evidence.recovered_success == 0.0


def test_phase_two_diagnosis_separates_precheckpoint_failures_from_recovery_failures():
    records = [
        {"invalid": {"stage": "baseline", "detail": "ValueError: unverified_progress"},
         "outcome": {"baseline_success": False, "recovery_success": False}},
        {"invalid": {"stage": "crash", "detail": "ValueError: unverified_mutation"},
         "outcome": {"baseline_success": True, "recovery_success": False}},
        {"invalid": {"stage": "resume", "detail": "ValueError: model_no_verified_progress"},
         "outcome": {"baseline_success": True, "recovery_success": False}},
        {"outcome": {"baseline_success": True, "recovery_success": False}},
        {"outcome": {"baseline_success": True, "recovery_success": True}},
    ]

    diagnosis = diagnose_phase_one_records(records)

    assert diagnosis["attempted"] == 5
    assert diagnosis["baseline_completion_failures"] == 1
    assert diagnosis["checkpoint_acquisition_failures"] == 1
    assert diagnosis["recovery_path_failures"] == 2
    assert diagnosis["recovered_successes"] == 1
    assert diagnosis["failure_reasons"] == {
        "unverified_mutation": 1,
        "unverified_progress": 1,
        "model_no_verified_progress": 1,
    }


def test_phase_two_freeze_records_hashes_and_diagnosis(tmp_path):
    evidence = tmp_path / "phase-one.jsonl"
    evidence.write_text(
        '{"invalid":{"stage":"baseline","detail":"ValueError: unverified_progress"},'
        '"outcome":{"baseline_success":false,"recovery_success":false}}\n',
        encoding="utf-8",
    )

    frozen = freeze_phase_one_controls([evidence])

    assert frozen["schema_version"] == "cairn.phase-2-control-freeze.v0.1"
    assert frozen["records"] == 1
    assert frozen["artifacts"][0]["path"] == "phase-one.jsonl"
    assert len(frozen["artifacts"][0]["sha256"]) == 64
    assert frozen["diagnosis"]["baseline_completion_failures"] == 1


def test_phase_two_freeze_writer_preserves_a_reproducible_json_artifact(tmp_path):
    evidence = tmp_path / "phase-one.jsonl"
    evidence.write_text('{"outcome":{"baseline_success":true,"recovery_success":true}}\n', encoding="utf-8")
    output = tmp_path / "phase-two" / "control-freeze.json"

    written = write_control_freeze([evidence], output)

    assert written == output
    assert output.exists()
    assert '"records": 1' in output.read_text(encoding="utf-8")


def test_phase_two_compacted_continuation_round_trips_without_original_observations():
    history = [
        StepRecord(step=0, action=Action(kind=CODE, code="print('first')"), stdout="secret-observation"),
        StepRecord(step=1, action=Action(kind=CODE, code="print('second')"), stdout="latest-observation"),
    ]

    branch = compacted_continuation(distill("finish the task", history, mode=CHECKPOINT, step=1))

    assert branch.goal == "finish the task"
    assert branch.state.durable_core.intent.root_goal == "finish the task"
    assert len(branch.state.elastic_tail.recent_steps) == 1
    assert [record.action.code for record in branch.history] == ["print('first')", "print('second')"]
    assert all(not record.stdout for record in branch.history)


def test_phase_two_compacted_continuation_can_finish_a_repository_without_the_original_transcript(tmp_path):
    fixture = load_fixture("bugfix")
    goal = "complete the repository task"
    original = fixture.copy_to(tmp_path / "original")
    recovered_root = fixture.copy_to(tmp_path / "recovered")
    compacted_root = fixture.copy_to(tmp_path / "compacted")
    original_world = TerminalWorld(str(original), str(tmp_path / "original-snaps"))
    recovered_world = TerminalWorld(str(recovered_root), str(tmp_path / "recovered-snaps"))
    compacted_world = TerminalWorld(str(compacted_root), str(tmp_path / "compacted-snaps"))
    original_store = CheckpointStore(str(tmp_path / "original-ckpts"))
    recovered_store = CheckpointStore(str(tmp_path / "recovered-ckpts"))
    compacted_store = CheckpointStore(str(tmp_path / "compacted-ckpts"))
    original_ledger = EffectLedger(str(tmp_path / "original-effects.jsonl"), "original")
    recovered_ledger = EffectLedger(str(tmp_path / "recovered-effects.jsonl"), "recovered")
    compacted_ledger = EffectLedger(str(tmp_path / "compacted-effects.jsonl"), "compacted")
    history = []
    run_control_step(goal, fixture, original_world, original_store, original_ledger, run_id="u", step=0, history=history)
    recovered_history = []
    run_control_step(goal, fixture, recovered_world, recovered_store, recovered_ledger,
                     run_id="r", step=0, history=recovered_history)
    fixture.apply_control_action(compacted_root, 0)
    checkpoint_state = original_store.load_latest()[0]
    branch = compacted_continuation(checkpoint_state)

    def provider_for(expected_step):
        code = f"from pathlib import Path\nPath('project.py').write_text({fixture.steps[expected_step]!r})"
        return LiveModelProvider(lambda _prompt: "```python\n" + code + "\n```")

    run_live_step(goal, fixture, original_world, original_store, original_ledger, provider_for(1),
                  run_id="u", step=1, history=list(history), model_version="control")
    regrounded = recoverybench.recover(recovered_world, recovered_store, recovered_ledger)
    run_live_step(branch.goal, fixture, recovered_world, recovered_store, recovered_ledger, provider_for(1),
                  run_id="r", step=1, history=regrounded.history, model_version="control")
    run_live_step(branch.prompt, fixture, compacted_world, compacted_store, compacted_ledger, provider_for(1),
                  run_id="c", step=1, history=branch.history, model_version="control")

    assert fixture.progress(original) == fixture.progress(recovered_root) == fixture.progress(compacted_root) == 2


@pytest.mark.parametrize(
    ("field", "expected_goal", "expected_history"),
    [("intent", "", 1), ("plan", "finish", 0), ("decisions", "finish", 1),
     ("verification", "finish", 1), ("world", "finish", 1)],
)
def test_phase_two_ablation_removes_only_the_named_continuation_state_field(field, expected_goal, expected_history):
    state = distill(
        "finish", [StepRecord(step=0, action=Action(kind=CODE, code="print('done')"))],
        mode=CHECKPOINT, step=0, digest={"project.py": "digest"},
    )
    state.durable_core.verification.append(VerificationItem("unit", "pass", 0))

    branch = ablated_continuation(state, field)

    assert branch.goal == expected_goal
    assert len(branch.history) == expected_history
    if field == "decisions":
        assert not branch.state.durable_core.decisions
    if field == "verification":
        assert not branch.state.durable_core.verification
    if field == "world":
        assert not branch.state.durable_core.world.digest


def test_phase_two_compacted_continuation_renders_existing_operational_state_without_transcript():
    state = distill(
        "finish", [StepRecord(step=0, action=Action(kind=CODE, code="print('done')"))],
        mode=CHECKPOINT, step=0, digest={"project.py": "digest"},
    )
    state.durable_core.decisions[0].rationale = "the direct path worked"
    state.durable_core.verification.append(VerificationItem("unit", "pass", 0))

    prompt = compacted_continuation(state).prompt

    assert "GOAL:\nfinish" in prompt
    assert "DECISIONS:" in prompt
    assert "the direct path worked" in prompt
    assert "VERIFICATION:" in prompt
    assert "unit: pass" in prompt
    assert "WORLD:" in prompt
    assert "project.py" in prompt


def test_phase_two_live_urc_runner_uses_fresh_branches_and_records_all_outcomes(tmp_path):
    record = run_live_urc(
        tmp_path, "bugfix", split_step=0,
        config=recoverybench.LiveRunConfig(provider="fake", model="control"),
    )

    assert record["fixture"] == {"name": "bugfix", "version": "2"}
    assert record["split_step"] == 0
    assert all(record["branches"][name]["success"] for name in ("U", "R", "C"))
    assert record["branches"]["C"]["original_transcript_available"] is False
    assert record["branches"]["C"]["prompt_has_durable_state"] is True


def test_phase_two_verification_counterfactual_seeds_verified_prefix_progress(tmp_path):
    record = run_live_urc(
        tmp_path, "bugfix", split_step=0,
        config=recoverybench.LiveRunConfig(provider="fake", model="control"),
        verification_mode="progress",
    )

    assert record["verification_mode"] == "progress"
    checkpoint = next(tmp_path.glob("*/R/checkpoints/ckpt_1.json"))
    state = json.loads(checkpoint.read_text(encoding="utf-8"))["state"]
    assert state["durable_core"]["verification"] == [{"target": "step:0", "result": "pass", "at_step": 0}]


def test_phase_two_live_urc_runs_the_model_prefix_once_before_materializing_branches(monkeypatch, tmp_path):
    calls = []
    original = recoverybench.run_live_step

    def record_prefix(*args, **kwargs):
        calls.append((kwargs["run_id"], kwargs["step"]))
        return original(*args, **kwargs)

    monkeypatch.setattr(recoverybench, "run_live_step", record_prefix)
    run_live_urc(
        tmp_path, "bugfix", split_step=0,
        config=recoverybench.LiveRunConfig(provider="fake", model="control"),
    )

    assert calls.count(("prefix", 0)) == 1
    assert not any(run_id in {"U", "R", "C"} and step == 0 for run_id, step in calls)


def test_phase_two_control_prefix_reuses_the_harness_checkpoint_without_a_model_prefix(monkeypatch, tmp_path):
    live_calls = []
    control_calls = []
    live = recoverybench.run_live_step
    control = recoverybench.run_control_step

    def record_live(*args, **kwargs):
        live_calls.append((kwargs["run_id"], kwargs["step"]))
        return live(*args, **kwargs)

    def record_control(*args, **kwargs):
        control_calls.append((kwargs["run_id"], kwargs["step"]))
        return control(*args, **kwargs)

    monkeypatch.setattr(recoverybench, "run_live_step", record_live)
    monkeypatch.setattr(recoverybench, "run_control_step", record_control)
    record = run_live_urc(
        tmp_path, "bugfix", split_step=0,
        config=recoverybench.LiveRunConfig(provider="fake", model="control"), prefix_mode="control",
    )

    assert record["prefix"] == {"mode": "control", "work_units": 1}
    assert control_calls == [("prefix", 0)]
    assert ("prefix", 0) not in live_calls
    assert all(record["branches"][name]["success"] for name in ("U", "R", "C"))


def test_phase_two_single_goal_composition_removes_only_the_outer_duplicate_wrapper(tmp_path):
    record = run_live_urc(
        tmp_path, "bugfix", split_step=0,
        config=recoverybench.LiveRunConfig(provider="fake", model="control"),
        prefix_mode="control", prompt_composition="single_goal",
    )

    assert record["prompt_composition"] == "single_goal"
    assert all(record["branches"][name]["success"] for name in ("U", "R", "C"))


def test_recoverybench_control_command_uses_the_world_interpreter_for_a_portable_terminal_action():
    fixture = load_fixture("bugfix")

    assert fixture.control_command(0, interpreter="python").startswith('"python" -c ')


def test_phase_two_live_urc_runner_records_a_named_compaction_ablation(tmp_path):
    record = run_live_urc(
        tmp_path, "bugfix", split_step=0,
        config=recoverybench.LiveRunConfig(provider="fake", model="control"),
        ablate="decisions",
    )

    assert record["ablation"] == "decisions"
    assert record["branches"]["C"]["success"]


def test_phase_two_live_urc_runner_can_repeat_into_the_same_evidence_parent(tmp_path):
    config = recoverybench.LiveRunConfig(provider="fake", model="control")

    first = run_live_urc(tmp_path, "bugfix", split_step=0, config=config)
    second = run_live_urc(tmp_path, "bugfix", split_step=0, config=config)

    assert first["branches"]["U"]["success"]
    assert second["branches"]["U"]["success"]


def test_phase_two_live_urc_capture_preserves_a_failed_attempt(monkeypatch, tmp_path):
    monkeypatch.setattr("cairn.eval.phase2.run_live_urc", lambda *_a, **_k: (_ for _ in ()).throw(ValueError("no progress")))
    output = tmp_path / "failed-urc.json"

    record = capture_live_urc(tmp_path, "bugfix", split_step=0,
                              config=recoverybench.LiveRunConfig(provider="fake", model="control"),
                              evidence_path=output)

    assert record["invalid"]["stage"] == "urc"
    assert "ValueError: no progress" in record["invalid"]["detail"]
    assert json.loads(output.read_text(encoding="utf-8")) == record


def test_phase_two_live_urc_runner_keeps_completed_branch_evidence_when_a_sibling_fails(monkeypatch, tmp_path):
    original = recoverybench.run_live_step

    def fail_recovery_branch(*args, **kwargs):
        if kwargs["run_id"] == "R":
            raise ValueError("forced recovery branch failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(recoverybench, "run_live_step", fail_recovery_branch)
    record = run_live_urc(
        tmp_path, "bugfix", split_step=0,
        config=recoverybench.LiveRunConfig(provider="fake", model="control"),
    )

    assert record["branches"]["U"]["success"]
    assert not record["branches"]["R"]["success"]
    assert "forced recovery branch failure" in record["branches"]["R"]["invalid"]
    assert record["branches"]["C"]["success"]


def test_phase_two_live_urc_runner_checkpoints_branch_evidence_to_an_output_file(tmp_path):
    output = tmp_path / "urc.json"

    record = run_live_urc(
        tmp_path / "runs", "bugfix", split_step=0,
        config=recoverybench.LiveRunConfig(provider="fake", model="control"), evidence_path=output,
    )

    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == record


def test_phase_two_urc_summary_excludes_failed_uninterrupted_controls_from_pairs():
    records = [
        {"branches": {"U": {"success": True}, "R": {"success": True}, "C": {"success": True}}},
        {"branches": {"U": {"success": True}, "R": {"success": True}, "C": {"success": False}}},
        {"branches": {"U": {"success": False}, "R": {"success": True}, "C": {"success": True}}},
        {"invalid": {"stage": "urc"}},
    ]

    assert summarize_urc_records(records) == {
        "attempted": 4,
        "complete_records": 3,
        "incomplete_records": 1,
        "baseline_eligible": 2,
        "ineligible_baseline": 1,
        "recovery_successes": 2,
        "compaction_successes": 1,
        "complete_triplets": 1,
    }


def test_phase_two_matrix_cells_enumerate_every_frozen_model_boundary_and_repetition():
    protocol = {
        "matrix": {
            "models": [{"provider": "claude_code", "model": "opus"}],
            "fixtures": ["bugfix"],
            "split_steps": "all_nonterminal",
            "repetitions_per_model_fixture_split": 2,
        }
    }

    assert matrix_cells(protocol) == [
        {"provider": "claude_code", "model": "opus", "fixture": "bugfix", "split_step": 0, "repetition": 1},
        {"provider": "claude_code", "model": "opus", "fixture": "bugfix", "split_step": 1, "repetition": 1},
        {"provider": "claude_code", "model": "opus", "fixture": "bugfix", "split_step": 0, "repetition": 2},
        {"provider": "claude_code", "model": "opus", "fixture": "bugfix", "split_step": 1, "repetition": 2},
    ]
