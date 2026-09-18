from __future__ import annotations

import json
from pathlib import Path

import pytest

from conformance.v2.stage6b_provider import (
    candidate_observation_from_provider,
    launch_provider,
    verify_effect_evidence,
)


def test_provider_is_a_separate_process_with_a_durable_create_once_ledger(tmp_path: Path):
    ledger = tmp_path / "provider-ledger"
    with launch_provider(ledger) as provider:
        first = provider.create(
            idempotency_key="request-1",
            request_fingerprint="fingerprint-1",
            request_id="dispatch-1",
        )
        second = provider.create(
            idempotency_key="request-1",
            request_fingerprint="fingerprint-1",
            request_id="dispatch-2",
        )
        observation = provider.observe("request-1")

        assert provider.pid != 0
        assert provider._token not in " ".join(map(str, provider._process.args))  # noqa: SLF001
        assert first["resource_id"] == second["resource_id"]
        assert observation["state"] == "present"
        assert observation["request_fingerprint"] == "fingerprint-1"

    persisted = json.loads((ledger / "provider-ledger.json").read_text(encoding="utf-8"))
    assert persisted["resources"]["request-1"]["create_count"] == 1
    assert (ledger / "provider-events.jsonl").is_file()

    with launch_provider(ledger) as restarted:
        after_restart = restarted.observe("request-1")

    assert after_restart["state"] == "present"
    assert after_restart["resource_id"] == first["resource_id"]


def test_provider_observation_is_ledger_derived_not_cell_derived(tmp_path: Path):
    with launch_provider(tmp_path / "ledger") as provider:
        provider.create(
            idempotency_key="request-2",
            request_fingerprint="fingerprint-2",
            request_id="dispatch-2",
        )
        actual = provider.observe("request-2")
        absent = provider.observe("different-request")

    assert {key: actual[key] for key in (
        "state", "observation", "resource_id", "request_fingerprint",
        "resource_fingerprint", "idempotency_key", "receipt_id",
    )} == {
        "state": "present",
        "observation": "present",
        "resource_id": actual["resource_id"],
        "request_fingerprint": "fingerprint-2",
        "resource_fingerprint": "fingerprint-2",
        "idempotency_key": "request-2",
        "receipt_id": actual["receipt_id"],
    }
    assert {key: absent[key] for key in (
        "state", "observation", "resource_id", "request_fingerprint",
        "resource_fingerprint", "idempotency_key", "receipt_id",
    )} == {
        "state": "absent",
        "observation": "absent",
        "resource_id": None,
        "request_fingerprint": None,
        "resource_fingerprint": None,
        "idempotency_key": "different-request",
        "receipt_id": None,
    }


def test_candidate_observation_exposes_only_provider_derived_evaluator_fields(tmp_path: Path):
    with launch_provider(tmp_path / "ledger") as provider:
        receipt = provider.create(
            idempotency_key="request-2b",
            request_fingerprint="fingerprint-2b",
            request_id="dispatch-2b",
        )
        present = provider.observe("request-2b")
        absent = provider.observe("request-absent")
        provider.configure(unknown=True)
        unknown = provider.observe("request-unknown")

    present_envelope = candidate_observation_from_provider(present)
    assert present_envelope == {
        "state": "present",
        "observation": "present",
        "resource_id": present["resource_id"],
        "request_fingerprint": "fingerprint-2b",
        "resource_fingerprint": "fingerprint-2b",
        "idempotency_key": "request-2b",
        "receipt_id": receipt["receipt_id"],
        "observation_event_id": present["observation_event_id"],
    }
    for raw, state in ((absent, "absent"), (unknown, "unknown")):
        envelope = candidate_observation_from_provider(raw)
        assert envelope["state"] == envelope["observation"] == state
        assert envelope["idempotency_key"] == raw["idempotency_key"]
        assert envelope["resource_id"] is None
        assert envelope["request_fingerprint"] is None
        assert envelope["resource_fingerprint"] is None
        assert envelope["receipt_id"] is None
        assert envelope["observation_event_id"] == raw["observation_event_id"]


def test_effect_evaluator_rejects_synthetic_or_unobserved_effect_evidence(tmp_path: Path):
    with launch_provider(tmp_path / "ledger") as provider:
        with pytest.raises(ValueError, match="durable provider ledger"):
            verify_effect_evidence(
                provider=provider,
                idempotency_key="request-3",
                expected_fingerprint="fingerprint-3",
                candidate_observation={"state": "present", "resource_id": "fixed"},
                candidate_decision="skip",
                observation_event_sequence=("reobservation-request", "provider-observation"),
            )


