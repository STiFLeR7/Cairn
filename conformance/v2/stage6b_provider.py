"""Verifier-owned, durable create-once provider for a Stage 6B holdout.

The provider is intentionally separate from a candidate workspace.  A sealer
may use its control endpoint to establish an ambiguous pre-crash condition,
but recovery observations and final verdicts must be read back from this
provider's durable ledger.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from typing import Any, Iterator
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    with temporary.open("w", encoding="utf-8") as output:
        output.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        return default
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


class _Ledger:
    def __init__(self, root: Path):
        self.root = root
        self.state_path = root / "provider-ledger.json"
        self.events_path = root / "provider-events.jsonl"
        self.root.mkdir(parents=True, exist_ok=True)

    def state(self) -> dict[str, Any]:
        return _read_json(
            self.state_path,
            {
                "schema_version": "cairn.stage6b-provider.v1",
                "unknown": False,
                "resources": {},
                "receipts": {},
            },
        )

    def save(self, state: dict[str, Any]) -> None:
        _write_json(self.state_path, state)

    def event(self, kind: str, **data: Any) -> dict[str, Any]:
        record = {
            "event_id": secrets.token_urlsafe(18),
            "kind": kind,
            "provider_pid": os.getpid(),
            "at_utc": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        with self.events_path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, sort_keys=True) + "\n")
            output.flush()
            os.fsync(output.fileno())
        return record

    def dispatch(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.event("dispatch", **payload)

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        required = ("idempotency_key", "request_fingerprint", "request_id")
        if any(not isinstance(payload.get(name), str) or not payload[name] for name in required):
            raise ValueError("create requires non-empty idempotency_key, request_fingerprint, and request_id")
        self.dispatch(payload)
        state = self.state()
        resources = state["resources"]
        key = payload["idempotency_key"]
        existing = resources.get(key)
        if existing is None:
            existing = {
                "resource_id": "resource-" + secrets.token_hex(16),
                "request_fingerprint": payload["request_fingerprint"],
                "first_request_id": payload["request_id"],
                "create_count": 1,
            }
            resources[key] = existing
            self.save(state)
            self.event("create_committed", idempotency_key=key, **existing)
        else:
            self.event("create_idempotent", idempotency_key=key, request_id=payload["request_id"], resource_id=existing["resource_id"])
        receipt = {
            "receipt_id": "receipt-" + secrets.token_hex(16),
            "idempotency_key": key,
            "request_fingerprint": existing["request_fingerprint"],
            "resource_id": existing["resource_id"],
        }
        state = self.state()
        state.setdefault("receipts", {})[receipt["receipt_id"]] = receipt
        self.save(state)
        self.event("receipt_issued", **receipt)
        return receipt

    def observe(self, idempotency_key: str) -> dict[str, Any]:
        state = self.state()
        if state.get("unknown"):
            response = {
                "state": "unknown", "idempotency_key": idempotency_key,
                "resource_id": None, "request_fingerprint": None,
            }
        else:
            resource = state["resources"].get(idempotency_key)
            response = {
                "state": "absent" if resource is None else "present",
                "idempotency_key": idempotency_key,
                "resource_id": None if resource is None else resource["resource_id"],
                "request_fingerprint": None if resource is None else resource["request_fingerprint"],
            }
        response["receipt_id"] = next(
            (
                receipt_id
                for receipt_id, receipt in reversed(list(state.get("receipts", {}).items()))
                if receipt.get("idempotency_key") == idempotency_key
                and receipt.get("resource_id") == response["resource_id"]
            ),
            None,
        )
        response["observation"] = response["state"]
        response["resource_fingerprint"] = response["request_fingerprint"]
        event = self.event("observe", **response)
        return {**response, "observation_event_id": event["event_id"]}

    def configure(self, payload: dict[str, Any]) -> dict[str, Any]:
        state = self.state()
        state["unknown"] = bool(payload.get("unknown", False))
        self.save(state)
        event = self.event("configured", unknown=state["unknown"])
        return {"unknown": state["unknown"], "configuration_event_id": event["event_id"]}


class _Handler(BaseHTTPRequestHandler):
    server: "_ProviderServer"

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _authorized(self) -> bool:
        return self.headers.get("X-Stage6B-Provider-Key") == self.server.token

    def _json(self, status: int, value: object) -> None:
        encoded = json.dumps(value, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        value = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("request body is not an object")
        return value

    def do_POST(self) -> None:  # noqa: N802
        if not self._authorized():
            self._json(403, {"error": "forbidden"})
            return
        try:
            payload = self._body()
            if self.path == "/v1/create":
                self._json(200, self.server.ledger.create(payload))
            elif self.path == "/v1/dispatch":
                self._json(200, self.server.ledger.dispatch(payload))
            elif self.path == "/v1/control":
                self._json(200, self.server.ledger.configure(payload))
            else:
                self._json(404, {"error": "not found"})
        except (ValueError, json.JSONDecodeError) as error:
            self._json(400, {"error": str(error)})

    def do_GET(self) -> None:  # noqa: N802
        if not self._authorized():
            self._json(403, {"error": "forbidden"})
            return
        query = parse_qs(urlparse(self.path).query)
        if urlparse(self.path).path != "/v1/observe" or len(query.get("idempotency_key", [])) != 1:
            self._json(400, {"error": "idempotency_key is required"})
            return
        self._json(200, self.server.ledger.observe(query["idempotency_key"][0]))


class _ProviderServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], ledger: _Ledger, token: str):
        super().__init__(address, _Handler)
        self.ledger = ledger
        self.token = token


def _serve(ledger: Path, ready: Path, token: str) -> None:
    server = _ProviderServer(("127.0.0.1", 0), _Ledger(ledger), token)
    _write_json(ready, {"pid": os.getpid(), "port": server.server_port})
    server.serve_forever(poll_interval=0.05)


class ProviderClient:
    """Verifier-only client; the candidate receives no provider credentials."""

    def __init__(self, port: int, token: str, process: subprocess.Popen[str]):
        self.port = port
        self._token = token
        self._process = process

    @property
    def pid(self) -> int:
        return self._process.pid

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"http://127.0.0.1:{self.port}{path}", data=data, method=method,
            headers={"Content-Type": "application/json", "X-Stage6B-Provider-Key": self._token},
        )
        try:
            with urlopen(request, timeout=3) as response:  # noqa: S310 - loopback verifier service
                value = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise ValueError(error.read().decode("utf-8")) from error
        if not isinstance(value, dict):
            raise ValueError("provider response is not an object")
        return value

    def dispatch(self, *, idempotency_key: str, request_fingerprint: str, request_id: str) -> dict[str, Any]:
        return self._request("POST", "/v1/dispatch", {"idempotency_key": idempotency_key, "request_fingerprint": request_fingerprint, "request_id": request_id})

    def create(self, *, idempotency_key: str, request_fingerprint: str, request_id: str) -> dict[str, Any]:
        return self._request("POST", "/v1/create", {"idempotency_key": idempotency_key, "request_fingerprint": request_fingerprint, "request_id": request_id})

    def observe(self, idempotency_key: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/observe?idempotency_key={idempotency_key}")

    def configure(self, *, unknown: bool) -> dict[str, Any]:
        return self._request("POST", "/v1/control", {"unknown": unknown})

    def ledger(self) -> dict[str, Any]:
        # The verifier owns this path; a candidate never receives it.
        return _read_json(self._ledger_path, {"resources": {}})


def candidate_observation_from_provider(observation: dict[str, Any]) -> dict[str, Any]:
    """Expose only the provider's durable observation in the host-visible envelope."""
    state = observation.get("state")
    if state not in {"present", "absent", "unknown"}:
        raise ValueError("provider observation state is invalid")
    if observation.get("observation") not in {None, state}:
        raise ValueError("provider observation alias does not match state")
    resource_id = observation.get("resource_id")
    request_fingerprint = observation.get("request_fingerprint")
    receipt_id = observation.get("receipt_id")
    if observation.get("resource_fingerprint") not in {None, request_fingerprint}:
        raise ValueError("provider resource fingerprint alias does not match request fingerprint")
    if state != "present" and any(value is not None for value in (resource_id, request_fingerprint, receipt_id)):
        raise ValueError("absent or unknown provider observation contains resource evidence")
    return {
        "state": state,
        "observation": state,
        "resource_id": resource_id,
        "request_fingerprint": request_fingerprint,
        "resource_fingerprint": request_fingerprint,
        "idempotency_key": observation.get("idempotency_key"),
        "receipt_id": receipt_id,
        "observation_event_id": observation.get("observation_event_id"),
    }


