from benchmarks.p3_holdout import holdout_cells


def test_holdout_cells_derive_exactly_from_the_public_author_cases():
    author = {
        "acceptance_cases": [
            {"tool_class": "check-before-retry", "observation": "absent", "decision": "retry"},
            {"tool_class": "check-before-retry", "observation": "present", "decision": "skip"},
            {"tool_class": "check-before-retry", "observation": "unknown", "decision": "escalate"},
            {"tool_class": "check-before-retry", "observation": "mismatch", "decision": "escalate"},
            {"tool_class": "never-retry", "observation": "present", "decision": "escalate"},
        ]
    }

    cells = holdout_cells(author, repetitions=3)

    assert len(cells) == 15
    assert {(cell["tool_class"], cell["expected_decision"]) for cell in cells} == {
        ("check-before-retry", "retry"),
        ("check-before-retry", "skip"),
        ("check-before-retry", "escalate"),
        ("never-retry", "escalate"),
    }
