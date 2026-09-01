from __future__ import annotations
from typing import List, Dict


def priority_band(priority: int) -> int:
    """Return the scheduling band for a given priority."""
    ...


def retry_schedule(attempt: int) -> List[int]:
    """Return the list of delays before each attempt."""
    ...


def dispatchable_ids(tasks: Dict[str, str]) -> List[str]:
    """Return sorted ids whose state is ready or queued."""
    ...


def partition_batches(ids: List[str], batch_size: int) -> List[List[str]]:
    """Partition ids into batches of at most batch_size."""
    ...
