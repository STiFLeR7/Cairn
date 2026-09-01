"""Audit clean-room P2.4 task descriptions before they are sealed."""

from __future__ import annotations

import json
import re


EXPOSED_V12_FUNCTIONS = {"normalize_key", "clamp", "contains_token", "render_tags"}
_REQUIRED_KEYS = {"task_id", "title", "functions", "starter_project_py", "public_readme", "acceptance_cases"}


def _literal(value) -> bool:
    if value is None or isinstance(value, (bool, int, float, str)):
        return True
    if isinstance(value, list):
        return all(_literal(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _literal(item) for key, item in value.items())
    return False


def _public_cases(readme: str) -> list[dict] | None:
    match = re.search(r"```json\s*(\[.*?\])\s*```", readme, flags=re.DOTALL)
    if match is None:
        return None
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, list) else None


def audit_author_output(payload: dict) -> dict:
    """Accept only a fully public, literal, disjoint four-function task."""
    reasons: list[str] = []
    if not _REQUIRED_KEYS <= payload.keys():
        reasons.append("missing_required_field")
        return {"admitted": False, "reasons": reasons}

    functions = payload["functions"]
    if not isinstance(functions, list) or len(functions) != 4:
        reasons.append("not_four_functions")
        functions = []
    names = [item.get("name") for item in functions if isinstance(item, dict)]
    if len(names) != 4 or any(not isinstance(name, str) or not name for name in names):
        reasons.append("invalid_function_name")
    elif len(set(names)) != 4:
        reasons.append("duplicate_function_name")
    elif EXPOSED_V12_FUNCTIONS & set(names):
        reasons.append("exposed_v12_function_name")
    if any(not isinstance(item.get("domain"), str) or not item["domain"].strip() for item in functions if isinstance(item, dict)):
        reasons.append("missing_input_domain")

    try:
        compile(payload["starter_project_py"], "project.py", "exec")
    except (SyntaxError, TypeError):
        reasons.append("starter_project_not_parseable")

    cases = payload["acceptance_cases"]
    if not isinstance(cases, list) or not cases:
        reasons.append("missing_acceptance_cases")
        cases = []
    elif any(
        not isinstance(case, dict)
        or set(case) != {"function", "args", "expected"}
        or case["function"] not in names
        or not isinstance(case["args"], list)
        or not _literal(case["args"])
        or not _literal(case["expected"])
        for case in cases
    ):
        reasons.append("nonliteral_or_invalid_acceptance_case")

    public_cases = _public_cases(payload["public_readme"])
    if public_cases is None:
        reasons.append("missing_public_acceptance_cases")
    elif {
        json.dumps(case, sort_keys=True, separators=(",", ":")) for case in public_cases
    } != {
        json.dumps(case, sort_keys=True, separators=(",", ":")) for case in cases
    }:
        reasons.append("unpublished_acceptance_case")
    if "not scored" not in payload["public_readme"].lower():
        reasons.append("missing_unscored_domain_statement")

    return {"admitted": not reasons, "reasons": sorted(set(reasons))}
