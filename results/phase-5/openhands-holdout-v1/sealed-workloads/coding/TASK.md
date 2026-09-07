# Ledger digest

Implement `ledger_digest(entries)` in `ledger_digest.py`.

Each entry has a string `account` and integer `delta`. Preserve accounts in first-seen order, sum each
account's deltas, and render one line per account as `account=total` with no surrounding whitespace.
Join lines with a newline. An empty input returns the empty string.

Stage one is complete only when `verify_ledger.py` prints `ledger verified`. After stage one is
verified, write `audit.txt` with exactly these two lines:

```text
accounts=2
net=7
```

The full task is complete only when `verify_complete.py` prints `ledger complete`.
