"""Make the repo root importable so tests can use `benchmarks.scenarios` (concrete wiring).

`src/` is already on the path via pyproject's `pythonpath`; this adds the repo root for the
`benchmarks` package, keeping concrete tasks out of the library (ADR-0007 / ADR-0009).
"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
