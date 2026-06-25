from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from robot_lsp.domain.models import LspPosition, RobotSuite
from robot_lsp.domain.positions import position_to_utf16_offset

from .document_store import Document, DocumentStore
from .parse_service import ParseService
from .workspace import WorkspaceIndex


class CompletionItemKind(IntEnum):
    TEXT = 1
    METHOD = 2
    FUNCTION = 3
    VARIABLE = 6
    MODULE = 9
    KEYWORD = 14
    SNIPPET = 15


class InsertTextFormat(IntEnum):
    PLAIN_TEXT = 1
    SNIPPET = 2


@dataclass(frozen=True)
class CompletionItem:
    label: str
    kind: CompletionItemKind
    detail: str | None = None
    documentation: str | None = None
    insert_text: str | None = None
    insert_text_format: InsertTextFormat | None = None
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
        if self.insert_text is not None:
            payload["insertText"] = self.insert_text
        if self.insert_text_format is not None:
            payload["insertTextFormat"] = int(self.insert_text_format)
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
    SECTION_SNIPPETS = {
        "*** Settings ***": "*** Settings ***\n$0",
        "*** Variables ***": "*** Variables ***\n$0",
        "*** Test Cases ***": "*** Test Cases ***\n${1:Test Case}\n    $0",
        "*** Keywords ***": "*** Keywords ***\n${1:Keyword Name}\n    $0",
    }
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
    VARIABLE_TYPE_ITEMS = [
        "str",
        "int",
        "float",
        "bool",
        "list",
        "dict",
        "tuple",
        "set",
        "bytes",
        "datetime",
        "date",
        "timedelta",
        "Decimal",
        "Path",
        "Secret",
        "Any",
    ]

    def __init__(
        self,
        document_store: DocumentStore,
        parse_service: ParseService,
        workspace_index: WorkspaceIndex | None = None,
    ) -> None:
        self._document_store = document_store
        self._parse_service = parse_service
        self._workspace_index = workspace_index

    def compute_completion(
        self,
        uri: str,
        position: LspPosition,
        *,
        trigger_character: str | None = None,
        snippets_enabled: bool = True,
    ) -> CompletionList | None:
        document = self._document_store.get(uri)
        if document is None:
            return None

        result = self._parse_service.parse_document(document)
        context = self._context(document, result.suite, position, trigger_character)
        if context is None:
            return CompletionList(items=[])

        if self._is_variable_type_context(context):
            return CompletionList(self._variable_type_items())
        if self._is_variable_context(context):
            return CompletionList(self._variable_items(context))
        if self._is_section_context(context):
            return CompletionList(self._section_items(snippets_enabled=snippets_enabled))
        if context.section == "settings":
            return CompletionList(self._setting_items())
        if context.section in {"test cases", "keywords"}:
            return CompletionList(self._keyword_items(context))

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

    def _is_variable_type_context(self, context: CompletionContext) -> bool:
        last_open = max(context.line_prefix.rfind(f"{prefix}{{") for prefix in self.VARIABLE_TRIGGERS)
        if last_open == -1 or context.line_prefix.rfind("}") > last_open:
            return False
        return ":" in context.line_prefix[last_open:]

    def _section_items(self, *, snippets_enabled: bool) -> list[CompletionItem]:
        if not snippets_enabled:
            return [
                CompletionItem(
                    label=item,
                    kind=CompletionItemKind.TEXT,
                    detail="Robot Framework section",
                )
                for item in self.SECTION_ITEMS
            ]
        return [
            CompletionItem(
                label=item,
                kind=CompletionItemKind.SNIPPET,
                detail="Robot Framework section",
                insert_text=self.SECTION_SNIPPETS[item],
                insert_text_format=InsertTextFormat.SNIPPET,
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

    def _keyword_items(self, context: CompletionContext) -> list[CompletionItem]:
        if context.suite is None:
            return []
        items = [
            CompletionItem(
                label=keyword.name,
                kind=CompletionItemKind.FUNCTION,
                detail="Local keyword",
                documentation=keyword.doc or None,
            )
            for keyword in context.suite.keywords
        ]
        if self._workspace_index is not None and context.document.path is not None:
            items.extend(
                CompletionItem(
                    label=location.name,
                    kind=CompletionItemKind.FUNCTION,
                    detail="Imported keyword",
                )
                for location in self._workspace_index.imported_keyword_locations(
                    context.document.path,
                    context.suite,
                )
                if location.name not in {item.label for item in items}
            )
        return items

    def _variable_type_items(self) -> list[CompletionItem]:
        return [
            CompletionItem(
                label=item,
                kind=CompletionItemKind.TEXT,
                detail="Robot Framework variable type",
            )
            for item in self.VARIABLE_TYPE_ITEMS
        ]

    def _variable_items(self, context: CompletionContext) -> list[CompletionItem]:
        if context.suite is None:
            return []
        items = [
            CompletionItem(
                label=variable.name,
                kind=CompletionItemKind.VARIABLE,
                detail=f"Local {variable.kind} variable",
                documentation=str(variable.value) if variable.value is not None else None,
            )
            for variable in context.suite.variables
        ]
        items.extend(
            CompletionItem(
                label=variable.name,
                kind=CompletionItemKind.VARIABLE,
                detail=f"Scoped {variable.kind} variable",
                documentation=str(variable.value) if variable.value is not None else None,
            )
            for variable in _scoped_variables(context)
            if variable.name not in {item.label for item in items}
        )
        if self._workspace_index is not None and context.document.path is not None:
            items.extend(
                CompletionItem(
                    label=location.name,
                    kind=CompletionItemKind.VARIABLE,
                    detail="Imported variable",
                )
                for location in self._workspace_index.imported_variable_locations(
                    context.document.path,
                    context.suite,
                )
                if location.name not in {item.label for item in items}
            )
        return items


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


def _scoped_variables(context: CompletionContext):
    if context.suite is None:
        return []
    variables = []
    for test_case in context.suite.test_cases:
        if test_case.range.start.line <= context.position.line <= test_case.range.end.line:
            variables.extend(test_case.variables)
    for keyword in context.suite.keywords:
        if keyword.range.start.line <= context.position.line <= keyword.range.end.line:
            variables.extend(keyword.variables)
    return variables
