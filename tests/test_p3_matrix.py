from benchmarks.p3_matrix import reference_cells


def test_reference_matrix_has_exactly_twelve_rows_times_three_repetitions():
    cells = reference_cells({"matrix": {"repetitions": 3}})

    assert len(cells) == 36
    assert {cell["row"] for cell in cells} == {
        "intent-absent-retry",
        "dispatch-absent-retry",
        "commit-skip",
        "response-skip",
        "receipt-skip",
        "unknown-escalate",
        "mismatch-escalate",
        "never-retry-escalate",
        "safe-retry-convergent",
        "normal-check-before-retry",
        "normal-safe-to-retry",
        "normal-never-retry",
    }
