"""M5 — the pre-registered v1.0-gate live study (AP-0055/AP-0056).

Per model: calibration (uncrashed), then the chain study with a torn `send-report` effect at each
crash step, B0 vs B3, `repeats` times. Records go to results/m5/<label>.json; `compute_gate` applies
the pre-registered gate. Live use is gated by `m5_preregister.verify()` in `main`.

Every calibration run and every study repeat is one checkpointed unit, appended to
`<label>.partial.jsonl` as it finishes. `PAUSE_AFTER_CONSECUTIVE_ERRORS` errored units in a row (a
usage cap, an outage) pause the run with the checkpoint kept; `--resume` reuses the finished units,
re-attempts errored or missing ones, and reports every earlier error in `resumed_errors` (spec §8).
"""

from __future__ import annotations

try:
    import _bootstrap  # noqa: F401
except ImportError:
    pass

import dataclasses
import datetime
import glob
import json
import os
import sys

from benchmarks.m5_preregister import PREREG, preregistration_digest
from benchmarks.scenarios import build_live_transport, live_chain_effect_scenario, live_chain_scenario
from cairn.eval.baselines import ColdRestart, RGR
from cairn.eval.calibration import calibration_summary, run_calibration
from cairn.eval.metrics import RecoveryReport
from cairn.eval.runner import (
    RepeatedRun, aggregate_repeated, run_repeated, verdict_c1, verdict_c1_capability, verdict_c3_live,
    verdict_v1_gate,
)

BASELINES = 2  # B0, B3
PAUSE_AFTER_CONSECUTIVE_ERRORS = 2
NOTES = ("transport errors include CLI is_error responses (e.g. structured-output exhaustion); "
         "counted as loss in both calibration and study")


class StudyPaused(RuntimeError):
    """Consecutive units errored (e.g. a usage cap): the checkpoint is kept for `--resume`."""


class BudgetExhausted(StudyPaused):
    """The protocol's max_calls is spent across all sessions; a resume cannot grant a fresh budget."""


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


def _preregistration() -> tuple:
    digest = preregistration_digest()
    if digest is None:
        return None, None
    with open(PREREG, encoding="utf-8") as f:
        return digest, json.load(f).get("git_commit")


