from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from robot_lsp.domain.models import LspPosition, LspRange, RobotKeyword, RobotSuite
from robot_lsp.domain.positions import position_to_utf16_offset

from .document_store import Document, DocumentStore
from .parse_service import ParseService


@dataclass(frozen=True)
class MarkupContent:
    kind: str
    value: str

    def to_lsp(self) -> dict[str, str]:
        return {"kind": self.kind, "value": self.value}


@dataclass(frozen=True)
class Hover:
    contents: MarkupContent
    range: LspRange | None = None

    def to_lsp(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"contents": self.contents.to_lsp()}
        if self.range is not None:
            payload["range"] = {
                "start": {
                    "line": self.range.start.line,
                    "character": self.range.start.character,
                },
                "end": {
                    "line": self.range.end.line,
                    "character": self.range.end.character,
                },
            }
        return payload


@dataclass(frozen=True)
class HoverContext:
    uri: str
    position: LspPosition
    document: Document
    suite: RobotSuite | None
    line_text: str


class HoverService:
    def __init__(self, document_store: DocumentStore, parse_service: ParseService) -> None:
        self._document_store = document_store
        self._parse_service = parse_service

    def compute_hover(self, uri: str, position: LspPosition) -> Hover | None:
        document = self._document_store.get(uri)
        if document is None:
            return None

        result = self._parse_service.parse_document(document)
        context = self._context(document, result.suite, position)
        if context is None or context.suite is None:
            return None

        return (
            self._variable_hover(context)
            or self._import_hover(context)
            or self._keyword_hover(context)
        )

    def _context(
        self,
        document: Document,
        suite: RobotSuite | None,
        position: LspPosition,
    ) -> HoverContext | None:
        lines = _logical_lines(document.text)
        if position.line < 0 or position.line >= len(lines):
            return None
        return HoverContext(
            uri=document.uri,
            position=position,
            document=document,
            suite=suite,
            line_text=lines[position.line],
        )

    def _variable_hover(self, context: HoverContext) -> Hover | None:
        assert context.suite is not None
        for variable in context.suite.variables:
            match_range = _symbol_range_on_line(
                context.line_text,
                context.position.line,
                variable.name,
                context.position,
            )
            if match_range is None:
                continue
            return Hover(
                contents=MarkupContent(
                    kind="markdown",
                    value=(
                        f"**{variable.name}**\n\n"
                        f"```text\nType: {variable.kind}\nValue: {variable.value}\n```"
                    ),
                ),
                range=match_range,
            )
        return None

    def _import_hover(self, context: HoverContext) -> Hover | None:
        assert context.suite is not None
        for import_ in context.suite.imports:
            match_range = _symbol_range_on_line(
                context.line_text,
                context.position.line,
                import_.name,
                context.position,
            )
            if match_range is None:
                continue
            import_type = import_.type.title()
            alias = f" as {import_.alias}" if import_.alias else ""
            args = f"\nArgs: {' '.join(import_.args)}" if import_.args else ""
            return Hover(
                contents=MarkupContent(
                    kind="markdown",
                    value=f"**{import_type}**: `{import_.name}`{alias}{args}",
                ),
                range=match_range,
            )
        return None

    def _keyword_hover(self, context: HoverContext) -> Hover | None:
        assert context.suite is not None
        for keyword in context.suite.keywords:
            match_range = _symbol_range_on_line(
                context.line_text,
                context.position.line,
                keyword.name,
                context.position,
            )
            if match_range is None:
                continue
            return Hover(
                contents=MarkupContent(
                    kind="markdown",
                    value=_keyword_markdown(keyword),
                ),
                range=match_range,
            )
        return None


def _keyword_markdown(keyword: RobotKeyword) -> str:
    args = ", ".join(arg.name if arg.default is None else f"{arg.name}={arg.default}" for arg in keyword.args)
    signature = f"{keyword.name}({args})" if args else f"{keyword.name}()"
    if keyword.doc:
        return f"**{signature}**\n\n{keyword.doc}"
    return f"**{signature}**"


def _symbol_range_on_line(
    line_text: str,
    line: int,
    symbol: str,
    position: LspPosition,
) -> LspRange | None:
    start = 0
    while True:
        index = line_text.find(symbol, start)
        if index == -1:
            return None
        start_character = _utf16_len(line_text[:index])
        end_character = start_character + _utf16_len(symbol)
        if start_character <= position.character <= end_character:
            return LspRange(
                start=LspPosition(line=line, character=start_character),
                end=LspPosition(line=line, character=end_character),
            )
        start = index + len(symbol)


def _logical_lines(text: str) -> list[str]:
    lines = text.splitlines()
    if text.endswith(("\n", "\r")):
        lines.append("")
    return lines or [""]


def _utf16_len(text: str) -> int:
    return sum(1 if ord(ch) < 0x10000 else 2 for ch in text)
