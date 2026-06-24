from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from robot_lsp.domain.models import LspPosition, LspRange, RobotSuite

from .document_store import Document, DocumentStore
from .parse_service import ParseService
from .workspace import WorkspaceIndex


class SymbolKind(IntEnum):
    FILE = 1
    MODULE = 2
    METHOD = 6
    FUNCTION = 12
    VARIABLE = 13


@dataclass(frozen=True)
class SymbolMatch:
    name: str
    kind: str
    definition_uri: str
    definition_range: LspRange
    reference_range: LspRange


class NavigationService:
    def __init__(
        self,
        document_store: DocumentStore,
        parse_service: ParseService,
        workspace_index: WorkspaceIndex | None = None,
    ) -> None:
        self._document_store = document_store
        self._parse_service = parse_service
        self._workspace_index = workspace_index

    def definition(self, uri: str, position: LspPosition) -> list[dict[str, Any]]:
        document, suite = self._document_and_suite(uri)
        if document is None or suite is None:
            return []

        match = self._symbol_at(document, suite, position)
        if match is None:
            return []
        return [_location(match.definition_uri, match.definition_range)]

    def references(
        self,
        uri: str,
        position: LspPosition,
        *,
        include_declaration: bool = True,
    ) -> list[dict[str, Any]]:
        document, suite = self._document_and_suite(uri)
        if document is None or suite is None:
            return []

        match = self._symbol_at(document, suite, position)
        if match is None:
            return []

        locations = []
        for reference_range in _find_symbol_ranges(document.text, match.name):
            if not include_declaration and _range_inside(reference_range, match.definition_range):
                continue
            locations.append(_location(uri, reference_range))
        return locations

    def document_symbols(self, uri: str) -> list[dict[str, Any]]:
        document, suite = self._document_and_suite(uri)
        if document is None or suite is None:
            return []

        symbols: list[dict[str, Any]] = []
        for import_ in suite.imports:
            symbols.append(_document_symbol(import_.name, SymbolKind.MODULE, import_.range, f"{import_.type} import"))
        for variable in suite.variables:
            symbols.append(_document_symbol(variable.name, SymbolKind.VARIABLE, variable.range, variable.kind))
        for test_case in suite.test_cases:
            symbols.append(_document_symbol(test_case.name, SymbolKind.METHOD, test_case.range, "test case"))
        for keyword in suite.keywords:
            symbols.append(_document_symbol(keyword.name, SymbolKind.FUNCTION, keyword.range, "keyword"))
        return symbols

    def folding_ranges(self, uri: str) -> list[dict[str, Any]]:
        document, suite = self._document_and_suite(uri)
        if document is None:
            return []

        ranges = _section_folding_ranges(document.text)
        if suite is not None:
            for test_case in suite.test_cases:
                _append_folding_range(ranges, test_case.range)
            for keyword in suite.keywords:
                _append_folding_range(ranges, keyword.range)
        return ranges

    def selection_ranges(self, uri: str, positions: list[LspPosition]) -> list[dict[str, Any]]:
        document, suite = self._document_and_suite(uri)
        if document is None:
            return []

        result = []
        lines = _logical_lines(document.text)
        for position in positions:
            line_range = _line_range(lines, position.line)
            match = self._symbol_at(document, suite, position) if suite is not None else None
            symbol_range = match.reference_range if match is not None else None
            if symbol_range is None:
                result.append({"range": _range_to_lsp(line_range)})
            else:
                result.append({"range": _range_to_lsp(symbol_range), "parent": {"range": _range_to_lsp(line_range)}})
        return result

    def _document_and_suite(self, uri: str) -> tuple[Document | None, RobotSuite | None]:
        document = self._document_store.get(uri)
        if document is None:
            return None, None
        result = self._parse_service.parse_document(document)
        return document, result.suite

    def _symbol_at(self, document: Document, suite: RobotSuite, position: LspPosition) -> SymbolMatch | None:
        lines = _logical_lines(document.text)
        if position.line < 0 or position.line >= len(lines):
            return None
        line_text = lines[position.line]

        candidates: list[tuple[str, str, str, LspRange]] = []
        candidates.extend((variable.name, "variable", document.uri, variable.range) for variable in suite.variables)
        candidates.extend((import_.name, "import", document.uri, import_.range) for import_ in suite.imports)
        candidates.extend((keyword.name, "keyword", document.uri, keyword.range) for keyword in suite.keywords)
        candidates.extend((test_case.name, "test_case", document.uri, test_case.range) for test_case in suite.test_cases)
        if self._workspace_index is not None and document.path is not None:
            candidates.extend(
                (location.name, "imported_keyword", location.uri, location.range)
                for location in self._workspace_index.imported_keyword_locations(document.path, suite)
            )
            candidates.extend(
                (location.name, "imported_variable", location.uri, location.range)
                for location in self._workspace_index.imported_variable_locations(document.path, suite)
            )
        candidates.sort(key=lambda item: len(item[0]), reverse=True)

        for name, kind, definition_uri, definition_range in candidates:
            reference_range = _symbol_range_on_line(line_text, position.line, name, position)
            if reference_range is not None:
                return SymbolMatch(name, kind, definition_uri, definition_range, reference_range)
        return None


def _document_symbol(name: str, kind: SymbolKind, range: LspRange, detail: str) -> dict[str, Any]:
    return {
        "name": name,
        "kind": int(kind),
        "detail": detail,
        "range": _range_to_lsp(range),
        "selectionRange": _range_to_lsp(range),
    }


def _location(uri: str, range: LspRange) -> dict[str, Any]:
    return {"uri": uri, "range": _range_to_lsp(range)}


def _range_to_lsp(range: LspRange) -> dict[str, Any]:
    return {
        "start": {"line": range.start.line, "character": range.start.character},
        "end": {"line": range.end.line, "character": range.end.character},
    }


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


def _section_folding_ranges(text: str) -> list[dict[str, Any]]:
    lines = _logical_lines(text)
    headers = [index for index, line in enumerate(lines) if line.strip().startswith("***") and line.strip().endswith("***")]
    ranges: list[dict[str, Any]] = []
    for i, start_line in enumerate(headers):
        end_line = (headers[i + 1] - 1) if i + 1 < len(headers) else len(lines) - 1
        if end_line > start_line:
            ranges.append({"startLine": start_line, "endLine": end_line, "kind": "region"})
    return ranges


def _append_folding_range(ranges: list[dict[str, Any]], range: LspRange) -> None:
    if range.end.line > range.start.line:
        item = {"startLine": range.start.line, "endLine": range.end.line, "kind": "region"}
        if item not in ranges:
            ranges.append(item)


def _line_range(lines: list[str], line: int) -> LspRange:
    if line < 0 or line >= len(lines):
        return LspRange(LspPosition(0, 0), LspPosition(0, 0))
    return LspRange(LspPosition(line, 0), LspPosition(line, _utf16_len(lines[line])))


def _range_inside(inner: LspRange, outer: LspRange) -> bool:
    if inner.start.line < outer.start.line or inner.end.line > outer.end.line:
        return False
    if inner.start.line == outer.start.line and inner.start.character < outer.start.character:
        return False
    if inner.end.line == outer.end.line and inner.end.character > outer.end.character:
        return False
    return True


def _logical_lines(text: str) -> list[str]:
    lines = text.splitlines()
    if text.endswith(("\n", "\r")):
        lines.append("")
    return lines or [""]


def _utf16_len(text: str) -> int:
    return sum(1 if ord(ch) < 0x10000 else 2 for ch in text)
