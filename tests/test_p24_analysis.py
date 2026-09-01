from benchmarks.p24_analysis import analyze_p24_records


def _branch(name: str, parent_pid: int, *, success: bool = True) -> dict:
    return {
        "success": success,
        "verified": success,
        "worker_pid": parent_pid if name == "U" else parent_pid + (1 if name == "R" else 2),
        "parent_pid": parent_pid,
        "used_in_memory_history": name == "U",
        "original_transcript_available": name == "U",
        "state_serialized": name == "C",
        "start_progress": 2,
        "accepted_progress": [3, 4],
        "final_progress": 4,
        "accepted_actions": [{"code": "one"}, {"code": "two"}],
        "final_digest": {"project.py": "same"},
    }


def test_p24_analysis_separates_triplets_from_structural_evidence():
    record = {"parent_pid": 10, "branches": {name: _branch(name, 10) for name in ("U", "R", "C")}}

    analysis = analyze_p24_records([record])

    assert analysis["attempts"] == 1
    assert analysis["eligible"] == 1
    assert analysis["recovery_successes"] == 1
    assert analysis["compaction_successes"] == 1
    assert analysis["complete_triplets"] == 1
    assert analysis["structural_failures"] == 0


def test_p24_analysis_rejects_in_memory_recovery_history():
    record = {"parent_pid": 10, "branches": {name: _branch(name, 10) for name in ("U", "R", "C")}}
    record["branches"]["R"]["used_in_memory_history"] = True

    assert analyze_p24_records([record])["structural_failures"] == 1


def test_p24_analysis_accepts_each_registered_nonterminal_split():
    record = {"parent_pid": 10, "branches": {name: _branch(name, 10) for name in ("U", "R", "C")}}
    for branch in record["branches"].values():
        branch["start_progress"] = 1
        branch["accepted_progress"] = [2, 3, 4]
        branch["accepted_actions"] = [{"code": "one"}, {"code": "two"}, {"code": "three"}]

    assert analyze_p24_records([record])["structural_failures"] == 0
