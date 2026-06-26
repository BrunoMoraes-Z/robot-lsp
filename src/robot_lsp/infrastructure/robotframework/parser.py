from __future__ import annotations

import tempfile
import re
from pathlib import Path

from robot.api.parsing import get_model
from robot.api.parsing import Token

from robot_lsp.application.semantic_tokens_service import SemanticToken
from robot_lsp.domain.features import FeatureSet
from robot_lsp.domain.models import ParseResult

from .adapter import RobotFrameworkASTAdapter
from .version import RobotFrameworkVersionDetector


_VARIABLE_RE = re.compile(r"[$@&%]\{[^}\r\n]+\}")


class RobotFrameworkParser:
    def __init__(self, features: FeatureSet | None = None) -> None:
        self._features = features or RobotFrameworkVersionDetector().detect()
        self._adapter = RobotFrameworkASTAdapter(self._features)

    def parse_file(self, path: Path) -> ParseResult:
        model = get_model(str(path))
        return self._adapter.to_parse_result(model, source=str(path))

    def parse_text(self, text: str, *, source_name: str = "document.robot") -> ParseResult:
        with tempfile.TemporaryDirectory(prefix="robot-lsp-") as tmp_dir:
            path = Path(tmp_dir) / source_name
            path.write_text(text, encoding="utf-8")
            return self.parse_file(path)

    def semantic_tokens(self, text: str, *, source_name: str = "document.robot") -> list[SemanticToken]:
        with tempfile.TemporaryDirectory(prefix="robot-lsp-") as tmp_dir:
            path = Path(tmp_dir) / source_name
            path.write_text(text, encoding="utf-8")
            model = get_model(str(path))
            return _semantic_tokens(model)


def _semantic_tokens(model) -> list[SemanticToken]:
    result: list[SemanticToken] = []
    seen: set[tuple[int, int, int, str]] = set()
    for node in _iter_nodes(model):
        for raw_token in _node_tokens(node):
            for semantic_token in _semantic_tokens_for_raw_token(raw_token):
                key = (semantic_token.line, semantic_token.start, semantic_token.length, semantic_token.token_type)
                if key in seen:
                    continue
                seen.add(key)
                result.append(semantic_token)
    return result


def _iter_nodes(node):
    yield node
    for section in getattr(node, "sections", []) or []:
        yield from _iter_nodes(section)
    for child in getattr(node, "body", []) or []:
        yield from _iter_nodes(child)


def _node_tokens(node) -> list:
    tokens = list(getattr(node, "tokens", []) or [])
    header = getattr(node, "header", None)
    if header is not None:
        tokens.extend(getattr(header, "tokens", []) or [])
    return tokens


def _semantic_token_type(raw_token) -> str | None:
    token_type = raw_token.type
    if token_type in {Token.SEPARATOR, Token.EOL, Token.EOS, Token.CONTINUATION}:
        return None
    if token_type == Token.COMMENT:
        return "comment"
    if token_type in _header_tokens():
        return "header"
    if token_type in _setting_tokens():
        return "setting"
    if token_type == Token.NAME:
        return "name"
    if token_type == Token.KEYWORD_NAME:
        return "keywordNameDefinition"
    if token_type == Token.TESTCASE_NAME:
        return "testCaseName"
    if token_type == Token.KEYWORD:
        return "keywordNameCall"
    if token_type == Token.ARGUMENT:
        return "argumentValue"
    if token_type in {Token.VARIABLE, Token.ASSIGN}:
        return "variable"
    if token_type in _control_tokens():
        return "control"
    if token_type in {Token.ERROR, Token.FATAL_ERROR}:
        return "error"
    return None


def _semantic_tokens_for_raw_token(raw_token) -> list[SemanticToken]:
    token_type = _semantic_token_type(raw_token)
    if token_type is None:
        return []
    value = raw_token.value or ""
    line = max(0, (raw_token.lineno or 1) - 1)
    start = raw_token.col_offset or 0
    if token_type == "setting" and value.startswith("[") and value.endswith("]") and len(value) > 2:
        return [
            SemanticToken(line=line, start=start, length=1, token_type="settingOperator"),
            SemanticToken(line=line, start=start + 1, length=_utf16_len(value[1:-1]), token_type="setting"),
            SemanticToken(line=line, start=start + _utf16_len(value[:-1]), length=1, token_type="settingOperator"),
        ]
    if token_type == "argumentValue":
        named_argument_tokens = _split_named_argument_tokens(value, line=line, start=start)
        if named_argument_tokens is not None:
            return named_argument_tokens
    if token_type in {"argumentValue", "variable"}:
        return _split_variable_tokens(value, line=line, start=start, fallback_token_type=token_type)
    return [SemanticToken(line=line, start=start, length=_utf16_len(value), token_type=token_type)]


