import json
from pathlib import Path

from benchmarks.p24_fixture import STEPS, register_fixture
from cairn.eval.recoverybench import load_fixture


def test_p24_fixture_progress_is_ordered_and_public(tmp_path):
    register_fixture()
    fixture = load_fixture("p24_queue_policy")
    root = fixture.copy_to(tmp_path)

    assert fixture.work_units == 4
    assert fixture.progress(root) == 0
    for step, expected_progress in enumerate((1, 2, 3, 4)):
        fixture.apply_control_action(root, step)
        assert fixture.progress(root) == expected_progress
    assert fixture.verify(root).passed is True


def test_p24_later_work_does_not_advance_before_earlier_work(tmp_path):
    register_fixture()
    fixture = load_fixture("p24_queue_policy")
    root = fixture.copy_to(tmp_path)
    (root / "project.py").write_text(STEPS[-1].replace("return 0 if priority >= 80 else 1 if priority >= 50 else 2 if priority >= 20 else 3 if priority >= 0 else 4", "return 4"), encoding="utf-8")

    assert fixture.progress(root) == 0


def test_p24_fixture_materializes_the_sealed_public_task_exactly():
    root = Path("benchmarks/recoverybench_fixtures/p24_queue_policy")
    authored = json.loads(Path("results/phase-2/p24-author-output-opencode.json").read_text(encoding="utf-8"))

    assert (root / "README.md").read_text(encoding="utf-8") == authored["public_readme"] + "\n"
    assert (root / "project.py").read_text(encoding="utf-8") == authored["starter_project_py"]
