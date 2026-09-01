from hashlib import sha256
import json
from pathlib import Path

from benchmarks.p4_claude_verdict import artifact_equivalent, evidence_manifest_matches, input_is_transcript_free, projection_is_valid, receipt_matches_intent_and_observation, snapshot_matches_record, write_evidence_manifest


def test_projection_validation_rejects_transcript_and_requires_contract_fields():
    projection = {
        "intent": "x", "active_subgoal": "x", "accepted_decisions": ["x"], "verified_work": ["x"],
        "verification_state": "passed", "world_digest": "x", "checkpoint_provenance": "x",
        "stop_condition": "x", "next_action": "x", "first_recovery_operation": "reobserve",
    }
    assert projection_is_valid(projection)
    assert not projection_is_valid(projection | {"transcript": "forbidden"})
    assert not projection_is_valid(projection | {"session_id": "forbidden"})
    assert not projection_is_valid(projection | {"accepted_decisions": []})


def test_verdict_controls_reject_changed_artifact_and_reused_session_input(tmp_path: Path):
    prompt = "fresh recovery"
    record = {
        "artifact_sha256": {"greeting.py": sha256(b"good").hexdigest()},
        "projection": {"ok": True},
        "input_boundary": {"prompt": prompt, "prompt_sha256": sha256(prompt.encode()).hexdigest(), "no_session_persistence": True, "contains_original_session_or_transcript": False},
        "argv": ["claude", "--no-session-persistence"],
    }
    (tmp_path / "greeting.py").write_text("good", encoding="utf-8")
    (tmp_path / ".cairn-continuation.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    assert input_is_transcript_free(record, prompt)
    assert snapshot_matches_record(record, tmp_path, "greeting.py")
    assert artifact_equivalent([record, record], "greeting.py")
    assert not input_is_transcript_free(record | {"argv": ["claude", "--resume", "x"]}, prompt)
    (tmp_path / "greeting.py").write_text("changed", encoding="utf-8")
    assert not snapshot_matches_record(record, tmp_path, "greeting.py")


def test_evidence_manifest_and_receipt_binding_reject_tampering(tmp_path: Path):
    raw = tmp_path / "raw.json"
    raw.write_text("raw", encoding="utf-8")
    write_evidence_manifest(tmp_path)
    assert evidence_manifest_matches(tmp_path)
    raw.write_text("tampered", encoding="utf-8")
    assert not evidence_manifest_matches(tmp_path)

    intent = {"effect_id": "e", "idempotency_key": "k", "request_fingerprint": "f"}
    observation = {"request_fingerprint": "f", "resource_id": "r"}
    receipt = intent | {"observed_from": "reobserve", "resource_id": "r"}
    assert receipt_matches_intent_and_observation(receipt, intent, observation)
    assert not receipt_matches_intent_and_observation(receipt | {"resource_id": "other"}, intent, observation)
