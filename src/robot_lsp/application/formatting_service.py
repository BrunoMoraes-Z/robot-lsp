from __future__ import annotations

import re
from typing import Any

from robot_lsp.domain.models import LspPosition, LspRange

from .document_store import DocumentStore


class FormattingService:
    def __init__(self, document_store: DocumentStore) -> None:
        self._document_store = document_store

    def format_document(self, uri: str, options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        document = self._document_store.get(uri)
        if document is None:
            return []
        formatted = format_robot_text(document.text)
        if formatted == document.text:
            return []
        return [{"range": _full_document_range(document.text), "newText": formatted}]

    def format_range(
        self,
        uri: str,
        range_: LspRange,
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        document = self._document_store.get(uri)
        if document is None:
            return []
        lines = document.text.splitlines(keepends=True)
        if range_.start.line < 0 or range_.start.line >= len(lines):
            return []
        end_line = min(range_.end.line, len(lines) - 1)
        selected = "".join(lines[range_.start.line : end_line + 1])
        formatted = format_robot_text(selected)
        if formatted == selected:
            return []
        edit_range = LspRange(
            start=LspPosition(range_.start.line, 0),
            end=LspPosition(end_line, _utf16_len(lines[end_line].rstrip("\r\n"))),
        )
        return [{"range": _range_to_lsp(edit_range), "newText": formatted.rstrip("\r\n")}]


def format_robot_text(text: str) -> str:
    has_final_newline = text.endswith(("\n", "\r"))
    lines = text.splitlines()
    formatted = [_format_line(line) for line in lines]
    result = "\n".join(formatted)
    if has_final_newline:
        result += "\n"
    return result


def _format_line(line: str) -> str:
    stripped_right = line.rstrip()
    if not stripped_right or stripped_right.lstrip().startswith("#"):
        return stripped_right
    leading = stripped_right[: len(stripped_right) - len(stripped_right.lstrip(" "))]
    content = stripped_right[len(leading) :]
    if content.startswith("***"):
        return content.strip()
    cells = [cell.strip() for cell in re.split(r" {2,}|\t+", content) if cell.strip()]
    if len(cells) <= 1:
        return leading + content.strip()
    return leading + "    ".join(cells)


def _full_document_range(text: str) -> dict[str, Any]:
    lines = text.splitlines(keepends=True)
    if not lines:
        return _range_to_lsp(LspRange(LspPosition(0, 0), LspPosition(0, 0)))
    end_line = len(lines) - 1
    last_line = lines[-1]
    if last_line.endswith(("\n", "\r")):
        return _range_to_lsp(LspRange(LspPosition(0, 0), LspPosition(len(lines), 0)))
    return _range_to_lsp(
        LspRange(
            LspPosition(0, 0),
            LspPosition(end_line, _utf16_len(last_line.rstrip("\r\n"))),
        )
    )


def _range_to_lsp(range_: LspRange) -> dict[str, Any]:
    return {
        "start": {"line": range_.start.line, "character": range_.start.character},
        "end": {"line": range_.end.line, "character": range_.end.character},
    }


def _utf16_len(text: str) -> int:
    return sum(1 if ord(ch) < 0x10000 else 2 for ch in text)
