from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from typing import Any

from robot_lsp.domain.models import LspPosition, LspRange, RobotVariable


_ZERO_RANGE = LspRange(LspPosition(0, 0), LspPosition(0, 0))


def parse_python_variable_file(path: Path) -> list[RobotVariable]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    variables: list[RobotVariable] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            value = _literal_value(node.value)
            if value is None:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    variables.append(_robot_variable(target.id, value, _node_name_range(target)))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            value = _literal_value(node.value)
            if value is not None:
                variables.append(_robot_variable(node.target.id, value, _node_name_range(node.target)))
        elif isinstance(node, ast.FunctionDef) and node.name in {"get_variables", "getVariables"}:
            variables.extend(_variables_from_get_variables(node))
    return variables


def parse_yaml_variable_file(path: Path) -> list[RobotVariable]:
    try:
        import yaml
    except ImportError:
        return []

    try:
        with path.open("r", encoding="utf-8") as stream:
            contents = yaml.safe_load(stream)
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return []
    if not isinstance(contents, dict):
        return []
    ranges = _yaml_key_ranges(path)
    return [_robot_variable(str(name), value, ranges.get(str(name), _ZERO_RANGE)) for name, value in contents.items()]


def has_yaml_support() -> bool:
    return importlib.util.find_spec("yaml") is not None


def _variables_from_get_variables(node: ast.FunctionDef) -> list[RobotVariable]:
    variables: list[RobotVariable] = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Return):
            continue
        if isinstance(child.value, ast.Dict):
            for key_node, value_node in zip(child.value.keys, child.value.values):
                key = _literal_value(key_node)
                value = _literal_value(value_node)
                if key is not None and value is not None:
                    variables.append(_robot_variable(str(key), value, _node_range(key_node)))
            break
        value = _literal_value(child.value)
        if not isinstance(value, dict):
            continue
        for name, item in value.items():
            variables.append(_robot_variable(str(name), item, _node_range(child)))
        break
    return variables


def _literal_value(node: ast.AST | None) -> Any | None:
    if node is None:
        return None
    try:
        return _normalize_value(ast.literal_eval(node))
    except (ValueError, TypeError):
        return None


def _robot_variable(name: str, value: Any, range_: LspRange) -> RobotVariable:
    name = _strip_robot_variable_prefix(name)
    value = _normalize_value(value)
    return RobotVariable(
        name=f"${{{name}}}",
        value=value,
        kind=_variable_kind(value),
        range=range_,
    )


def _strip_robot_variable_prefix(name: str) -> str:
    if len(name) >= 4 and name[1] == "{" and name.endswith("}") and name[0] in "$@&%":
        return name[2:-1]
    if name.startswith(("DICT__", "LIST__")):
        return name[6:]
    return name


def _variable_kind(value: Any):
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, list):
        return "list"
    return "scalar"


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    return value


def _node_range(node: ast.AST) -> LspRange:
    lineno = max(0, getattr(node, "lineno", 1) - 1)
    col = getattr(node, "col_offset", 0)
    end_lineno = max(0, getattr(node, "end_lineno", lineno + 1) - 1)
    end_col = getattr(node, "end_col_offset", col)
    return LspRange(LspPosition(lineno, col), LspPosition(end_lineno, end_col))


def _node_name_range(node: ast.Name) -> LspRange:
    lineno = max(0, getattr(node, "lineno", 1) - 1)
    col = getattr(node, "col_offset", 0)
    return LspRange(LspPosition(lineno, col), LspPosition(lineno, col + len(node.id)))


def _yaml_key_ranges(path: Path) -> dict[str, LspRange]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return {}

    ranges: dict[str, LspRange] = {}
    for line_number, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#") or len(stripped) != len(line):
            continue
        separator = stripped.find(":")
        if separator <= 0:
            continue
        key = stripped[:separator].strip().strip('"\'')
        if not key:
            continue
        start = line.find(stripped[:separator])
        start = max(0, start)
        end = start + len(stripped[:separator])
        ranges[key] = LspRange(LspPosition(line_number, start), LspPosition(line_number, end))
    return ranges
