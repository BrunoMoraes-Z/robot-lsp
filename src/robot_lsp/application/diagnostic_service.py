from __future__ import annotations

import re
import threading
from collections.abc import Callable

from robot_lsp.domain.diagnostics import DiagnosticSeverity, LspDiagnostic
from robot_lsp.domain.models import LspRange, RobotDiagnostic, RobotStep, RobotSuite

from .parse_service import ParseService
from .workspace import WorkspaceIndex


PublishDiagnostics = Callable[[str, list[LspDiagnostic]], None]


class DiagnosticService:
    DEBOUNCE_SECONDS = 0.3

    def __init__(
        self,
        parse_service: ParseService,
        publisher: PublishDiagnostics,
        *,
        workspace_index: WorkspaceIndex | None = None,
        debounce_seconds: float | None = None,
    ) -> None:
        self._parse_service = parse_service
        self._publisher = publisher
        self._workspace_index = workspace_index
        self._debounce_seconds = (
            self.DEBOUNCE_SECONDS if debounce_seconds is None else debounce_seconds
        )
        self._timers: dict[str, threading.Timer] = {}
        self._last_diagnostics: dict[str, list[LspDiagnostic]] = {}
        self._lock = threading.RLock()

    def schedule_diagnostics(self, uri: str) -> None:
        self.cancel_pending(uri)
        timer = threading.Timer(self._debounce_seconds, self.compute_and_publish, args=(uri,))
        with self._lock:
            self._timers[uri] = timer
        timer.start()

    def compute_and_publish(self, uri: str) -> None:
        with self._lock:
            self._timers.pop(uri, None)

        result = self._parse_service.parse_uri(uri)
        diagnostics = [] if result is None else [_to_lsp(item) for item in result.errors]
        if result is not None and result.suite is not None and not result.errors:
            diagnostics.extend(self._semantic_diagnostics(uri, result.suite))
        self.publish_if_changed(uri, diagnostics)

    def flush(self, uri: str) -> None:
        self.cancel_pending(uri)
        self.compute_and_publish(uri)

    def publish_if_changed(self, uri: str, diagnostics: list[LspDiagnostic]) -> None:
        with self._lock:
            if self._last_diagnostics.get(uri) == diagnostics:
                return
            self._last_diagnostics[uri] = diagnostics
        self._publisher(uri, diagnostics)

    def cancel_pending(self, uri: str) -> bool:
        with self._lock:
            timer = self._timers.pop(uri, None)
        if timer is None:
            return False
        timer.cancel()
        return True

    def clear(self, uri: str) -> None:
        self.cancel_pending(uri)
        self.publish_if_changed(uri, [])

    def _semantic_diagnostics(self, uri: str, suite: RobotSuite) -> list[LspDiagnostic]:
        diagnostics: list[LspDiagnostic] = []
        diagnostics.extend(self._import_diagnostics(uri, suite))
        diagnostics.extend(self._type_diagnostics(suite))
        diagnostics.extend(self._keyword_diagnostics(uri, suite))
        diagnostics.extend(self._variable_diagnostics(uri, suite))
        return diagnostics

    def _import_diagnostics(self, uri: str, suite: RobotSuite) -> list[LspDiagnostic]:
        if self._workspace_index is None:
            return []
        source_path = self._source_path(uri)
        if source_path is None:
            return []
        diagnostics = []
        for import_ in suite.imports:
            if self._workspace_index.resolve_import(source_path, import_).resolved_path is None:
                diagnostics.append(
                    _diagnostic(
                        import_.range,
                        DiagnosticSeverity.ERROR,
                        f"Import not found: {import_.name}",
                        "import_not_found",
                    )
                )
        return diagnostics

    def _keyword_diagnostics(self, uri: str, suite: RobotSuite) -> list[LspDiagnostic]:
        known_keywords = {keyword.name.casefold() for keyword in suite.keywords}
        known_keywords.update(_BUILTIN_KEYWORDS)
        source_path = self._source_path(uri)
        if self._workspace_index is not None and source_path is not None:
            known_keywords.update(
                location.name.casefold()
                for location in self._workspace_index.imported_keyword_locations(source_path, suite)
            )

        diagnostics = []
        for step in _steps(suite):
            if not step.keyword or _is_control_keyword(step.keyword):
                continue
            if step.keyword.casefold() not in known_keywords:
                diagnostics.append(
                    _diagnostic(
                        step.range,
                        DiagnosticSeverity.WARNING,
                        f"Keyword not found: {step.keyword}",
                        "keyword_not_found",
                    )
                )
        return diagnostics

    def _variable_diagnostics(self, uri: str, suite: RobotSuite) -> list[LspDiagnostic]:
        defined = {_normalize_variable(variable.name) for variable in suite.variables}
        defined.update(_BUILTIN_VARIABLES)
        source_path = self._source_path(uri)
        if self._workspace_index is not None and source_path is not None:
            defined.update(
                _normalize_variable(location.name)
                for location in self._workspace_index.imported_variable_locations(source_path, suite)
            )
        diagnostics = []
        for keyword in suite.keywords:
            defined_with_args = defined | {_normalize_variable(arg.name) for arg in keyword.args}
            defined_with_args.update(_normalize_variable(variable.name) for variable in keyword.variables)
            diagnostics.extend(_undefined_variable_diagnostics(keyword.body, defined_with_args))
        for test_case in suite.test_cases:
            defined_with_vars = defined | {_normalize_variable(variable.name) for variable in test_case.variables}
            diagnostics.extend(_undefined_variable_diagnostics(test_case.body, defined_with_vars))
        return diagnostics

    def _type_diagnostics(self, suite: RobotSuite) -> list[LspDiagnostic]:
        diagnostics = []
        variables = list(suite.variables)
        for keyword in suite.keywords:
            variables.extend(keyword.variables)
        for test_case in suite.test_cases:
            variables.extend(test_case.variables)
        for variable in variables:
            if variable.type_annotation is not None and not _is_valid_type_annotation(variable.type_annotation):
                diagnostics.append(
                    _diagnostic(
                        variable.range,
                        DiagnosticSeverity.WARNING,
                        f"Unknown variable type: {variable.type_annotation}",
                        "unknown_variable_type",
                    )
                )
        return diagnostics

    def _source_path(self, uri: str):
        return self._parse_service.document_path(uri)


