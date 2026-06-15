"""A trivial baseline Task: create a file with exact content. Verified by an oracle."""

from __future__ import annotations

import os

from ..task import Task


class CreateFileTask(Task):
    def __init__(self, filename: str, content: str) -> None:
        self.filename = filename
        self.content = content

    @property
    def goal(self) -> str:
        return f"Create a file named {self.filename!r} containing exactly: {self.content!r}"

    def is_complete(self, workspace: str) -> bool:
        path = os.path.join(workspace, self.filename)
        if not os.path.isfile(path):
            return False
        with open(path, "r", encoding="utf-8") as f:
            return f.read() == self.content
