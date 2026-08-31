"""Public-spec audit for the independently authored Phase 3 holdout."""

from __future__ import annotations


_STATES = {"absent", "present", "unknown", "mismatch"}
_DECISIONS = {"retry", "skip", "escalate"}


def audit_holdout(payload: dict) -> dict:
    reasons = []
    if not isinstance(payload.get("title"), str) or not isinstance(payload.get("operation"), str):
        reasons.append("title and operation must be published strings")
    if set(payload.get("request_schema", {})) != {"idempotency_key", "request_fingerprint"}:
        reasons.append("request schema must publish idempotency_key and request_fingerprint")
    published_states = set(payload.get("observation_states", []))
    for state in sorted(_STATES - published_states):
        reasons.append(f"missing published observation state: {state}")
    rules = payload.get("resolution_rules", {})
    for key, decision in {"absent": "retry", "present": "skip", "unknown": "escalate", "mismatch": "escalate", "never-retry": "escalate"}.items():
        if rules.get(key) != decision:
            reasons.append(f"missing or invalid rule: {key}")
    cases = payload.get("acceptance_cases", [])
    required_cases = {
        ("check-before-retry", "absent", "retry"),
        ("check-before-retry", "present", "skip"),
        ("check-before-retry", "unknown", "escalate"),
        ("check-before-retry", "mismatch", "escalate"),
        ("never-retry", "present", "escalate"),
    }
    published_cases = {(case.get("tool_class"), case.get("observation"), case.get("decision")) for case in cases}
    if not required_cases <= published_cases:
        reasons.append("acceptance cases must publish valid observations and decisions")
    return {"admitted": not reasons, "reasons": reasons}
