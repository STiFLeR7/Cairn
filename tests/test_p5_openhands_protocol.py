import base64
from pathlib import Path
import re

import pytest

import benchmarks.p5_openhands_protocol as protocol
from benchmarks.p5_openhands_protocol import coding_commands, continuation_payload, validate_workload_manifest


def test_p5_openhands_workload_manifest_rejects_a_changed_sealed_file(tmp_path: Path):
    root = tmp_path / "fixture"
    source = root / "sealed-workloads" / "coding"
    source.mkdir(parents=True)
    task = source / "TASK.md"
    task.write_text("original\n", encoding="utf-8")
    (root / "workload-manifest.json").write_text(
        '{"files": [{"path": "sealed-workloads/coding/TASK.md", "bytes": 9, '
        '"sha256": "b0a5d6e1a1f5d8d0b32a99b02601bd0e5f7c5afdc5ea2c2c740e5a7f42d08e1e"}]}\n',
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="sealed workload mismatch"):
        validate_workload_manifest(root)


def test_p5_recovery_input_is_raw_contract_state_without_host_history():
    state = continuation_payload({"route_report.py": "abc"}, blocked=True)

    assert state["durable_core"]["plan"][0]["status"] == "done"
    assert state["durable_core"]["plan"][1]["status"] == "blocked"
    assert state["durable_core"]["verification"][0]["result"] == "pass"
    assert "session" not in str(state).lower()
    assert "transcript" not in str(state).lower()


def test_p5_recovery_command_targets_the_sealed_completion_artifact():
    command = coding_commands(recovery=True)[1]

    assert "Set-Content -Path completion.txt -Value" in command


def test_p5_initial_control_formats_an_empty_route_without_a_trailing_space():
    command = coding_commands()[1]
    encoded = re.search(r"b64decode\('([^']+)'\)", command).group(1)
    namespace: dict[str, object] = {}
    exec(base64.b64decode(encoded), namespace)

    assert namespace["make_route_report"]([{"route": "solo", "stops": []}]) == "solo:"


def test_p5_protocol_exposes_a_raw_evidence_manifest_writer(tmp_path: Path):
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "raw.json").write_text('{"event":"observed"}\n', encoding="utf-8")

    manifest = protocol.write_evidence_manifest(root)

    assert manifest["schema_version"] == "cairn.p5-evidence-manifest.v0"
    assert [entry["path"] for entry in manifest["entries"]] == ["raw.json"]
    assert protocol.evidence_manifest_matches(root) is True