def _to_lsp(diagnostic: RobotDiagnostic) -> LspDiagnostic:
    return LspDiagnostic(
        range=diagnostic.range,
        severity=_severity(diagnostic.severity),
        message=diagnostic.message,
        source="robot-lsp",
        code=diagnostic.code,
    )


def _severity(severity: str) -> DiagnosticSeverity:
    if severity == "warning":
        return DiagnosticSeverity.WARNING
    if severity == "info":
        return DiagnosticSeverity.INFORMATION
    return DiagnosticSeverity.ERROR


_VARIABLE_PATTERN = re.compile(r"[$@&%]\{[^}]+\}")
_BUILTIN_VARIABLES = {"${CURDIR}", "${TEMPDIR}", "${EXECDIR}", "${/}", "${:}", "${SPACE}", "${EMPTY}", "${TRUE}", "${FALSE}", "${NONE}", "${NULL}"}
_BUILTIN_KEYWORDS = {
    "log",
    "no operation",
    "should be equal",
    "should not be equal",
    "should be true",
    "should be false",
    "fail",
    "set variable",
    "create list",
    "create dictionary",
}
_BUILTIN_TYPES = {
    "Any",
    "bool",
    "bytes",
    "date",
    "datetime",
    "Decimal",
    "dict",
    "float",
    "int",
    "list",
    "None",
    "Path",
    "Secret",
    "set",
    "str",
    "timedelta",
    "tuple",
}


def _steps(suite: RobotSuite) -> list[RobotStep]:
    return [step for test_case in suite.test_cases for step in test_case.body] + [
        step for keyword in suite.keywords for step in keyword.body
    ]


def _undefined_variable_diagnostics(steps: list[RobotStep], defined: set[str]) -> list[LspDiagnostic]:
    diagnostics = []
    local_defined = set(defined)
    for step in steps:
        for value in [step.keyword, *step.args]:
            for variable in _VARIABLE_PATTERN.findall(value):
                if _normalize_variable(variable) not in local_defined:
                    diagnostics.append(
                        _diagnostic(
                            step.range,
                            DiagnosticSeverity.WARNING,
                            f"Variable not found: {variable}",
                            "variable_not_found",
                        )
                    )
        local_defined.update(_normalize_variable(assign) for assign in step.assign)
    return diagnostics


def _normalize_variable(variable: str) -> str:
    return variable.rstrip("=").casefold()


def _is_control_keyword(keyword: str) -> bool:
    return keyword.upper() in {"IF", "ELSE", "ELSE IF", "END", "FOR", "WHILE", "TRY", "EXCEPT", "FINALLY"}


def _diagnostic(range_: LspRange, severity: DiagnosticSeverity, message: str, code: str) -> LspDiagnostic:
    return LspDiagnostic(range=range_, severity=severity, message=message, source="robot-lsp", code=code)


def _is_valid_type_annotation(type_annotation: str) -> bool:
    parts = [part.strip() for part in type_annotation.replace("|", ",").split(",")]
    return all(part in _BUILTIN_TYPES for part in parts if part)
