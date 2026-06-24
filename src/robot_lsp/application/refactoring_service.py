from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from robot_lsp.domain.models import LspPosition, LspRange, RobotSuite

from .document_store import Document, DocumentStore
from .parse_service import ParseService
from .workspace import WorkspaceIndex


@dataclass(frozen=True)
class RenameTarget:
    name: str
    kind: str
    range: LspRange


class RefactoringService:
    def __init__(
        self,
        document_store: DocumentStore,
        parse_service: ParseService,
        workspace_index: WorkspaceIndex | None = None,
    ) -> None:
        self._document_store = document_store
        self._parse_service = parse_service
        self._workspace_index = workspace_index

    def prepare_rename(self, uri: str, position: LspPosition) -> dict[str, Any] | None:
        target = self._target_at(uri, position)
        if target is None:
            return None
        return {"range": _range_to_lsp(target.range), "placeholder": target.name}

    def rename(self, uri: str, position: LspPosition, new_name: str) -> dict[str, Any] | None:
        target = self._target_at(uri, position)
        if target is None or not new_name:
            return None

        changes: dict[str, list[dict[str, Any]]] = {}
        for edit_uri, text in self._candidate_documents(uri).items():
            edits = [
                {"range": _range_to_lsp(range_), "newText": new_name}
                for range_ in _find_symbol_ranges(text, target.name)
            ]
            if edits:
                changes[edit_uri] = edits
        return {"changes": changes}

    def _candidate_documents(self, uri: str) -> dict[str, str]:
        candidates: dict[str, str] = {}
        document = self._document_store.get(uri)
        if document is not None:
            candidates[uri] = document.text
        if self._workspace_index is not None:
            for entry_uri, entry in self._workspace_index.entries.items():
                if entry_uri in candidates:
                    continue
                candidates[entry_uri] = entry.path.read_text(encoding="utf-8")
        return candidates

    def _target_at(self, uri: str, position: LspPosition) -> RenameTarget | None:
        document = self._document_store.get(uri)
        if document is None:
            return None
        result = self._parse_service.parse_document(document)
        if result.suite is None:
            return None
        return _target_at(document, result.suite, position)


def _target_at(document: Document, suite: RobotSuite, position: LspPosition) -> RenameTarget | None:
    lines = _logical_lines(document.text)
    if position.line < 0 or position.line >= len(lines):
        return None

    line_text = lines[position.line]
    candidates: list[tuple[str, str]] = []
    candidates.extend((variable.name, "variable") for variable in suite.variables)
    candidates.extend((keyword.name, "keyword") for keyword in suite.keywords)
    candidates.extend((test_case.name, "test_case") for test_case in suite.test_cases)
    candidates.sort(key=lambda item: len(item[0]), reverse=True)
    for name, kind in candidates:
        range_ = _symbol_range_on_line(line_text, position.line, name, position)
        if range_ is not None:
            return RenameTarget(name=name, kind=kind, range=range_)
    return None


def _symbol_range_on_line(line_text: str, line: int, symbol: str, position: LspPosition) -> LspRange | None:
    start = 0
    while True:
        index = line_text.find(symbol, start)
        if index == -1:
            return None
        start_character = _utf16_len(line_text[:index])
        end_character = start_character + _utf16_len(symbol)
        if start_character <= position.character <= end_character:
            return LspRange(LspPosition(line, start_character), LspPosition(line, end_character))
        start = index + max(1, len(symbol))


def _find_symbol_ranges(text: str, symbol: str) -> list[LspRange]:
    ranges: list[LspRange] = []
    for line_number, line_text in enumerate(_logical_lines(text)):
        start = 0
        while True:
            index = line_text.find(symbol, start)
            if index == -1:
                break
            start_character = _utf16_len(line_text[:index])
            end_character = start_character + _utf16_len(symbol)
            ranges.append(LspRange(LspPosition(line_number, start_character), LspPosition(line_number, end_character)))
            start = index + max(1, len(symbol))
    return ranges


def _range_to_lsp(range_: LspRange) -> dict[str, Any]:
    return {
        "start": {"line": range_.start.line, "character": range_.start.character},
        "end": {"line": range_.end.line, "character": range_.end.character},
    }


def _logical_lines(text: str) -> list[str]:
    lines = text.splitlines()
    if text.endswith(("\n", "\r")):
        lines.append("")
    return lines or [""]


def _utf16_len(text: str) -> int:
    return sum(1 if ord(ch) < 0x10000 else 2 for ch in text)
