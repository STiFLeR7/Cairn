# Queue Scheduling Policy

## Functions

### priority_band(priority: int) -> int
Return band 0 for priority >= 80, 1 for 50 <= priority < 80, 2 for 20 <= priority < 50, 3 for 0 <= priority < 20, and 4 for priority < 0. Domain: integers.

### retry_schedule(attempt: int) -> list[int]
Return [] for attempt 0. For attempt k >= 1, return [2**0, 2**1, ..., 2**(k-1)]. Domain: non-negative integers.

### dispatchable_ids(tasks: dict[str, str]) -> list[str]
Return the lexicographically sorted IDs whose value is exactly ready or queued. Domain: dicts with string keys and values in {ready, queued, running, failed, done}.

### partition_batches(ids: list[str], batch_size: int) -> list[list[str]]
Split ids into ordered sublists of at most batch_size. The final batch may be shorter. Domain: lists of strings and positive integer batch_size. Empty ids returns [].

Any input outside a documented domain is not scored.

## Acceptance Cases

```json
[{"function":"priority_band","args":[90],"expected":0},{"function":"priority_band","args":[50],"expected":1},{"function":"priority_band","args":[20],"expected":2},{"function":"priority_band","args":[0],"expected":3},{"function":"priority_band","args":[-5],"expected":4},{"function":"retry_schedule","args":[0],"expected":[]},{"function":"retry_schedule","args":[3],"expected":[1,2,4]},{"function":"dispatchable_ids","args":[{"t1":"ready","t2":"running","t3":"queued","t4":"done"}],"expected":["t1","t3"]},{"function":"partition_batches","args":[["a","b","c","d","e"],2],"expected":[["a","b"],["c","d"],["e"]]}]
```
