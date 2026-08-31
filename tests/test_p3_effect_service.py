from pathlib import Path

from benchmarks.p3_effect_service import CreateOnceProvider, Intent


def _intent(*, fingerprint: str = "request-a") -> Intent:
    return Intent(
        effect_id="effect-1",
        idempotency_key="create-1",
        request_fingerprint=fingerprint,
        tool_class="check-before-retry",
    )


def test_provider_commits_once_for_matching_create_once_key(tmp_path: Path):
    provider = CreateOnceProvider(tmp_path / "remote")

    first = provider.commit(_intent())
    second = provider.commit(_intent())

    assert first.resource_id == second.resource_id
    assert provider.commit_count == 1
    assert provider.call_count == 2
    assert provider.observe(_intent()).state == "present"


def test_provider_observes_absent_before_commit(tmp_path: Path):
    provider = CreateOnceProvider(tmp_path / "remote")

    provider.dispatch(_intent())

    assert provider.observe(_intent()).state == "absent"
    assert provider.call_count == 1
    assert provider.commit_count == 0


def test_provider_detects_same_key_with_different_request(tmp_path: Path):
    provider = CreateOnceProvider(tmp_path / "remote")
    provider.commit(_intent())

    observation = provider.observe(_intent(fingerprint="request-b"))

    assert observation.state == "mismatch"
    assert observation.resource_id


def test_provider_can_report_unknown_without_creating_a_resource(tmp_path: Path):
    provider = CreateOnceProvider(tmp_path / "remote")
    provider.set_unknown(True)

    observation = provider.observe(_intent())

    assert observation.state == "unknown"
    assert provider.commit_count == 0
