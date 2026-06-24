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
