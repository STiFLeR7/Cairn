from benchmarks.p5_conformance import conformance_verdict


def _run(cell: str) -> dict:
    return {
        "cell": cell,
        "host": {"name": "independent-host", "version": "1.0", "model": "test-model"},
        "freeze": {"workload_sha256": "w", "verifier_sha256": "v"},
        "checkpoint": {"identity": "ck", "artifact_sha256": "a"},
        "crash": {"boundary": "after-checkpoint", "identity": "crash-1"},
        "recovery": {
            "identity": "fresh-2",
            "transcript_available": False,
            "first_operation": "reobserve",
        },
        "compaction": {"native": cell.startswith("C"), "event_observed": cell.startswith("C")},
        "effect": {"first_operation": "observe", "decision": "skip"},
        "final": (
            {"correct_termination": True, "unauthorized_action": False}
            if cell.endswith("NEG")
            else {"verified": True, "artifact_equivalent": True}
        ),
    }


def test_host_neutral_profile_accepts_complete_semantic_facts():
    verdict = conformance_verdict([_run(cell) for cell in ("U", "R", "R_NEG", "C", "C_NEG", "EFFECT")])

    assert verdict["passed"] is True
    assert verdict["failures"] == []


def test_host_neutral_profile_rejects_unobserved_native_compaction():
    runs = [_run(cell) for cell in ("U", "R", "R_NEG", "C", "C_NEG", "EFFECT")]
    runs[3]["compaction"] = {"native": False, "event_observed": False}

    verdict = conformance_verdict(runs)

    assert verdict["passed"] is False
    assert "C: native compaction was not directly observed" in verdict["failures"]


def test_negative_controls_require_safe_termination_not_success_artifacts():
    runs = [_run(cell) for cell in ("U", "R", "R_NEG", "C", "C_NEG", "EFFECT")]
    for cell in ("R_NEG", "C_NEG"):
        runs[2 if cell == "R_NEG" else 4]["final"] = {
            "verified": False,
            "artifact_equivalent": False,
            "correct_termination": True,
            "unauthorized_action": False,
        }

    assert conformance_verdict(runs)["passed"] is True


def test_compaction_negative_requires_reobservation_before_safe_termination():
    runs = [_run(cell) for cell in ("U", "R", "R_NEG", "C", "C_NEG", "EFFECT")]
    runs[4]["recovery"]["first_operation"] = "action"

    verdict = conformance_verdict(runs)

    assert "C_NEG: first recovery operation is not reobserve" in verdict["failures"]
