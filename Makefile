# Cairn — reproducibility task runner. See REPRODUCE.md.
# Deterministic: a scripted mock model, no network/wall-clock (ADR-0009).
#
# PY is intentionally NOT named PYTHON: on some Windows setups a PYTHON env var holds a
# backslashed path (C:\...\python.exe) that GNU make cannot exec directly. Override with
# `make PY=python3` if needed.

PY ?= python

.PHONY: all test demo bench bench-matrix bench-ablation bench-xversion bench-live clean

all: test demo bench

test:
	$(PY) -m pytest -q

demo:
	$(PY) examples/recovery_demo.py

bench: bench-matrix bench-ablation bench-xversion

bench-matrix:
	$(PY) benchmarks/recovery_matrix.py

bench-ablation:
	$(PY) benchmarks/ablation_study.py

bench-xversion:
	$(PY) benchmarks/cross_version_resume.py

# Live-pipeline study (Milestone M1) — runs OFFLINE on a deterministic fake transport
# (no key, no spend). The paid live run is gated; see REPRODUCE.md.
bench-live:
	$(PY) benchmarks/live_study.py

clean:
	$(PY) -c "import shutil,glob; [shutil.rmtree(p,ignore_errors=True) for p in glob.glob('**/__pycache__',recursive=True)]"
