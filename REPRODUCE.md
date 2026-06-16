# Reproducing Cairn's results

Everything here is **deterministic** — a scripted mock model, no wall-clock or network — so a clean run
regenerates the same numbers every time (see [ADR-0009](docs/adr/ADR-0009-evaluation-framework.md)).

## Environment

- **Python 3.12+** (developed on 3.12.4). No third-party runtime dependencies; tests use `pytest`.
- No build step — the package is imported from `src/` via `pyproject.toml`'s `pythonpath`.

```bash
git clone https://github.com/STiFLeR7/Cairn.git
cd Cairn
python -m pip install --upgrade pytest    # the only dependency, for the test suite
```

## One-command paths

With `make` (Linux/macOS, or Windows via Git Bash / WSL):

```bash
make test     # run the full test suite
make demo     # run the crash-then-recover demonstration
make bench     # run all three benchmarks
make all      # test + demo + bench
```

Without `make` (any platform), run the same commands directly:

```bash
python -m pytest -q                       # test
python examples/recovery_demo.py          # demo
python benchmarks/recovery_matrix.py      # bench: baseline × failure-step matrix + effect-safety
python benchmarks/ablation_study.py       # bench: Continuation-State ablation
python benchmarks/cross_version_resume.py # bench: cross-version resume
```

## Expected outputs

### Tests
```
42 passed
```

### Recovery demo (`examples/recovery_demo.py`)
```
[crash] injected failure after step 1
[state] files=['step0.txt', 'step1.txt'] outbox_lines=1
[resume] success=True recovery_tax=1 (cold restart would be 3)
[resume] effect resolutions=[('send-1', 'skip')]
[done] files=['step0.txt', 'step1.txt', 'step2.txt'] outbox_lines=1 (effect happened exactly once)
```

### Recovery matrix (`benchmarks/recovery_matrix.py`)
RGR (B3) vs cold restart (B0), failures at k=1..4:

| baseline | no_regression | recovery_tax |
|---|---|---|
| B0 | 0.00 | 5.00 |
| B3 | 1.00 | 1.50 |

Effect-safety (torn effect at k=2): **B3 duplicates=0 (gate PASS)**, **B0 duplicates=1 (gate FAIL)**.
Verdicts printed: **C1 SUPPORTED**, **C3 SUPPORTED**.

### Ablation (`benchmarks/ablation_study.py`)
Dropping `plan` is a fidelity cliff (recovery_tax 2 → 5, no-regression 1.0 → 0.0); dropping
`decisions` / `ruled_out` / `world_digest` / `verification` causes no degradation (slack). Verdict: **C5**.

### Cross-version (`benchmarks/cross_version_resume.py`)
```
checkpointed under: 'model-A'
resumed under:      'model-B'
resume success:     True
```

## Scope

These are **reference-harness** results (deterministic scripted mock), establishing that the mechanisms
behave as designed and are reproducible — **not** a live-LLM study. See `PAPER.md` §9 and the
[claims registry](docs/research/claims-registry.md) for the honest scope of each claim.
