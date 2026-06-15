"""Append-only effect ledger (taxonomy layer 2).

Implements the write-ahead discipline's storage: INTENT and COMPLETE records, both
append-only with monotonic sequence numbers (boundary-contract invariants I1, I3).
Resume-time reconciliation consumes it via `cairn.harness.effects` (Phase 4).
"""

from __future__ import annotations

import json
import os
import time

INTENT = "INTENT"
COMPLETE = "COMPLETE"


class EffectLedger:
    def __init__(self, path: str, ledger_id: str = "default") -> None:
        self.path = path
        self.ledger_id = ledger_id
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        if not os.path.exists(path):
            open(path, "w", encoding="utf-8").close()

    def _count(self) -> int:
        n = 0
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    n += 1
        return n

    def current_offset(self) -> int:
        return self._count()

    def _append(self, rec: dict) -> int:
        seq = self._count()
        rec["seq"] = seq
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        return seq

    def append_effect(
        self, intent: str, idempotency_key: str, tool_class: str = "never-retry", step: int = 0
    ) -> int:
        return self._append(
            {
                "type": INTENT,
                "action": intent,
                "idempotency_key": idempotency_key,
                "tool_class": tool_class,
                "step": step,
                "timestamp": time.time(),
            }
        )

    def complete_effect(self, idempotency_key: str) -> None:
        self._append(
            {
                "type": COMPLETE,
                "action": "",
                "idempotency_key": idempotency_key,
                "tool_class": "",
                "step": 0,
                "timestamp": time.time(),
            }
        )

    def list_effects_since(self, offset: int) -> list[dict]:
        out: list[dict] = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("seq", -1) >= offset:
                    out.append(rec)
        return out
