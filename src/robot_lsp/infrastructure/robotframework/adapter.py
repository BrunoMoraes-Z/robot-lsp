from __future__ import annotations

from pathlib import Path
from typing import Any

from robot.api.parsing import Token

from robot_lsp.domain.features import FeatureSet
from robot_lsp.domain.models import (
    LspPosition,
    LspRange,
    ParseResult,
    RobotArg,
    RobotDiagnostic,
    RobotImport,
    RobotKeyword,
    RobotSettings,
    RobotStep,
    RobotSuite,
    RobotTestCase,
    RobotVariable,
)

from .visitors import ErrorCollectingVisitor


class RobotFrameworkASTAdapter:
    def __init__(self, features: FeatureSet) -> None:
        self._features = features

    def to_parse_result(self, model: Any, *, source: str | None = None) -> ParseResult:
        errors = self._collect_errors(model)
        return ParseResult(suite=self.to_suite(model, source=source), errors=errors)

    def to_suite(self, model: Any, *, source: str | None = None) -> RobotSuite:
        settings = RobotSettings()
        variables: list[RobotVariable] = []
        imports: list[RobotImport] = []
        test_cases: list[RobotTestCase] = []
        keywords: list[RobotKeyword] = []
        doc = ""
        metadata: dict[str, str] = {}

        for section in getattr(model, "sections", []):
            section_type = type(section).__name__
            if section_type == "SettingSection":
                section_settings, section_imports, section_doc, section_metadata = self._settings(section)
                settings = section_settings
                imports.extend(section_imports)
                doc = section_doc or doc
                metadata.update(section_metadata)
            elif section_type == "VariableSection":
                variables.extend(self._variables(section))
            elif section_type == "TestCaseSection":
                test_cases.extend(self._test_cases(section))
            elif section_type == "KeywordSection":
                keywords.extend(self._keywords(section))

        suite_name = Path(source).stem if source else "document"
        return RobotSuite(
            source=source,
            name=suite_name,
            doc=doc,
            metadata=metadata,
            settings=settings,
            variables=variables,
            imports=imports,
            test_cases=test_cases,
            keywords=keywords,
        )

    def to_diagnostic(self, node: Any) -> RobotDiagnostic:
        message = (
            getattr(node, "error", None)
            or getattr(node, "message", None)
            or "Robot Framework parse error"
        )
        return RobotDiagnostic(
            message=str(message),
            severity="error",
            range=self._node_range(node),
            code="parse_error",
        )

    def _settings(self, section: Any) -> tuple[RobotSettings, list[RobotImport], str, dict[str, str]]:
        settings = RobotSettings()
        imports: list[RobotImport] = []
        doc = ""
        metadata: dict[str, str] = {}

        for stmt in getattr(section, "body", []):
            stmt_type = type(stmt).__name__
            if stmt_type == "LibraryImport":
                imports.append(self._import(stmt, "library"))
            elif stmt_type == "ResourceImport":
                imports.append(self._import(stmt, "resource"))
            elif stmt_type == "VariablesImport":
                imports.append(self._import(stmt, "variables"))
            elif stmt_type == "Documentation":
                doc = _joined(_token_values(stmt, Token.ARGUMENT))
            elif stmt_type == "Metadata":
                name = _token_value(stmt, Token.NAME) or ""
                metadata[name] = _joined(_token_values(stmt, Token.ARGUMENT))
            elif stmt_type == "SuiteSetup":
                settings.suite_setup = _call_text(stmt)
            elif stmt_type == "SuiteTeardown":
                settings.suite_teardown = _call_text(stmt)
            elif stmt_type == "TestSetup":
                settings.test_setup = _call_text(stmt)
            elif stmt_type == "TestTeardown":
                settings.test_teardown = _call_text(stmt)
            elif stmt_type == "TestTemplate":
                settings.test_template = _call_text(stmt)
            elif stmt_type == "TestTimeout":
                settings.test_timeout = _call_text(stmt) or _joined(_token_values(stmt, Token.ARGUMENT))
            elif stmt_type in {"ForceTags", "TestTags"}:
                settings.force_tags = _token_values(stmt, Token.ARGUMENT)
            elif stmt_type == "DefaultTags":
                settings.default_tags = _token_values(stmt, Token.ARGUMENT)

        return settings, imports, doc, metadata

    def _import(self, stmt: Any, import_type: str) -> RobotImport:
        name = _token_value(stmt, Token.NAME) or getattr(stmt, "name", "") or ""
        values = _token_values(stmt, Token.ARGUMENT)
        alias = _alias(stmt)
        args = values
        return RobotImport(
            type=import_type,  # type: ignore[arg-type]
            name=name,
            args=args,
            alias=alias,
            range=self._node_range(stmt),
        )

    def _variables(self, section: Any) -> list[RobotVariable]:
        variables: list[RobotVariable] = []
        for stmt in getattr(section, "body", []):
            if type(stmt).__name__ != "Variable":
                continue
            name = _token_value(stmt, Token.VARIABLE) or getattr(stmt, "name", "") or ""
            if not name:
                continue
            values = _token_values(stmt, Token.ARGUMENT)
            variables.append(
                RobotVariable(
                    name=name,
                    value=_variable_value(name, values),
                    kind=_variable_kind(name, self._features),
                    range=self._node_range(stmt),
                )
            )
        return variables

    def _test_cases(self, section: Any) -> list[RobotTestCase]:
        cases: list[RobotTestCase] = []
        for node in getattr(section, "body", []):
            if type(node).__name__ != "TestCase":
                continue
            doc, tags, template, timeout, setup, teardown, body = self._body_items(node)
            cases.append(
                RobotTestCase(
                    name=getattr(node, "name", "") or "",
                    doc=doc,
                    tags=tags,
                    template=template,
                    timeout=timeout,
                    setup=setup,
                    teardown=teardown,
                    body=body,
                    range=self._node_range(node),
                )
            )
        return cases

    def _keywords(self, section: Any) -> list[RobotKeyword]:
        keywords: list[RobotKeyword] = []
        for node in getattr(section, "body", []):
            if type(node).__name__ != "Keyword":
                continue
            doc, tags, _template, _timeout, _setup, _teardown, body = self._body_items(node)
            keywords.append(
                RobotKeyword(
                    name=getattr(node, "name", "") or "",
                    doc=doc,
                    tags=tags,
                    args=self._keyword_args(node),
                    body=body,
                    range=self._node_range(node),
                )
            )
        return keywords

    def _body_items(
        self, node: Any
    ) -> tuple[str, list[str], str | None, str | None, str | None, str | None, list[RobotStep]]:
        doc = ""
        tags: list[str] = []
        template = None
        timeout = None
        setup = None
        teardown = None
        body: list[RobotStep] = []

        for stmt in getattr(node, "body", []):
            stmt_type = type(stmt).__name__
            if stmt_type == "Documentation":
                doc = _joined(_token_values(stmt, Token.ARGUMENT))
            elif stmt_type == "Tags":
                tags = _token_values(stmt, Token.ARGUMENT)
            elif stmt_type == "Template":
                template = _call_text(stmt)
            elif stmt_type == "Timeout":
                timeout = _call_text(stmt)
            elif stmt_type == "Setup":
                setup = _call_text(stmt)
            elif stmt_type == "Teardown":
                teardown = _call_text(stmt)
            elif stmt_type == "KeywordCall":
                body.append(self._step(stmt))
        return doc, tags, template, timeout, setup, teardown, body

    def _keyword_args(self, node: Any) -> list[RobotArg]:
        for stmt in getattr(node, "body", []):
            if type(stmt).__name__ == "Arguments":
                return [_arg(value) for value in _token_values(stmt, Token.ARGUMENT)]
        return []

    def _step(self, stmt: Any) -> RobotStep:
        return RobotStep(
            keyword=_token_value(stmt, Token.KEYWORD) or getattr(stmt, "keyword", "") or "",
            args=_token_values(stmt, Token.ARGUMENT),
            assign=_token_values(stmt, Token.ASSIGN),
            range=self._node_range(stmt),
        )

    def _collect_errors(self, model: Any) -> list[RobotDiagnostic]:
        visitor = ErrorCollectingVisitor(self)
        visitor.visit(model)
        return visitor.errors

    def _node_range(self, node: Any) -> LspRange:
        tokens = [token for token in _tokens(node) if token.type not in {Token.SEPARATOR, Token.EOL}]
        if not tokens:
            tokens = _tokens(node)
        if not tokens:
            return LspRange(LspPosition(0, 0), LspPosition(0, 0))
        start = tokens[0]
        end = tokens[-1]
        start_line = max(0, (start.lineno or 1) - 1)
        start_col = start.col_offset or 0
        end_line = max(0, (end.lineno or start.lineno or 1) - 1)
        end_col = (end.col_offset or 0) + _utf16_len(end.value or "")
        return LspRange(
            start=LspPosition(start_line, start_col),
            end=LspPosition(end_line, end_col),
        )


