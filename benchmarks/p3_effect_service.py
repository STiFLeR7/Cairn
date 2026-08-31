"""Deterministic provider-like create-once effect used only by Phase 3."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path


@dataclass(frozen=True)
class Intent:
    effect_id: str
    idempotency_key: str
    request_fingerprint: str
    tool_class: str


@dataclass(frozen=True)
class Observation:
    state: str
    resource_id: str = ""
    request_fingerprint: str = ""


@dataclass(frozen=True)
class Receipt:
    effect_id: str
    idempotency_key: str
    request_fingerprint: str
    resource_id: str
    observed_from: str


class CreateOnceProvider:
    """A remote-root service: the same key/fingerprint creates one resource."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._state_path = self.root / "provider.json"
        self._events_path = self.root / "provider-events.jsonl"

    def _state(self) -> dict:
        if not self._state_path.exists():
            return {"unknown": False, "resources": {}}
        return json.loads(self._state_path.read_text(encoding="utf-8"))

    def _save(self, state: dict) -> None:
        temporary = self._state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
        temporary.replace(self._state_path)

    def _event(self, kind: str, intent: Intent) -> None:
        with self._events_path.open("a", encoding="utf-8") as output:
            output.write(json.dumps({"kind": kind, **asdict(intent)}, sort_keys=True) + "\n")

    @property
    def call_count(self) -> int:
        if not self._events_path.exists():
            return 0
        return sum(1 for line in self._events_path.read_text(encoding="utf-8").splitlines() if line)

    @property
    def commit_count(self) -> int:
        return len(self._state()["resources"])

    def set_unknown(self, value: bool) -> None:
        state = self._state()
        state["unknown"] = value
        self._save(state)

    def dispatch(self, intent: Intent) -> None:
        self._event("dispatch", intent)

    def commit(self, intent: Intent) -> Receipt:
        self._event("commit", intent)
        state = self._state()
        existing = state["resources"].get(intent.idempotency_key)
        if existing is None:
            resource_id = "resource-" + sha256(intent.idempotency_key.encode("utf-8")).hexdigest()[:12]
            existing = {"resource_id": resource_id, "request_fingerprint": intent.request_fingerprint}
            state["resources"][intent.idempotency_key] = existing
            self._save(state)
        return Receipt(
            effect_id=intent.effect_id,
            idempotency_key=intent.idempotency_key,
            request_fingerprint=existing["request_fingerprint"],
            resource_id=existing["resource_id"],
            observed_from="commit",
        )

    def observe(self, intent: Intent) -> Observation:
        state = self._state()
        if state["unknown"]:
            return Observation("unknown")
        existing = state["resources"].get(intent.idempotency_key)
        if existing is None:
            return Observation("absent")
        if existing["request_fingerprint"] != intent.request_fingerprint:
            return Observation("mismatch", existing["resource_id"], existing["request_fingerprint"])
        return Observation("present", existing["resource_id"], existing["request_fingerprint"])
