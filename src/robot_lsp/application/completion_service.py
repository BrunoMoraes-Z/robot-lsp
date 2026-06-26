from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum
from functools import lru_cache
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
    FIELD = 5
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
    text_edit: dict[str, Any] | None = None
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
        if self.text_edit is not None:
            payload["textEdit"] = self.text_edit
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
        "*** Tasks ***",
        "*** Keywords ***",
    ]
    SECTION_SNIPPETS = {
        "*** Settings ***": "*** Settings ***\n$0",
        "*** Variables ***": "*** Variables ***\n$0",
        "*** Test Cases ***": "*** Test Cases ***\n${1:Test Case}\n    $0",
        "*** Tasks ***": "*** Tasks ***\n${1:Task Name}\n    $0",
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
    TEST_CASE_SETTING_ITEMS = [
        "Documentation",
        "Tags",
        "Setup",
        "Teardown",
        "Template",
        "Timeout",
    ]
    KEYWORD_SETTING_ITEMS = [
        "Documentation",
        "Arguments",
        "Setup",
        "Teardown",
        "Timeout",
        "Tags",
        "Return",
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
    RESERVED_TAGS = {
        "robot:skip": {
            "contexts": {"test cases", "tasks"},
            "documentation": "Skips the test/task before execution. Valid in tests and tasks.",
        },
        "robot:exclude": {
            "contexts": {"test cases", "tasks"},
            "documentation": "Excludes the test/task completely from execution and output. Valid in tests and tasks.",
        },
        "robot:exit": {
            "contexts": {"test cases", "tasks"},
            "documentation": "Reserved tag added automatically when execution is stopped. Valid in tests and tasks.",
        },
        "robot:skip-on-failure": {
            "contexts": {"test cases", "tasks"},
            "documentation": "Converts a failure into SKIP. Valid in tests and tasks.",
        },
        "robot:exit-on-failure": {
            "contexts": {"test cases", "tasks"},
            "documentation": "Stops the whole execution if this test/task fails. Valid in tests and tasks.",
        },
        "robot:continue-on-failure": {
            "contexts": {"test cases", "tasks", "keywords"},
            "documentation": "Continues execution after failures in the immediate scope. Valid in tests, tasks and keywords.",
        },
        "robot:recursive-continue-on-failure": {
            "contexts": {"test cases", "tasks", "keywords"},
            "documentation": "Continues execution after failures recursively in called keywords. Valid in tests, tasks and keywords.",
        },
        "robot:stop-on-failure": {
            "contexts": {"test cases", "tasks", "keywords"},
            "documentation": "Disables continue-on-failure behavior in the immediate scope. Valid in tests, tasks and keywords.",
        },
        "robot:recursive-stop-on-failure": {
            "contexts": {"test cases", "tasks", "keywords"},
            "documentation": "Disables recursive continue-on-failure behavior. Valid in tests, tasks and keywords.",
        },
        "robot:private": {
            "contexts": {"keywords"},
            "documentation": "Marks a user keyword private and warns when it is used outside its defining file. Valid in keywords.",
        },
        "robot:no-dry-run": {
            "contexts": {"keywords"},
            "documentation": "Excludes the user keyword from normal dry-run validation. Valid in keywords.",
        },
        "robot:flatten": {
            "contexts": {"keywords"},
            "documentation": "Flattens/suppresses detailed keyword logging in output. Valid in keywords.",
        },
    }

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

        dictionary_items = self._dictionary_key_items(context)
        if dictionary_items is not None:
            return CompletionList(dictionary_items)
        if self._is_variable_type_context(context):
            return CompletionList(self._variable_type_items())
        if self._is_variable_context(context):
            return CompletionList(self._variable_items(context))
        if self._is_section_context(context):
            return CompletionList(self._section_items(snippets_enabled=snippets_enabled))
        local_setting_items = self._local_setting_items(context)
        if local_setting_items is not None:
            return CompletionList(local_setting_items)
        tag_items = self._tag_items(context)
        if tag_items is not None:
            return CompletionList(tag_items)
        if context.section == "settings":
            return CompletionList(self._setting_items())
        if context.section in {"test cases", "tasks", "keywords"}:
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
        last_open = max(context.line_prefix.rfind(f"{prefix}{{") for prefix in self.VARIABLE_TRIGGERS)
        if last_open != -1 and context.line_prefix.rfind("}") < last_open:
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

    def _local_setting_items(self, context: CompletionContext) -> list[CompletionItem] | None:
        if context.section not in {"test cases", "tasks", "keywords"}:
            return None
        stripped = context.line_prefix.lstrip()
        if not stripped.startswith("[") and context.trigger_character != "[":
            return None
        if "]" in stripped:
            return None

        source = self.KEYWORD_SETTING_ITEMS if context.section == "keywords" else self.TEST_CASE_SETTING_ITEMS
        prefix = stripped[1:].casefold()
        return [
            CompletionItem(
                label=f"[{item}]",
                kind=CompletionItemKind.KEYWORD,
                detail="Robot Framework local setting",
            )
            for item in source
            if item.casefold().startswith(prefix)
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
            existing_labels = {item.label for item in items}
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
                if location.name not in existing_labels
            )
            existing_labels = {item.label for item in items}
            lib_keywords, _ = self._workspace_index.imported_library_keywords(
                context.document.path, context.suite
            )
            items.extend(
                CompletionItem(
                    label=name,
                    kind=CompletionItemKind.FUNCTION,
                    detail="Library keyword",
                )
                for name in lib_keywords
                if name not in existing_labels
            )
        existing_labels = {item.label for item in items}
        items.extend(
            CompletionItem(
                label=name,
                kind=CompletionItemKind.FUNCTION,
                detail="BuiltIn keyword",
            )
            for name in _builtin_keywords()
            if name not in existing_labels
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

    def _tag_items(self, context: CompletionContext) -> list[CompletionItem] | None:
        if context.section not in {"test cases", "tasks", "keywords"}:
            return None
        prefix = _tag_prefix(context)
        if prefix is None:
            return None
        normalized_prefix = prefix.casefold()
        return [
            CompletionItem(
                label=tag,
                kind=CompletionItemKind.KEYWORD,
                detail="Reserved Robot Framework tag",
                documentation=metadata["documentation"],
            )
            for tag, metadata in self.RESERVED_TAGS.items()
            if context.section in metadata["contexts"] and tag.casefold().startswith(normalized_prefix)
        ]

    def _variable_items(self, context: CompletionContext) -> list[CompletionItem]:
        if context.suite is None:
            return []
        sigil = _variable_completion_sigil(context)
        items: list[CompletionItem] = []
        seen: set[str] = set()
        for variable in context.suite.variables:
            _append_variable_item(
                items,
                seen,
                variable.name,
                f"Local {variable.kind} variable",
                str(variable.value) if variable.value is not None else None,
                sigil,
            )
        for variable in _scoped_variables(context):
            _append_variable_item(
                items,
                seen,
                variable.name,
                f"Scoped {variable.kind} variable",
                str(variable.value) if variable.value is not None else None,
                sigil,
            )
        if self._workspace_index is not None and context.document.path is not None:
            for location in self._workspace_index.imported_variable_locations(
                context.document.path,
                context.suite,
            ):
                _append_variable_item(items, seen, location.name, "Imported variable", None, sigil)
        return items

    def _dictionary_key_items(self, context: CompletionContext) -> list[CompletionItem] | None:
        access = _dictionary_access(context.line_prefix)
        if access is None:
            return None
        if context.suite is None:
            return []

        variables = []
        if self._workspace_index is not None and context.document.path is not None:
            variables.extend(
                self._workspace_index.imported_variables(
                    context.document.path,
                    context.suite,
                )
            )
        variables.extend(_visible_variables(context))

        dictionary = _resolve_dictionary(access.base_name, access.path, variables)
        if dictionary is None:
            return []

        filter_text = access.filter_text.casefold()
        return [
            CompletionItem(
                label=key,
                kind=CompletionItemKind.FIELD,
                detail="Dictionary key",
                documentation=str(value) if value is not None else None,
                text_edit=_dictionary_key_text_edit(context, access.filter_text, key, quote_key=access.quote_key),
            )
            for key, value in dictionary.items()
            if key.casefold().startswith(filter_text)
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
        elif normalized == "*** tasks ***":
            section = "tasks"
        elif normalized == "*** keywords ***":
            section = "keywords"
    return section


def _tag_prefix(context: CompletionContext) -> str | None:
    lines = _logical_lines(context.document.text)
    if context.position.line < 0 or context.position.line >= len(lines):
        return None
    tag_start_line = _tag_statement_start_line(lines, context.position.line)
    if tag_start_line is None:
        return None
    return _tag_value_prefix(context.line_prefix)


def _tag_statement_start_line(lines: list[str], line: int) -> int | None:
    cursor = line
    while cursor >= 0:
        if cursor != line and not _is_continuation_line(lines[cursor + 1]):
            return None
        if _is_continuation_line(lines[cursor]):
            cursor -= 1
            continue
        return cursor if _is_tags_line(lines[cursor]) else None
    return None


def _is_tags_line(line: str) -> bool:
    cells = _robot_cells(line)
    return bool(cells) and cells[0].casefold() == "[tags]"


def _is_continuation_line(line: str) -> bool:
    cells = _robot_cells(line)
    return bool(cells) and cells[0] == "..."


def _tag_value_prefix(line_prefix: str) -> str | None:
    cells = _robot_cells(line_prefix)
    if not cells:
        return ""
    first = cells[0].casefold()
    if first not in {"[tags]", "..."}:
        return None
    if _ends_with_separator(line_prefix):
        return ""
    return cells[-1] if len(cells) > 1 else ""


def _robot_cells(line: str) -> list[str]:
    return [cell for cell in re.split(r"(?: {2,}|\t+)", line.strip()) if cell]


def _ends_with_separator(text: str) -> bool:
    return text.endswith("\t") or len(text) >= 2 and text[-2:] == "  "


def _scoped_variables(context: CompletionContext):
    if context.suite is None:
        return []
    variables = []
    for test_case in context.suite.test_cases:
        if test_case.range.start.line <= context.position.line <= test_case.range.end.line:
            variables.extend(variable for variable in test_case.variables if _declared_before(variable, context.position))
    for keyword in context.suite.keywords:
        if keyword.range.start.line <= context.position.line <= keyword.range.end.line:
            variables.extend(variable for variable in keyword.variables if _declared_before(variable, context.position))
    return variables


@dataclass(frozen=True)
class _DictionaryAccess:
    base_name: str
    path: list[str]
    filter_text: str
    quote_key: bool = False


def _dictionary_access(line_prefix: str) -> _DictionaryAccess | None:
    bracket = _bracket_dictionary_access(line_prefix)
    if bracket is not None:
        return bracket
    return _dot_dictionary_access(line_prefix)


def _bracket_dictionary_access(line_prefix: str) -> _DictionaryAccess | None:
    inline = _inline_bracket_dictionary_access(line_prefix)
    if inline is not None:
        return inline

    open_index = line_prefix.rfind("[")
    if open_index == -1 or "]" in line_prefix[open_index:]:
        return None
    prefix = line_prefix[:open_index]
    filter_text = line_prefix[open_index + 1 :]
    if any(char.isspace() for char in filter_text):
        return None

    close_index = prefix.rfind("}")
    if close_index == -1:
        return None
    open_brace_index = max(prefix.rfind("${", 0, close_index), prefix.rfind("&{", 0, close_index))
    if open_brace_index == -1:
        return None

    base_name = prefix[open_brace_index + 2 : close_index]
    if not base_name:
        return None
    path = _completed_bracket_path(prefix[close_index + 1 :])
    if path is None:
        return None
    return _DictionaryAccess(base_name=base_name, path=path, filter_text=filter_text, quote_key=True)


def _inline_bracket_dictionary_access(line_prefix: str) -> _DictionaryAccess | None:
    open_brace_index = max(line_prefix.rfind("${"), line_prefix.rfind("&{"))
    if open_brace_index == -1:
        return None
    close_index = line_prefix.find("}", open_brace_index + 2)
    inner_end = close_index if close_index != -1 else len(line_prefix)
    inner = line_prefix[open_brace_index + 2 : inner_end]
    if not inner or any(char.isspace() for char in inner):
        return None
    if "[" not in inner:
        return None

    base_name, _, remainder = inner.partition("[")
    if not base_name or "]" in remainder:
        return None
    return _DictionaryAccess(base_name=base_name, path=[], filter_text=remainder, quote_key=True)


def _completed_bracket_path(text: str) -> list[str] | None:
    path: list[str] = []
    index = 0
    while index < len(text):
        if text[index] != "[":
            return None
        end_index = text.find("]", index + 1)
        if end_index == -1:
            return None
        path.append(text[index + 1 : end_index])
        index = end_index + 1
    return path


def _dot_dictionary_access(line_prefix: str) -> _DictionaryAccess | None:
    inline = _inline_dot_dictionary_access(line_prefix)
    if inline is not None:
        return inline

    close_index = line_prefix.rfind("}")
    if close_index == -1:
        return None
    open_brace_index = max(line_prefix.rfind("${", 0, close_index), line_prefix.rfind("&{", 0, close_index))
    if open_brace_index == -1:
        return None

    suffix = line_prefix[close_index + 1 :]
    if not suffix.startswith("."):
        return None
    base_name = line_prefix[open_brace_index + 2 : close_index]
    if not base_name:
        return None
    parts = suffix[1:].split(".")
    return _DictionaryAccess(base_name=base_name, path=parts[:-1], filter_text=parts[-1])


def _inline_dot_dictionary_access(line_prefix: str) -> _DictionaryAccess | None:
    open_brace_index = max(line_prefix.rfind("${"), line_prefix.rfind("&{"))
    if open_brace_index == -1:
        return None
    close_index = line_prefix.find("}", open_brace_index + 2)
    inner_end = close_index if close_index != -1 else len(line_prefix)
    inner = line_prefix[open_brace_index + 2 : inner_end]
    if not inner or any(char.isspace() for char in inner):
        return None
    if "." not in inner:
        return None
    parts = inner.split(".")
    if not parts[0]:
        return None
    return _DictionaryAccess(base_name=parts[0], path=parts[1:-1], filter_text=parts[-1])


def _visible_variables(context: CompletionContext):
    if context.suite is None:
        return []
    return [*context.suite.variables, *_scoped_variables(context)]


def _dictionary_key_text_edit(
    context: CompletionContext,
    filter_text: str,
    key: str,
    *,
    quote_key: bool = False,
) -> dict[str, Any]:
    start_character = max(0, context.position.character - _utf16_len(filter_text))
    new_text = _dictionary_key_new_text(context, key, quote_key=quote_key)
    return {
        "range": {
            "start": {"line": context.position.line, "character": start_character},
            "end": {"line": context.position.line, "character": context.position.character},
        },
        "newText": new_text,
    }


def _dictionary_key_new_text(context: CompletionContext, key: str, *, quote_key: bool) -> str:
    if not quote_key:
        return key
    if _character_at_utf16(context.line_text, context.position.character) == "]":
        return f'"{key}"'
    return f'"{key}"]'


def _character_at_utf16(text: str, character: int) -> str | None:
    offset = position_to_utf16_offset(text, 0, character)
    if offset is None or offset < 0 or offset >= len(text):
        return None
    return text[offset]


def _utf16_len(text: str) -> int:
    return sum(1 if ord(ch) < 0x10000 else 2 for ch in text)


def _append_variable_item(
    items: list[CompletionItem],
    seen: set[str],
    name: str,
    detail: str,
    documentation: str | None,
    sigil: str | None,
) -> None:
    base = _variable_base_name(name)
    if base is None:
        label = name
        key = name.casefold()
    else:
        label = _format_variable_name(sigil, base) if sigil is not None else name
        key = _normalize_variable_base(base)
    if key in seen:
        return
    seen.add(key)
    items.append(
        CompletionItem(
            label=label,
            kind=CompletionItemKind.VARIABLE,
            detail=detail,
            documentation=documentation,
        )
    )


def _variable_completion_sigil(context: CompletionContext) -> str | None:
    if context.trigger_character in CompletionService.VARIABLE_TRIGGERS:
        return context.trigger_character
    for sigil in CompletionService.VARIABLE_TRIGGERS:
        if context.line_prefix.endswith(sigil):
            return sigil
    last_open = max((context.line_prefix.rfind(f"{sigil}{{"), sigil) for sigil in CompletionService.VARIABLE_TRIGGERS)
    index, sigil = last_open
    if index != -1 and context.line_prefix.rfind("}") < index:
        return sigil
    return None


def _variable_base_name(name: str) -> str | None:
    if len(name) >= 4 and name[1] == "{" and name.endswith("}") and name[0] in CompletionService.VARIABLE_TRIGGERS:
        return name[2:-1]
    return None


def _format_variable_name(sigil: str, base: str) -> str:
    return f"{sigil}{{{base}}}"


def _normalize_variable_base(base: str) -> str:
    return "".join(char for char in base.casefold() if char not in " _")


def _resolve_dictionary(base_name: str, path: list[str], variables) -> dict[str, Any] | None:
    by_name = {_normalize_variable_name(variable.name): variable for variable in variables}
    current = _dictionary_value(base_name, by_name)
    for key in path:
        if current is None or key not in current:
            return None
        value = current[key]
        if isinstance(value, dict):
            current = value
        elif isinstance(value, str) and value.startswith("&{") and value.endswith("}"):
            current = _dictionary_value(value[2:-1], by_name)
        else:
            return None
    return current


def _dictionary_value(name: str, by_name: dict[str, Any]) -> dict[str, Any] | None:
    variable = by_name.get(_normalize_variable_name(name))
    if variable is None or variable.kind != "dict" or not isinstance(variable.value, dict):
        return None
    return variable.value


def _normalize_variable_name(name: str) -> str:
    if len(name) >= 4 and name[1] == "{" and name.endswith("}") and name[0] in "$@&%":
        name = name[2:-1]
    return "".join(char for char in name.casefold() if char not in " _")


def _declared_before(variable, position: LspPosition) -> bool:
    if variable.range.start.line < position.line:
        return True
    if variable.range.start.line == position.line:
        return variable.range.start.character < position.character
    return False


@lru_cache(maxsize=1)
def _builtin_keywords() -> tuple[str, ...]:
    try:
        from robot.libdocpkg import LibraryDocumentation  # type: ignore[import]

        libdoc = LibraryDocumentation("BuiltIn")
        return tuple(keyword.name for keyword in libdoc.keywords)
    except Exception:
        return (
            "Log",
            "No Operation",
            "Should Be Equal",
            "Should Not Be Equal",
            "Should Be True",
            "Should Be False",
            "Fail",
            "Set Variable",
            "Create List",
            "Create Dictionary",
            "Run Keyword If",
        )