def _tokens(node: Any) -> list[Any]:
    tokens = list(getattr(node, "tokens", []) or [])
    header = getattr(node, "header", None)
    if header is not None:
        tokens = list(getattr(header, "tokens", []) or []) + tokens
    for child in getattr(node, "body", []) or []:
        tokens.extend(_tokens(child))
    return tokens


def _token_values(stmt: Any, token_type: str) -> list[str]:
    return [token.value for token in getattr(stmt, "tokens", []) if token.type == token_type]


def _token_value(stmt: Any, token_type: str) -> str | None:
    values = _token_values(stmt, token_type)
    return values[0] if values else None


def _joined(values: list[str]) -> str:
    return " ".join(values)


def _call_text(stmt: Any) -> str | None:
    name = _token_value(stmt, Token.NAME)
    if name is None:
        return None
    args = _token_values(stmt, Token.ARGUMENT)
    return "    ".join([name, *args])


def _alias(stmt: Any) -> str | None:
    tokens = list(getattr(stmt, "tokens", []) or [])
    for index, token in enumerate(tokens):
        if token.type == Token.AS:
            for candidate in tokens[index + 1 :]:
                if candidate.type == Token.NAME:
                    return candidate.value
    return None


def _variable_value(name: str, values: list[str]) -> str | list[str] | dict[str, str] | None:
    if name.startswith("@{"):
        return values
    if name.startswith("&{"):
        result: dict[str, str] = {}
        for value in values:
            key, sep, item = value.partition("=")
            if sep:
                result[key] = item
        return result
    return values[0] if values else None


def _variable_kind(name: str, features: FeatureSet):
    if features.has_secret_variables and name.startswith("${") and name.endswith("}") and name[2:].startswith("SECRET"):
        return "secret"
    if name.startswith("@{"):
        return "list"
    if name.startswith("&{"):
        return "dict"
    return "scalar"


def _arg(value: str) -> RobotArg:
    name, sep, default = value.partition("=")
    if name.startswith("@{"):
        kind = "varargs"
    elif name.startswith("&{"):
        kind = "kwargs"
    elif sep:
        kind = "optional"
    else:
        kind = "positional"
    return RobotArg(name=name, default=default if sep else None, kind=kind)  # type: ignore[arg-type]


def _utf16_len(text: str) -> int:
    return sum(1 if ord(ch) < 0x10000 else 2 for ch in text)
