import json

from benchmarks.phase2_acquisition_continuity import analyze_records


def test_analyzer_separates_checkpoint_acquisition_from_continuity():
    records = [
        {"live": {"model": "m"}, "fixture": {"name": "bugfix"}, "split_step": 0,
         "branches": {"U": {"success": True}, "R": {"success": True}, "C": {"success": False, "invalid": "ValueError: no progress"}}},
        {"live": {"model": "m"}, "fixture": {"name": "bugfix"}, "split_step": 1,
         "branches": {"U": {"success": False, "invalid": "ValueError: unverified_progress"}, "R": {"success": True}, "C": {"success": True}}},
    ]

    result = analyze_records(records)

    assert result["attempts"] == 2
    assert result["acquisition"]["eligible"] == 1
    assert result["acquisition"]["ineligible"] == 1
    assert result["continuity"] == {"eligible": 1, "recovery_successes": 1, "compaction_successes": 0, "complete_triplets": 0}
    assert result["conditional_divergence"] == {"recovery_only_failures": 0, "compaction_only_failures": 1, "both_failures": 0}
    assert result["failure_classes"] == {"U": {"unverified_progress": 1}, "R": {}, "C": {"no progress": 1}}


def test_analyzer_json_round_trip(tmp_path):
    output = tmp_path / "analysis.json"
    records = [{"branches": {"U": {"success": True}, "R": {"success": True}, "C": {"success": True}}}]
    result = analyze_records(records)
    output.write_text(json.dumps(result), encoding="utf-8")

    assert json.loads(output.read_text(encoding="utf-8")) == result


def test_terminal_invalid_attempt_is_acquisition_failure_not_incomplete():
    result = analyze_records([
        {"invalid": {"stage": "urc", "detail": "LiveModelConfigError: chat request timed out"}},
    ])

    assert result["incomplete"] == 0
    assert result["terminal_invalid"] == 1
    assert result["acquisition"] == {"eligible": 0, "ineligible": 1}
    assert result["terminal_failure_classes"] == {"chat request timed out": 1}