def _split_named_argument_tokens(value: str, *, line: int, start: int) -> list[SemanticToken] | None:
    split_index = _find_unescaped_equal(value)
    if split_index is None or split_index == 0:
        return None
    name = value[:split_index]
    argument_value = value[split_index + 1 :]
    value_start = start + _utf16_len(value[: split_index + 1])
    result = [
        *_split_variable_tokens(name, line=line, start=start, fallback_token_type="parameterName"),
        SemanticToken(
            line=line,
            start=start + _utf16_len(value[:split_index]),
            length=1,
            token_type="variableOperator",
        ),
    ]
    if argument_value:
        result.extend(
            _split_variable_tokens(
                argument_value,
                line=line,
                start=value_start,
                fallback_token_type="argumentValue",
            )
        )
    return [token for token in result if token.length > 0]


def _split_variable_tokens(value: str, *, line: int, start: int, fallback_token_type: str) -> list[SemanticToken]:
    result: list[SemanticToken] = []
    current = 0
    for match in _VARIABLE_RE.finditer(value):
        if match.start() > current and fallback_token_type in {"argumentValue", "parameterName"}:
            result.append(
                SemanticToken(
                    line=line,
                    start=start + _utf16_len(value[:current]),
                    length=_utf16_len(value[current : match.start()]),
                    token_type=fallback_token_type,
                )
            )
        variable = match.group(0)
        variable_start = start + _utf16_len(value[: match.start()])
        result.extend(
            [
                SemanticToken(line=line, start=variable_start, length=2, token_type="variableOperator"),
                SemanticToken(line=line, start=variable_start + 2, length=_utf16_len(variable[2:-1]), token_type="variable"),
                SemanticToken(line=line, start=variable_start + _utf16_len(variable[:-1]), length=1, token_type="variableOperator"),
            ]
        )
        current = match.end()
    if current < len(value) and fallback_token_type in {"argumentValue", "parameterName"}:
        result.append(
            SemanticToken(
                line=line,
                start=start + _utf16_len(value[:current]),
                length=_utf16_len(value[current:]),
                token_type=fallback_token_type,
            )
        )
    if result:
        return [token for token in result if token.length > 0]
    return [SemanticToken(line=line, start=start, length=_utf16_len(value), token_type=fallback_token_type)]


def _find_unescaped_equal(value: str) -> int | None:
    for index, character in enumerate(value):
        if character == "=" and not _is_escaped(value, index):
            return index
    return None


def _is_escaped(value: str, index: int) -> bool:
    slash_count = 0
    cursor = index - 1
    while cursor >= 0 and value[cursor] == "\\":
        slash_count += 1
        cursor -= 1
    return slash_count % 2 == 1


def _header_tokens() -> set[str]:
    names = [
        "HEADER",
        "SETTING_HEADER",
        "VARIABLE_HEADER",
        "TESTCASE_HEADER",
        "TASK_HEADER",
        "KEYWORD_HEADER",
        "COMMENT_HEADER",
        "INVALID_HEADER",
    ]
    return {value for name in names if isinstance(value := getattr(Token, name, None), str)}


def _setting_tokens() -> set[str]:
    names = [
        "SETTING",
        "LIBRARY",
        "RESOURCE",
        "VARIABLES",
        "DOCUMENTATION",
        "METADATA",
        "SUITE_SETUP",
        "SUITE_TEARDOWN",
        "TEST_SETUP",
        "TEST_TEARDOWN",
        "TEST_TEMPLATE",
        "TEST_TIMEOUT",
        "TEST_TAGS",
        "FORCE_TAGS",
        "DEFAULT_TAGS",
        "TAGS",
        "SETUP",
        "TEARDOWN",
        "TEMPLATE",
        "TIMEOUT",
        "ARGUMENTS",
        "RETURN",
    ]
    return {value for name in names if isinstance(value := getattr(Token, name, None), str)}


def _control_tokens() -> set[str]:
    names = [
        "FOR",
        "FOR_SEPARATOR",
        "END",
        "IF",
        "ELSE_IF",
        "ELSE",
        "TRY",
        "EXCEPT",
        "FINALLY",
        "WHILE",
        "BREAK",
        "CONTINUE",
        "RETURN_STATEMENT",
        "GROUP",
    ]
    return {value for name in names if isinstance(value := getattr(Token, name, None), str)}


def _utf16_len(text: str) -> int:
    return sum(1 if ord(ch) < 0x10000 else 2 for ch in text)
