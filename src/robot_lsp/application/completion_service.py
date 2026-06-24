from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from robot_lsp.domain.models import LspPosition, RobotSuite
from robot_lsp.domain.positions import position_to_utf16_offset

from .document_store import Document, DocumentStore
from .parse_service import ParseService


class CompletionItemKind(IntEnum):
    TEXT = 1
    METHOD = 2
    FUNCTION = 3
    VARIABLE = 6
    MODULE = 9
    KEYWORD = 14
    SNIPPET = 15


@dataclass(frozen=True)
class CompletionItem:
    label: str
    kind: CompletionItemKind
    detail: str | None = None
    documentation: str | None = None
    data: Any = None

    def to_lsp(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "label": self.label,
            "kind": int(self.kind),
        }
        if self.detail is not None:
            payload["detail"] = self.detail
        if self.documentation is not None:
            payload["documentation"] = self.documentation
        if self.data is not None:
            payload["data"] = self.data
        return payload


@dataclass(frozen=True)
class CompletionList:
    items: list[CompletionItem]
    is_incomplete: bool = False

    def to_lsp(self) -> dict[str, Any]:
        return {
            "isIncomplete": self.is_incomplete,
            "items": [item.to_lsp() for item in self.items],
        }


@dataclass(frozen=True)
class CompletionContext:
    uri: str
    position: LspPosition
    document: Document
    suite: RobotSuite | None
    line_text: str
    line_prefix: str
    section: str | None
    trigger_character: str | None


class CompletionService:
    SECTION_ITEMS = [
        "*** Settings ***",
        "*** Variables ***",
        "*** Test Cases ***",
        "*** Keywords ***",
    ]
    SETTING_ITEMS = [
        "Library",
        "Resource",
        "Variables",
        "Documentation",
        "Metadata",
        "Suite Setup",
        "Suite Teardown",
        "Test Setup",
        "Test Teardown",
        "Test Tags",
        "Test Template",
        "Test Timeout",
        "Force Tags",
        "Default Tags",
    ]
    VARIABLE_TRIGGERS = {"$", "@", "&", "%"}

    def __init__(self, document_store: DocumentStore, parse_service: ParseService) -> None:
        self._document_store = document_store
        self._parse_service = parse_service

    def compute_completion(
        self,
        uri: str,
        position: LspPosition,
        *,
        trigger_character: str | None = None,
    ) -> CompletionList | None:
        document = self._document_store.get(uri)
        if document is None:
            return None

        result = self._parse_service.parse_document(document)
        context = self._context(document, result.suite, position, trigger_character)
        if context is None:
            return CompletionList(items=[])

        if self._is_variable_context(context):
            return CompletionList(self._variable_items(context.suite))
        if self._is_section_context(context):
            return CompletionList(self._section_items())
        if context.section == "settings":
            return CompletionList(self._setting_items())
        if context.section in {"test cases", "keywords"}:
            return CompletionList(self._keyword_items(context.suite))

        return CompletionList(items=[])

    def _context(
        self,
        document: Document,
        suite: RobotSuite | None,
        position: LspPosition,
        trigger_character: str | None,
    ) -> CompletionContext | None:
        lines = _logical_lines(document.text)
        if position.line < 0 or position.line >= max(1, len(lines)):
            return None
        line_text = lines[position.line] if lines else ""
        line_prefix = _prefix_for_utf16_character(line_text, position.character)
        return CompletionContext(
            uri=document.uri,
            position=position,
            document=document,
            suite=suite,
            line_text=line_text,
            line_prefix=line_prefix,
            section=_current_section(lines, position.line),
            trigger_character=trigger_character,
        )

    def _is_section_context(self, context: CompletionContext) -> bool:
        stripped = context.line_prefix.strip()
        return (stripped == "" and context.section is None) or stripped.startswith("***")

    def _is_variable_context(self, context: CompletionContext) -> bool:
        if context.trigger_character in self.VARIABLE_TRIGGERS:
            return True
        return any(context.line_prefix.endswith(trigger) for trigger in self.VARIABLE_TRIGGERS)

    def _section_items(self) -> list[CompletionItem]:
        return [
            CompletionItem(
                label=item,
                kind=CompletionItemKind.SNIPPET,
                detail="Robot Framework section",
            )
            for item in self.SECTION_ITEMS
        ]

    def _setting_items(self) -> list[CompletionItem]:
        return [
            CompletionItem(
                label=item,
                kind=CompletionItemKind.KEYWORD,
                detail="Robot Framework setting",
            )
            for item in self.SETTING_ITEMS
        ]

    def _keyword_items(self, suite: RobotSuite | None) -> list[CompletionItem]:
        if suite is None:
            return []
        return [
            CompletionItem(
                label=keyword.name,
                kind=CompletionItemKind.FUNCTION,
                detail="Local keyword",
                documentation=keyword.doc or None,
            )
            for keyword in suite.keywords
        ]

    def _variable_items(self, suite: RobotSuite | None) -> list[CompletionItem]:
        if suite is None:
            return []
        return [
            CompletionItem(
                label=variable.name,
                kind=CompletionItemKind.VARIABLE,
                detail=f"Local {variable.kind} variable",
                documentation=str(variable.value) if variable.value is not None else None,
            )
            for variable in suite.variables
        ]


def _prefix_for_utf16_character(line_text: str, character: int) -> str:
    offset = position_to_utf16_offset(line_text, 0, character)
    if offset is None:
        return line_text
    return line_text[:offset]


def _logical_lines(text: str) -> list[str]:
    lines = text.splitlines()
    if text.endswith(("\n", "\r")):
        lines.append("")
    return lines or [""]


def _current_section(lines: list[str], line: int) -> str | None:
    section = None
    for candidate in lines[: line + 1]:
        normalized = candidate.strip().lower()
        if normalized == "*** settings ***":
            section = "settings"
        elif normalized == "*** variables ***":
            section = "variables"
        elif normalized == "*** test cases ***":
            section = "test cases"
        elif normalized == "*** keywords ***":
            section = "keywords"
    return section