@contextmanager
def launch_provider(ledger: Path) -> Iterator[ProviderClient]:
    """Start one provider process whose durable ledger is outside candidate state."""
    ledger = ledger.resolve()
    ready = ledger / "provider-ready.json"
    token = secrets.token_urlsafe(32)
    token_file = ledger / f".provider-auth-{secrets.token_hex(16)}"
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(token, encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "serve", "--ledger", str(ledger), "--ready", str(ready), "--token-file", str(token_file)],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if ready.is_file():
            try:
                value = _read_json(ready, {})
                if value.get("pid") == process.pid and isinstance(value.get("port"), int):
                    client = ProviderClient(value["port"], token, process)
                    client._ledger_path = ledger / "provider-ledger.json"  # noqa: SLF001 - verifier-owned state
                    token_file.unlink(missing_ok=True)
                    break
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        if process.poll() is not None:
            token_file.unlink(missing_ok=True)
            stdout, stderr = process.communicate()
            raise RuntimeError(f"provider exited before ready: {stdout} {stderr}")
        time.sleep(0.01)
    else:
        process.kill()
        token_file.unlink(missing_ok=True)
        raise TimeoutError("provider did not become ready")
    try:
        yield client
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


def verify_effect_evidence(
    *, provider: ProviderClient, idempotency_key: str, expected_fingerprint: str,
    candidate_observation: dict[str, Any], candidate_decision: str,
    observation_event_sequence: tuple[str, ...], tool_class: str = "check-before-retry",
    provider_observation: dict[str, Any] | None = None,
    retry_receipt: dict[str, Any] | None = None,
    candidate_root: Path | None = None,
) -> dict[str, Any]:
    """Derive an effect verdict from the provider ledger, not host assertions."""
    if candidate_root is not None:
        try:
            provider._ledger_path.resolve().relative_to(candidate_root.resolve())  # noqa: SLF001
        except ValueError:
            pass
        else:
            raise ValueError("provider ledger is inside the candidate workspace")
    if observation_event_sequence[:2] != ("reobservation-request", "provider-observation"):
        raise ValueError("re-observation must occur before the candidate result or retry")
    actual = provider_observation or provider.observe(idempotency_key)
    provider_events = [
        json.loads(line)
        for line in (provider._ledger_path.parent / "provider-events.jsonl").read_text(encoding="utf-8").splitlines()  # noqa: SLF001
        if line
    ]
    if not any(event.get("event_id") == actual.get("observation_event_id") and event.get("kind") == "observe" for event in provider_events):
        raise ValueError("provider observation is absent from the durable provider ledger")
    state = actual["state"]
    resource_fingerprint = actual["request_fingerprint"]
    expected = candidate_observation_from_provider(actual)
    if expected["idempotency_key"] != idempotency_key:
        raise ValueError("provider observation idempotency key does not match requested observation")
    if candidate_observation != expected:
        if state != "present" and candidate_observation.get("state") == "present":
            raise ValueError("candidate claims a durable provider ledger resource that does not exist")
        raise ValueError("candidate observation does not match durable provider ledger")
    matching = state == "present" and resource_fingerprint == expected_fingerprint
    expected_decision = (
        "skip" if matching else "escalate" if state in {"present", "unknown"}
        else "retry" if tool_class in {"safe-to-retry", "proven-idempotent"} else "escalate"
    )
    if candidate_decision != expected_decision:
        raise ValueError("candidate reconciliation decision does not match provider state")
    ledger = provider.ledger()
    resources = ledger.get("resources", {})
    if any(value.get("create_count") != 1 for value in resources.values()):
        raise ValueError("provider ledger records duplicate creation")
    if expected_decision == "retry":
        if observation_event_sequence[2:] != ("candidate-result", "post-result-provider-dispatch"):
            raise ValueError("retry requires a recorded post-result provider dispatch")
        receipts = ledger.get("receipts", {})
        if not retry_receipt or receipts.get(retry_receipt.get("receipt_id")) != retry_receipt:
            raise ValueError("retry receipt is absent from the durable provider ledger")
        observation_index = next(
            index for index, event in enumerate(provider_events)
            if event.get("event_id") == actual["observation_event_id"]
        )
        receipt_index = next(
            (
                index for index, event in enumerate(provider_events)
                if event.get("kind") == "receipt_issued"
                and event.get("receipt_id") == retry_receipt["receipt_id"]
            ),
            -1,
        )
        if receipt_index <= observation_index:
            raise ValueError("retry receipt predates the real provider observation")
    elif retry_receipt is not None:
        raise ValueError("non-retry resolution must not claim a post-recovery receipt")
    return {"provider_observation": actual, "decision": expected_decision, "ledger": ledger}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    serve = subparsers.add_parser("serve")
    serve.add_argument("--ledger", type=Path, required=True)
    serve.add_argument("--ready", type=Path, required=True)
    serve.add_argument("--token-file", type=Path, required=True)
    args = parser.parse_args(argv)
    _serve(args.ledger, args.ready, args.token_file.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
