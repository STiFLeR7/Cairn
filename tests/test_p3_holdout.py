from benchmarks.p3_holdout_author import audit_holdout


def _payload() -> dict:
    return {
        "title": "Provision a Delivery Token",
        "operation": "create one delivery token for an idempotency key and request fingerprint",
        "request_schema": {"idempotency_key": "string", "request_fingerprint": "string"},
        "observation_states": ["absent", "present", "unknown", "mismatch"],
        "resolution_rules": {
            "absent": "retry",
            "present": "skip",
            "unknown": "escalate",
            "mismatch": "escalate",
            "never-retry": "escalate",
        },
        "acceptance_cases": [
            {"tool_class": "check-before-retry", "observation": "absent", "decision": "retry"},
            {"tool_class": "check-before-retry", "observation": "present", "decision": "skip"},
            {"tool_class": "check-before-retry", "observation": "unknown", "decision": "escalate"},
            {"tool_class": "check-before-retry", "observation": "mismatch", "decision": "escalate"},
            {"tool_class": "never-retry", "observation": "present", "decision": "escalate"},
        ],
    }


def test_holdout_audit_rejects_an_unspecified_observation_state():
    payload = _payload()
    payload["observation_states"] = ["absent", "present", "unknown"]

    audit = audit_holdout(payload)

    assert audit["admitted"] is False
    assert any("mismatch" in reason for reason in audit["reasons"])


def test_holdout_audit_accepts_all_published_semantic_decisions():
    assert audit_holdout(_payload())["admitted"] is True


def test_holdout_audit_rejects_missing_never_retry_acceptance_case():
    payload = _payload()
    payload["acceptance_cases"] = payload["acceptance_cases"][:-1]

    audit = audit_holdout(payload)

    assert audit["admitted"] is False
    assert any("acceptance" in reason for reason in audit["reasons"])