def test_effect_evaluator_rejects_retry_before_real_reobservation_and_duplicate_create(tmp_path: Path):
    with launch_provider(tmp_path / "ledger") as provider:
        provider.create(
            idempotency_key="request-4",
            request_fingerprint="fingerprint-4",
            request_id="dispatch-4",
        )
        with pytest.raises(ValueError, match="re-observation"):
            verify_effect_evidence(
                provider=provider,
                idempotency_key="request-4",
                expected_fingerprint="fingerprint-4",
                candidate_observation={"state": "present"},
                candidate_decision="retry",
                observation_event_sequence=("candidate-result",),
            )


def test_effect_evaluator_requires_a_real_ledger_receipt_for_retry(tmp_path: Path):
    with launch_provider(tmp_path / "ledger") as provider:
        observed = provider.observe("request-5")
        candidate_observation = candidate_observation_from_provider(observed)
        with pytest.raises(ValueError, match="receipt is absent from the durable provider ledger"):
            verify_effect_evidence(
                provider=provider,
                idempotency_key="request-5",
                expected_fingerprint="fingerprint-5",
                candidate_observation=candidate_observation,
                candidate_decision="retry",
                observation_event_sequence=(
                    "reobservation-request", "provider-observation", "candidate-result",
                    "post-result-provider-dispatch",
                ),
                tool_class="safe-to-retry",
                provider_observation=observed,
                retry_receipt={"receipt_id": "invented", "resource_id": "fixed"},
            )


def test_effect_evaluator_rejects_a_real_retry_receipt_without_post_result_dispatch(tmp_path: Path):
    with launch_provider(tmp_path / "ledger") as provider:
        observed = provider.observe("request-6")
        receipt = provider.create(
            idempotency_key="request-6",
            request_fingerprint="fingerprint-6",
            request_id="post-recovery-dispatch-6",
        )
        candidate_observation = candidate_observation_from_provider(observed)
        with pytest.raises(ValueError, match="post-result provider dispatch"):
            verify_effect_evidence(
                provider=provider,
                idempotency_key="request-6",
                expected_fingerprint="fingerprint-6",
                candidate_observation=candidate_observation,
                candidate_decision="retry",
                observation_event_sequence=(
                    "reobservation-request", "provider-observation", "candidate-result",
                ),
                tool_class="safe-to-retry",
                provider_observation=observed,
                retry_receipt=receipt,
            )


def test_effect_evaluator_accepts_real_observation_then_one_real_retry(tmp_path: Path):
    with launch_provider(tmp_path / "ledger") as provider:
        observed = provider.observe("request-7")
        receipt = provider.create(
            idempotency_key="request-7",
            request_fingerprint="fingerprint-7",
            request_id="post-recovery-dispatch-7",
        )
        candidate_observation = candidate_observation_from_provider(observed)
        verdict = verify_effect_evidence(
            provider=provider,
            idempotency_key="request-7",
            expected_fingerprint="fingerprint-7",
            candidate_observation=candidate_observation,
            candidate_decision="retry",
            observation_event_sequence=(
                "reobservation-request", "provider-observation", "candidate-result",
                "post-result-provider-dispatch",
            ),
            tool_class="safe-to-retry",
            provider_observation=observed,
            retry_receipt=receipt,
        )

    assert verdict["decision"] == "retry"
    assert verdict["ledger"]["resources"]["request-7"]["create_count"] == 1


def test_effect_evaluator_rejects_provider_ledger_inside_candidate_workspace(tmp_path: Path):
    candidate_root = tmp_path / "candidate"
    with launch_provider(candidate_root / "provider-ledger") as provider:
        observed = provider.observe("request-8")
        candidate_observation = {
            key: observed[key]
            for key in ("state", "resource_id", "request_fingerprint", "idempotency_key")
        }
        with pytest.raises(ValueError, match="inside the candidate workspace"):
            verify_effect_evidence(
                provider=provider,
                idempotency_key="request-8",
                expected_fingerprint="fingerprint-8",
                candidate_observation=candidate_observation,
                candidate_decision="escalate",
                observation_event_sequence=(
                    "reobservation-request", "provider-observation", "candidate-result",
                ),
                provider_observation=observed,
                candidate_root=candidate_root,
            )
