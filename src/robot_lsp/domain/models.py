from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class LspPosition:
    line: int
    character: int


@dataclass
class LspRange:
    start: LspPosition
    end: LspPosition


@dataclass
class RobotArg:
    name: str
    default: str | None
    kind: Literal["positional", "optional", "varargs", "kwargs"]
    type_annotation: str | None = None


@dataclass
class RobotStep:
    keyword: str
    args: list[str]
    assign: list[str]
    range: LspRange


@dataclass
class RobotSettings:
    suite_setup: str | None = None
    suite_teardown: str | None = None
    test_setup: str | None = None
    test_teardown: str | None = None
    test_template: str | None = None
    test_timeout: str | None = None
    force_tags: list[str] = field(default_factory=list)
    default_tags: list[str] = field(default_factory=list)


@dataclass
class RobotVariable:
    name: str
    value: str | list | dict | None
    kind: Literal["scalar", "list", "dict", "secret"]
    range: LspRange
    scope: Literal["local", "test", "suite", "global"] | None = None
    type_annotation: str | None = None


@dataclass
class RobotImport:
    type: Literal["library", "resource", "variables"]
    name: str
    args: list[str]
    alias: str | None
    range: LspRange


@dataclass
class RobotTestCase:
    name: str
    doc: str
    tags: list[str]
    template: str | None
    timeout: str | None
    setup: str | None
    teardown: str | None
    body: list[RobotStep]
    range: LspRange
    variables: list[RobotVariable] = field(default_factory=list)


@dataclass
class RobotKeyword:
    name: str
    doc: str
    tags: list[str]
    args: list[RobotArg]
    body: list[RobotStep]
    range: LspRange
    variables: list[RobotVariable] = field(default_factory=list)


@dataclass
class RobotSuite:
    source: str | None
    name: str
    doc: str
    metadata: dict[str, str]
    settings: RobotSettings
    variables: list[RobotVariable]
    imports: list[RobotImport]
    test_cases: list[RobotTestCase]
    keywords: list[RobotKeyword]


@dataclass
class RobotDiagnostic:
    message: str
    severity: Literal["error", "warning", "info"]
    range: LspRange
    code: str | None = None


@dataclass
class RobotDocument:
    uri: str
    version: int
    text: str
    suite: RobotSuite | None
    errors: list[RobotDiagnostic]


@dataclass
class ParseResult:
    suite: RobotSuite | None
    errors: list[RobotDiagnostic] = field(default_factory=list)
