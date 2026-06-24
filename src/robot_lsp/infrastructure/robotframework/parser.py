from __future__ import annotations

import tempfile
from pathlib import Path

from robot.api.parsing import get_model

from robot_lsp.domain.features import FeatureSet
from robot_lsp.domain.models import ParseResult

from .adapter import RobotFrameworkASTAdapter
from .version import RobotFrameworkVersionDetector


class RobotFrameworkParser:
    def __init__(self, features: FeatureSet | None = None) -> None:
        self._features = features or RobotFrameworkVersionDetector().detect()
        self._adapter = RobotFrameworkASTAdapter(self._features)

    def parse_file(self, path: Path) -> ParseResult:
        model = get_model(str(path))
        return self._adapter.to_parse_result(model, source=str(path))

    def parse_text(self, text: str, *, source_name: str = "document.robot") -> ParseResult:
        with tempfile.TemporaryDirectory(prefix="robot-lsp-") as tmp_dir:
            path = Path(tmp_dir) / source_name
            path.write_text(text, encoding="utf-8")
            return self.parse_file(path)
