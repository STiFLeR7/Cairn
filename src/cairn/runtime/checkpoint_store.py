"""Atomic checkpoint store (boundary-contract invariant I2).

Each checkpoint is written to a temp file, fsync'd, then atomically renamed into
place. load_latest only ever considers fully-renamed `ckpt_N.json` files, so a
partially written checkpoint (a leftover `.tmp`) is never returned.
"""

from __future__ import annotations

import json
import os
from typing import Optional, Tuple

from ..state import ContinuationState


class CheckpointStore:
    def __init__(self, ckpt_dir: str) -> None:
        self.dir = ckpt_dir
        os.makedirs(ckpt_dir, exist_ok=True)
        self._n = self._highest() + 1

    def _highest(self) -> int:
        hi = -1
        for name in os.listdir(self.dir):
            if name.startswith("ckpt_") and name.endswith(".json"):
                try:
                    hi = max(hi, int(name[len("ckpt_") : -len(".json")]))
                except ValueError:
                    pass
        return hi

    def checkpoint(self, state: ContinuationState, snap_id: str, effect_offset: int) -> str:
        n = self._n
        self._n += 1
        ckpt_id = f"ckpt_{n}"
        payload = {
            "state": state.to_dict(),
            "snap_id": snap_id,
            "effect_offset": effect_offset,
        }
        final = os.path.join(self.dir, ckpt_id + ".json")
        tmp = final + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, final)  # atomic
        return ckpt_id

    def load_latest(self) -> Optional[Tuple[ContinuationState, str, int]]:
        hi = self._highest()
        if hi < 0:
            return None
        path = os.path.join(self.dir, f"ckpt_{hi}.json")
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        state = ContinuationState.from_dict(payload["state"])
        return (state, payload["snap_id"], int(payload["effect_offset"]))
