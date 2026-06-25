from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

from robot_lsp.application.document_store import uri_to_path


LogLevel = Literal["debug", "info", "warning", "error"]


@dataclass(frozen=True)
class DiagnosticsConfig:
    enable: bool = True


@dataclass(frozen=True)
class CompletionConfig:
    snippets: bool = True


@dataclass(frozen=True)
class ServerConfig:
    import_paths: tuple[Path, ...] = field(default_factory=tuple)
    log_level: LogLevel = "info"
    diagnostics: DiagnosticsConfig = field(default_factory=DiagnosticsConfig)
    completion: CompletionConfig = field(default_factory=CompletionConfig)
    variables: dict[str, str] = field(default_factory=dict)


class ConfigurationService:
    def __init__(self, config: ServerConfig | None = None) -> None:
        self._config = config or ServerConfig()
        self._workspace_settings: dict[str, dict[str, Any]] = {}

    @property
    def config(self) -> ServerConfig:
        return self._config

    def update(self, raw: dict[str, Any] | None, *, scope_uri: str | None = None) -> ServerConfig:
        current = self.config_for_uri(scope_uri) if scope_uri is not None else self._config
        if raw is None:
            return current
        settings = _robot_lsp_settings(raw)
        if not settings:
            return current

        if scope_uri is not None:
            workspace_settings = _merge_settings(self._workspace_settings.get(scope_uri, {}), settings)
            self._workspace_settings[scope_uri] = workspace_settings
            return _apply_settings(self._config, workspace_settings)

        self._config = _apply_settings(self._config, settings)
        return self._config

    def config_for_uri(self, uri: str | None) -> ServerConfig:
        if uri is None:
            return self._config
        scope_uri = self._matching_scope_uri(uri)
        if scope_uri is None:
            return self._config
        return _apply_settings(self._config, self._workspace_settings[scope_uri])

    def _matching_scope_uri(self, uri: str) -> str | None:
        path = uri_to_path(uri)
        best_scope_uri = None
        best_length = -1
        for scope_uri in self._workspace_settings:
            scope_path = uri_to_path(scope_uri)
            if path is not None and scope_path is not None:
                try:
                    path.relative_to(scope_path)
                except ValueError:
                    continue
                scope_length = len(str(scope_path))
            elif uri.startswith(scope_uri):
                scope_length = len(scope_uri)
            else:
                continue
            if scope_length > best_length:
                best_scope_uri = scope_uri
                best_length = scope_length
        return best_scope_uri


def _apply_settings(config: ServerConfig, settings: dict[str, Any]) -> ServerConfig:
    import_paths = config.import_paths
    raw_import_paths = settings.get("importPaths")
    if isinstance(raw_import_paths, list):
        import_paths = tuple(Path(item).expanduser() for item in raw_import_paths if isinstance(item, str) and item)

    log_level = config.log_level
    raw_log_level = settings.get("logLevel")
    if raw_log_level in {"debug", "info", "warning", "error"}:
        log_level = raw_log_level

    diagnostics = config.diagnostics
    raw_diagnostics = settings.get("diagnostics")
    if isinstance(raw_diagnostics, dict) and isinstance(raw_diagnostics.get("enable"), bool):
        diagnostics = replace(diagnostics, enable=raw_diagnostics["enable"])

    completion = config.completion
    raw_completion = settings.get("completion")
    if isinstance(raw_completion, dict) and isinstance(raw_completion.get("snippets"), bool):
        completion = replace(completion, snippets=raw_completion["snippets"])

    variables = config.variables
    raw_variables = settings.get("variables")
    if isinstance(raw_variables, dict):
        variables = {str(key): str(value) for key, value in raw_variables.items() if key and value is not None}

    return ServerConfig(
        import_paths=import_paths,
        log_level=log_level,
        diagnostics=diagnostics,
        completion=completion,
        variables=variables,
    )


def _merge_settings(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def _robot_lsp_settings(raw: dict[str, Any]) -> dict[str, Any]:
    if _has_known_keys(raw):
        return raw
    robot = raw.get("robot")
    if isinstance(robot, dict):
        lsp = robot.get("lsp")
        if isinstance(lsp, dict):
            return lsp
    lsp = raw.get("robot.lsp")
    if isinstance(lsp, dict):
        return lsp
    return {}


def _has_known_keys(raw: dict[str, Any]) -> bool:
    return any(key in raw for key in ["importPaths", "logLevel", "diagnostics", "completion", "variables"])
