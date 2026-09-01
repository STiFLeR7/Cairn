from __future__ import annotations

import json

from benchmarks.p24_author import audit_author_output
from benchmarks.p24_freeze import freeze_manifest, frozen_paths_match


def _author_payload() -> dict:
    cases = [
        {"function": "priority_band", "args": [39], "expected": "low"},
        {"function": "priority_band", "args": [40], "expected": "normal"},
        {"function": "retry_schedule", "args": [0], "expected": []},
        {"function": "retry_schedule", "args": [5], "expected": [1, 2, 4, 8, 8]},
        {
            "function": "dispatchable_ids",
            "args": [[{"id": "a", "state": "queued", "blocked": False}]],
            "expected": ["a"],
        },
        {"function": "partition_batches", "args": [[], 2], "expected": []},
    ]
    return {
        "task_id": "p24_queue_policy",
        "title": "Queue policy",
        "functions": [
            {"name": "priority_band", "domain": "score is an integer"},
            {"name": "retry_schedule", "domain": "attempts is a non-negative integer"},
            {"name": "dispatchable_ids", "domain": "jobs are dictionaries with id, state, blocked"},
            {"name": "partition_batches", "domain": "ids is a list and size is a positive integer"},
        ],
        "starter_project_py": "def priority_band(score):\n    return ''\n",
        "public_readme": (
            "# Queue policy\n\n"
            "Inputs outside the stated domains are not scored.\n\n"
            "## Acceptance cases\n\n```json\n"
            + json.dumps(cases, indent=2, sort_keys=True)
            + "\n```\n"
        ),
        "acceptance_cases": cases,
    }


def test_freeze_manifest_detects_changed_frozen_file(tmp_path):
    frozen = tmp_path / "frozen.py"
    frozen.write_text("a = 1\n", encoding="utf-8")

    manifest = freeze_manifest([frozen], {"branch": "test"})

    assert frozen_paths_match(manifest) is True
    frozen.write_text("a = 2\n", encoding="utf-8")
    assert frozen_paths_match(manifest) is False


def test_author_audit_accepts_cases_published_in_the_public_readme():
    audit = audit_author_output(_author_payload())

    assert audit["admitted"] is True
    assert audit["reasons"] == []


def test_author_audit_rejects_a_scored_case_missing_from_public_readme():
    payload = _author_payload()
    payload["acceptance_cases"].append(
        {"function": "priority_band", "args": [70], "expected": "urgent"}
    )

    audit = audit_author_output(payload)

    assert audit["admitted"] is False
    assert "unpublished_acceptance_case" in audit["reasons"]


def test_author_audit_rejects_exposed_v12_function_names():
    payload = _author_payload()
    payload["functions"][0]["name"] = "normalize_key"

    audit = audit_author_output(payload)

    assert audit["admitted"] is False
    assert "exposed_v12_function_name" in audit["reasons"]
