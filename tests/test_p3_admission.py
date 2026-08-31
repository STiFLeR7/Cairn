from benchmarks.p3_admission import evaluate_admission


def _passing(attempts: int) -> dict:
    return {
        "attempts": attempts,
        "structural_failures": 0,
        "correct_decisions": attempts,
        "duplicate_free": attempts,
        "silent_losses": 0,
        "semantic_failures": 0,
        "verdict": "PASS",
    }


def test_contract_admission_requires_both_matrices_and_the_frozen_baseline():
    result = evaluate_admission({"analysis": _passing(36)}, _passing(15), freeze_matches=True)

    assert result == {"admitted": True, "failures": []}


def test_contract_admission_rejects_a_duplicate_even_when_the_other_gates_pass():
    holdout = _passing(15)
    holdout["duplicate_free"] = 14

    result = evaluate_admission(_passing(36), holdout, freeze_matches=True)

    assert result["admitted"] is False
    assert "holdout: duplicate-free evidence 14/15" in result["failures"]
