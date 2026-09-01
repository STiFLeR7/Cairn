# Bugfix fixture

Repair `project.py` in three independently testable changes: make `add(a, b)` return a sum,
make `multiply(a, b)` return a product, then add `VERSION = "1.0"`. Keep each edit small enough
to verify independently. The Phase 1 final verifier is harness-owned, so the worker only receives
this repository and its terminal action surface.
