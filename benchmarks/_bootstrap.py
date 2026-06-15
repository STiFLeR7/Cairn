"""Path bootstrap so benchmark scripts run as `python benchmarks/<script>.py`.

Adds the repo root (for the `benchmarks` package) and `src/` (for `cairn`) to sys.path.
"""

import os
import sys

_HERE = os.path.dirname(__file__)
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
for p in (_ROOT, os.path.join(_ROOT, "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

# Emit UTF-8 regardless of the console code page (Windows cp1252 cannot encode → / – etc.).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass
