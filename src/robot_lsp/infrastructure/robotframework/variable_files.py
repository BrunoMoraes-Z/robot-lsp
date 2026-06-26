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
                    variables.append(_robot_variable(target.id, value, _node_range(node)))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            value = _literal_value(node.value)
            if value is not None:
                variables.append(_robot_variable(node.target.id, value, _node_range(node)))
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
    return [_robot_variable(str(name), value, _ZERO_RANGE) for name, value in contents.items()]


def has_yaml_support() -> bool:
    return importlib.util.find_spec("yaml") is not None


def _variables_from_get_variables(node: ast.FunctionDef) -> list[RobotVariable]:
    variables: list[RobotVariable] = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Return):
            continue
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
