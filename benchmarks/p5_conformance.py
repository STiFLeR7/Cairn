"""Host-neutral semantic evidence checks for the Phase 5 portability proof."""

from __future__ import annotations


CELLS = ("U", "R", "R_NEG", "C", "C_NEG", "EFFECT")


def conformance_verdict(runs: list[dict]) -> dict:
    """Judge already-observed host facts; this function never drives a host."""
    by_cell = {run.get("cell"): run for run in runs}
    failures = [f"missing required cell: {cell}" for cell in CELLS if cell not in by_cell]
    for cell in CELLS:
        run = by_cell.get(cell)
        if not run:
            continue
        required = ("host", "freeze", "checkpoint", "crash", "recovery", "compaction", "effect", "final")
        failures.extend(f"{cell}: missing {key}" for key in required if key not in run)
        if not all(key in run for key in required):
            continue
        if not all(run["host"].get(key) for key in ("name", "version", "model")):
            failures.append(f"{cell}: host identity is incomplete")
        if not all(run["freeze"].get(key) for key in ("workload_sha256", "verifier_sha256")):
            failures.append(f"{cell}: workload or verifier is not sealed")
        if not all(run["checkpoint"].get(key) for key in ("identity", "artifact_sha256")):
            failures.append(f"{cell}: checkpoint identity or artifact digest is absent")
        if cell in {"R_NEG", "C_NEG"}:
            if not run["final"].get("correct_termination") or run["final"].get("unauthorized_action") is not False:
                failures.append(f"{cell}: negative control did not safely terminate")
        elif not run["final"].get("verified") or not run["final"].get("artifact_equivalent"):
            failures.append(f"{cell}: final verification or artifact equivalence failed")
        if cell in {"R", "R_NEG", "EFFECT"}:
            if run["recovery"].get("identity") == run["crash"].get("identity"):
                failures.append(f"{cell}: recovery identity is not fresh")
            if run["recovery"].get("transcript_available") is not False:
                failures.append(f"{cell}: recovery transcript boundary is not fresh")
        if cell in {"R", "R_NEG", "C", "C_NEG"} and run["recovery"].get("first_operation") != "reobserve":
            failures.append(f"{cell}: first recovery operation is not reobserve")
        if cell in {"C", "C_NEG"} and not (run["compaction"].get("native") and run["compaction"].get("event_observed")):
            failures.append(f"{cell}: native compaction was not directly observed")
        if cell == "EFFECT" and run["effect"].get("first_operation") != "observe":
            failures.append("EFFECT: provider observation did not precede resolution")
    return {"schema_version": "cairn.p5-conformance.v0", "passed": not failures, "failures": failures}