def _read_partial(path: str, stamp: str) -> tuple[dict, list[dict]]:
    """Read a checkpoint; a torn last line (hard kill) is moved to `<path>.torn-<UTC>`, never deleted.

    The unit on a torn line is simply missing and re-attempted; the file is left ending in a newline so
    later appends start on a fresh line.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()
    complete, _, tail = text.rpartition("\n")
    torn = False
    if tail.strip():
        try:
            json.loads(tail)
            complete = text
        except ValueError:
            torn = True
    lines = [json.loads(line) for line in complete.splitlines() if line.strip()]
    if not lines or "preregistration_sha256" not in lines[0]:
        raise ValueError(f"{path} has no readable header line (torn or empty); cannot resume it")
    if torn:
        with open(f"{path}.torn-{stamp}", "w", encoding="utf-8") as f:
            f.write(tail)
        with open(path, "w", encoding="utf-8") as f:
            f.write(complete + "\n")
    elif not text.endswith("\n"):
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n")
    return lines[0], lines[1:]


def _sum_stats(sessions: list[dict]) -> dict:
    if not any(sessions):
        return {}
    return {k: sum(s.get(k, 0) for s in sessions) for k in ("calls", "errors")}


def _key(unit: dict) -> tuple:
    return ("cal", unit["i"]) if unit["unit"] == "cal" else ("study", unit["k"], unit["i"])


def run_m5_model(label: str, protocol: dict, *, transport=None, out_dir: str = "results/m5",
                 force: bool = False, resume: bool = False) -> dict:
    cfg = protocol["models"][label]
    record_path = os.path.join(out_dir, f"{label}.json")
    partial_path = os.path.join(out_dir, f"{label}.partial.jsonl")
    if force and resume:
        raise ValueError("force and resume are mutually exclusive")
    if os.path.exists(record_path) and not force:
        raise FileExistsError(f"{record_path} exists; pass force=True (--force) to supersede it")
    resuming = resume and os.path.exists(partial_path)
    if os.path.exists(partial_path) and not (force or resume):
        raise FileExistsError(f"{partial_path} exists (an interrupted run); pass resume=True (--resume) "
                              "to continue it or force=True (--force) to supersede it")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest, commit = _preregistration()
    n, steps, repeats = protocol["n"], list(protocol["steps"]), protocol["repeats"]
    planned = len(steps) * BASELINES * repeats
    latest: dict[tuple, dict] = {}
    resumed_errors: list[str] = []
    prior_sessions: list[dict] = []  # call_stats of earlier sessions, from the last checkpoint line
    if resuming:
        header, units = _read_partial(partial_path, stamp)
        if header.get("preregistration_sha256") != digest:
            raise ValueError(f"{partial_path} was written under preregistration "
                             f"{header.get('preregistration_sha256')}, not the current {digest}")
        for unit in units:
            if unit["status"] == "error":
                resumed_errors.append(unit["error"])
            latest[_key(unit)] = unit
            prior_sessions = unit.get("call_stats_sessions", prior_sessions)
    else:
        _supersede(record_path, stamp)
        _supersede(partial_path, stamp)
        os.makedirs(out_dir, exist_ok=True)
        with open(partial_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"preregistration_sha256": digest, "label": label}) + "\n")
    max_calls = protocol.get("max_calls")
    prior_calls = _sum_stats(prior_sessions).get("calls", 0)
    if transport is None:
        os.makedirs("benchmarks/transcripts", exist_ok=True)
        if not resuming:
            _supersede(f"benchmarks/transcripts/m5-{label}.jsonl", stamp)
        transport = build_live_transport(  # the call ceiling is cumulative over resumed sessions
            cfg["model"], provider=cfg["provider"],
            max_calls=None if max_calls is None else max(0, max_calls - prior_calls),
            transcript_path=f"benchmarks/transcripts/m5-{label}.jsonl", transcript_append=resuming,
            reasoning_effort=cfg.get("reasoning_effort"),
        )
    streak = [0]

    def sessions() -> list[dict]:
        return prior_sessions + [dict(getattr(transport, "call_stats", None) or {})]

    def check_budget() -> None:
        used = _sum_stats(sessions()).get("calls", 0)
        if max_calls is not None and used >= max_calls:
            raise BudgetExhausted(f"cumulative calls {used} reached the protocol max_calls {max_calls} "
                                  f"across {len(sessions())} session(s); checkpoint kept at {partial_path}, "
                                  "but resuming cannot grant a fresh budget")

    def checkpoint(unit: dict) -> None:
        unit["call_stats"] = _sum_stats(sessions())
        unit["call_stats_sessions"] = sessions()
        with open(partial_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(unit, default=str) + "\n")
        latest[_key(unit)] = unit
        streak[0] = streak[0] + 1 if unit["status"] == "error" else 0
        if streak[0] >= PAUSE_AFTER_CONSECUTIVE_ERRORS:
            raise StudyPaused(f"{streak[0]} consecutive units errored (last: {unit['error']}); "
                              f"checkpoint kept at {partial_path}; rerun with --resume")

    def done(key: tuple) -> bool:
        return latest.get(key, {}).get("status") == "ok"

    record = {"label": label, "provider": cfg["provider"], "model": cfg["model"],
              "planned_cells": planned, "preregistration_sha256": digest, "preregistration_commit": commit,
              "resumed": resuming, "notes": NOTES}
    cal_runs = protocol["calibration_runs"]
    for i in range(cal_runs):
        if done(("cal", i)):
            continue
        check_budget()
        cal = run_calibration(live_chain_scenario(n, transport), runs=1)
        ok = cal["completed"] == 1
        checkpoint({"unit": "cal", "i": i, "status": "ok" if ok else "error",
                    "success": bool(cal["successes"]) if ok else None,
                    "error": None if ok else cal["errors"][0]})
    # eligibility is decided only now, once every calibration unit is done
    cal_units = [latest[("cal", i)] for i in range(cal_runs)]
    record["calibration"] = calibration_summary(
        cal_runs, [u["success"] for u in cal_units if u["status"] == "ok"],
        [u["error"] for u in cal_units if u["status"] == "error"])
    record["study_run"] = bool(record["calibration"]["eligible"])
    reports, errors, skipped = [], [], 0
    if record["study_run"]:
        for k in steps:
            for i in range(repeats):
                if done(("study", k, i)):
                    continue
                check_budget()
                errs: list[str] = []
                run = run_repeated(
                    live_chain_effect_scenario(n, k, transport), steps=[k],
                    baselines=[ColdRestart(), RGR()], repeats=1,
                    on_error=lambda _r, exc: errs.append(f"k={k} repeat {i}: {type(exc).__name__}: {exc}"[:300]),
                )
                if run.errored:  # an errored repeat is lost, not skipped
                    checkpoint({"unit": "study", "k": k, "i": i, "status": "error", "reports": [],
                                "skipped": 0, "error": errs[0]})
                else:
                    checkpoint({"unit": "study", "k": k, "i": i, "status": "ok",
                                "reports": [dataclasses.asdict(r) for r in run.reports],
                                "skipped": run.skipped, "error": None})
        for k in steps:
            for i in range(repeats):
                unit = latest[("study", k, i)]
                if unit["status"] == "ok":
                    reports.extend(RecoveryReport(**d) for d in unit["reports"])
                    skipped += unit["skipped"]
                else:
                    errors.append(unit["error"])
    errored_repeats = len(errors)
    record["lost_cells"] = errored_repeats * BASELINES if record["study_run"] else planned
    record["skipped_cells"] = skipped
    record["fired_cells"] = len(reports)
    record["errors"] = errors[:20]
    record["error_count"] = len(errors)
    record["resumed_errors"] = {"count": len(resumed_errors), "errors": resumed_errors}
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
    record["call_stats"] = _sum_stats(sessions())  # cumulative over every resumed session
    record["call_stats_sessions"] = sessions() if any(sessions()) else []
    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, default=str)
    os.replace(partial_path, os.path.join(out_dir, f"{label}.partial.done-{stamp}.jsonl"))
    return record


def compute_gate(out_dir: str = "results/m5", prereg_digest: str | None = None) -> dict:
    per_model = {}
    for label in ("claude", "codex"):
        path = os.path.join(out_dir, f"{label}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                per_model[label] = json.load(f)
    gate = verdict_v1_gate(per_model)
    if prereg_digest is not None:
        unbound = [f"{label}.json ({rec.get('preregistration_sha256')})" for label, rec in per_model.items()
                   if rec.get("preregistration_sha256") != prereg_digest]
        if unbound:
            gate = {"decision": "INCONCLUSIVE",
                    "reason": f"records not bound to the current preregistration {prereg_digest}: {unbound}"}
    gate["models"] = {label: {k: rec.get(k) for k in ("accounting", "skipped_cells", "call_stats", "observed_models")}
                      for label, rec in per_model.items()}
    gate["superseded_files"] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(out_dir, "*.superseded-*")))
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
        print(json.dumps(compute_gate(prereg_digest=preregistration_digest()), indent=2))
        return 0
    label = argv[0] if argv else ""
    if label not in protocol["models"]:
        print(f"usage: python benchmarks/m5_study.py <{'|'.join(protocol['models'])}> [--force] [--resume]"
              " | gate")
        return 2
    try:
        rec = run_m5_model(label, protocol, force="--force" in argv[1:], resume="--resume" in argv[1:])
    except StudyPaused as exc:
        print(f"paused: {exc}")
        return 3
    print(json.dumps({k: rec[k] for k in ("label", "eligible", "fired_cells", "lost_cells", "c1", "c3")},
                     indent=2, default=str))
    return 0 if rec["eligible"] else 1  # ineligible at calibration: make the operator notice


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
