from __future__ import annotations

from robot.api.parsing import ModelVisitor

from robot_lsp.domain.models import RobotDiagnostic


class ErrorCollectingVisitor(ModelVisitor):
    def __init__(self, adapter) -> None:
        self._adapter = adapter
        self.errors: list[RobotDiagnostic] = []

    def visit_Error(self, node) -> None:  # noqa: N802 - Robot Framework visitor API
        self.errors.append(self._adapter.to_diagnostic(node))
