"""M5 — the pre-registered v1.0-gate live study (AP-0055/AP-0056).

Per model: calibration (uncrashed), then the chain study with a torn `send-report` effect at each
crash step, B0 vs B3, `repeats` times. Records go to results/m5/<label>.json; `compute_gate` applies
the pre-registered gate. Live use is gated by `m5_preregister.verify()` in `main`.
"""

from __future__ import annotations

try:
    import _bootstrap  # noqa: F401
except ImportError:
    pass

import datetime
import json
import os
import sys

from benchmarks.scenarios import build_live_transport, live_chain_effect_scenario, live_chain_scenario
from cairn.eval.baselines import ColdRestart, RGR
from cairn.eval.calibration import run_calibration
from cairn.eval.runner import (
    RepeatedRun, aggregate_repeated, run_repeated, verdict_c1, verdict_c1_capability, verdict_c3_live,
    verdict_v1_gate,
)

BASELINES = 2  # B0, B3


def load_protocol(path: str = "results/m5/protocol.json") -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _jsonable(stats: dict) -> dict:
    out = {}
    for name, row in stats.items():
        out[name] = {k: (vars(v) if hasattr(v, "mean") else v) for k, v in row.items()}
    return out


def _supersede(path: str, stamp: str) -> None:
    if os.path.exists(path):
        os.replace(path, f"{path}.superseded-{stamp}")  # never delete


def run_m5_model(label: str, protocol: dict, *, transport=None, out_dir: str = "results/m5",
                 force: bool = False) -> dict:
    cfg = protocol["models"][label]
    record_path = os.path.join(out_dir, f"{label}.json")
    if os.path.exists(record_path) and not force:
        raise FileExistsError(f"{record_path} exists; pass force=True (--force) to supersede it")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    n, steps, repeats = protocol["n"], list(protocol["steps"]), protocol["repeats"]
    planned = len(steps) * BASELINES * repeats
    _supersede(record_path, stamp)
    if transport is None:
        os.makedirs("benchmarks/transcripts", exist_ok=True)
        _supersede(f"benchmarks/transcripts/m5-{label}.jsonl", stamp)
        transport = build_live_transport(
            cfg["model"], provider=cfg["provider"], max_calls=protocol["max_calls"],
            transcript_path=f"benchmarks/transcripts/m5-{label}.jsonl",
        )
    record = {"label": label, "provider": cfg["provider"], "model": cfg["model"],
              "planned_cells": planned}
    record["calibration"] = run_calibration(live_chain_scenario(n, transport), runs=protocol["calibration_runs"])
    record["study_run"] = bool(record["calibration"]["eligible"])
    reports, errors, skipped, errored_repeats = [], [], 0, 0
    cur = [0]
    if record["study_run"]:
        for k in steps:
            skip_by_repeat: list[int] = []
            bad: set[int] = set()

            def _err(i, exc, k=k, bad=bad):
                bad.add(i)
                errors.append(f"k={k} repeat {i}: {type(exc).__name__}: {exc}"[:300])

            run = run_repeated(
                live_chain_effect_scenario(n, k, transport), steps=[k],
                baselines=[ColdRestart(), RGR()], repeats=repeats,
                before_repeat=lambda i: cur.__setitem__(0, i),
                on_skip=lambda _k, _name, sb=skip_by_repeat: sb.append(cur[0]),
                on_error=_err,
            )
            reports.extend(run.reports)
            skipped += sum(1 for i in skip_by_repeat if i not in bad)  # an errored repeat is lost, not skipped
            errored_repeats += run.errored
    record["lost_cells"] = errored_repeats * BASELINES if record["study_run"] else planned
    record["skipped_cells"] = skipped
    record["fired_cells"] = len(reports)
    record["errors"] = errors[:20]
    record["fired_by_baseline"] = {b: sum(1 for r in reports if r.baseline == b) for b in ("B0", "B3")}
    record["accounting"] = {
        "planned": planned, "fired": len(reports), "skipped": skipped, "lost": record["lost_cells"],
        "balanced": len(reports) + skipped + record["lost_cells"] == planned,
    }
    view = RepeatedRun(reports=reports, fired=len(reports), skipped=skipped, repeats=repeats,
                       steps=steps, baselines=["B0", "B3"], errored=errored_repeats)
    stats = aggregate_repeated(view) if reports else {}
    record["stats"] = _jsonable(stats)
    cal_rate = record["calibration"]["calibration_rate"]
    record["c1"] = verdict_c1_capability(stats, cal_rate)
    record["c1_strict"] = {k: v for k, v in verdict_c1(stats).items() if k in ("claim", "supported", "reason")} \
        if stats else {"claim": "C1", "supported": False, "reason": "no fired cells"}
    record["c3"] = verdict_c3_live(stats)
    record["eligible"] = record["calibration"]["eligible"]
    record["observed_models"] = sorted(getattr(transport, "observed_models", None) or [])
    os.makedirs(out_dir, exist_ok=True)
    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, default=str)
    return record


def compute_gate(out_dir: str = "results/m5") -> dict:
    per_model = {}
    for label in ("claude", "codex"):
        path = os.path.join(out_dir, f"{label}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                per_model[label] = json.load(f)
    gate = verdict_v1_gate(per_model)
    with open(os.path.join(out_dir, "gate-verdict.json"), "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2)
    return gate


def main(argv: list[str]) -> int:
    from benchmarks.m5_preregister import verify

    problems = verify()
    if problems:
        print("refusing to run: pre-registration mismatch:\n  " + "\n  ".join(problems))
        return 2
    protocol = load_protocol()
    if argv and argv[0] == "gate":
        print(json.dumps(compute_gate(), indent=2))
        return 0
    label = argv[0] if argv else ""
    if label not in protocol["models"]:
        print(f"usage: python benchmarks/m5_study.py <{'|'.join(protocol['models'])}|gate>")
        return 2
    rec = run_m5_model(label, protocol, force="--force" in argv[1:])
    print(json.dumps({k: rec[k] for k in ("label", "eligible", "fired_cells", "lost_cells", "c1", "c3")},
                     indent=2, default=str))
    return 0 if rec["eligible"] else 1  # ineligible at calibration: make the operator notice


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
