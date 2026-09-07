"""Public verifier for the sealed Phase 5 archive effect holdout."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("archive_gateway.py")


def call(workspace: Path, provider: Path, command: str) -> dict:
    output = subprocess.check_output(
        [sys.executable, str(SCRIPT), "--workspace", str(workspace), "--provider", str(provider), command],
        text=True,
    )
    return json.loads(output)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        workspace, provider = root / "workspace", root / "provider"
        assert call(workspace, provider, "init")["effect_id"] == "archive-job"
        assert call(workspace, provider, "create")["status"] == "committed"
        assert call(workspace, provider, "observe")["status"] == "present"
        assert call(workspace, provider, "close-skip")["decision"] == "skip"
        assert call(workspace, provider, "verify")["verified"] is True


if __name__ == "__main__":
    main()
    print("archive gateway verified")
