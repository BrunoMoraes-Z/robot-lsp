from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .models import LspRange


class DiagnosticSeverity(IntEnum):
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


@dataclass
class LspDiagnostic:
    range: LspRange
    severity: DiagnosticSeverity
    message: str
    source: str = "robot-lsp"
    code: str | None = None

    def to_lsp(self) -> dict:
        payload = {
            "range": {
                "start": {
                    "line": self.range.start.line,
                    "character": self.range.start.character,
                },
                "end": {
                    "line": self.range.end.line,
                    "character": self.range.end.character,
                },
            },
            "severity": int(self.severity),
            "message": self.message,
            "source": self.source,
        }
        if self.code is not None:
            payload["code"] = self.code
        return payload
