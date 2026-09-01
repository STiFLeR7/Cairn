# Benchmarks

`recoverybench.py` is the locked Phase 1 repository crash/restart control. It is intentionally
not an agent framework: a terminal repository action must make exactly one verified work-unit of
progress before Cairn takes a durable checkpoint. A crash is injected only after that checkpoint;
a fresh Python process invokes existing RGR and the harness-owned verifier judges the completed
repository.

Run the deterministic matrix (four fixtures, every non-terminal fault boundary, ten repeats):

```powershell
python benchmarks/recoverybench.py --control --repeats 10 --output results/phase-1/recoverybench-a.jsonl
python benchmarks/recoverybench.py --control --repeats 10 --output results/phase-1/recoverybench-b.jsonl
python benchmarks/recoverybench.py --compare results/phase-1/recoverybench-a.jsonl results/phase-1/recoverybench-b.jsonl
```

The JSONL schema is `recoverybench.v0.1`. Every scored row includes fixture/version, fault step,
the durable `failure_fired` receipt and clean checkpoint, baseline and recovery digests, verifier
output, and task-success/artifact-equivalence/no-regression/recovery-tax values. Rows without a
fired receipt, checkpoint ID/digest/provenance, or verifier result are invalid and excluded from
the deterministic summary.

Phase 1 has no external effects. The `effect_duplicates: 0` record field denotes this scoped
absence; it is not an exactly-once claim.

The same reference loop has a live-model adapter, but it deliberately refuses a real provider
unless an available Docker executor can isolate the action. That executor mounts only the fixture
repository, disables networking, receives no host environment, and drops Linux capabilities. The
built-in `fake` transport is only for offline process-boundary validation.

Once Docker is available, run the live matrix with explicit model and budget declarations. Two
models and two repeats yield 44 candidate fired pairs (11 fault cells × 2 models × 2 repeats):

```powershell
python benchmarks/recoverybench.py --live openrouter:stealth/Ox-alpha --live PROVIDER:MODEL --repeats 2 --max-calls 12 --max-chars 100000 --max-tokens 4096 --output results/phase-1/live.jsonl
```

The command writes the paired records to `live.jsonl`, worker transcripts under its sibling
`runs/` directory, and prints the gate-ready live-evidence summary. It fails before calling a real
model unless Docker is available.
