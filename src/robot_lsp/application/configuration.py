from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal


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


class ConfigurationService:
    def __init__(self, config: ServerConfig | None = None) -> None:
        self._config = config or ServerConfig()

    @property
    def config(self) -> ServerConfig:
        return self._config

    def update(self, raw: dict[str, Any] | None) -> ServerConfig:
        if raw is None:
            return self._config
        settings = _robot_lsp_settings(raw)
        if not settings:
            return self._config

        import_paths = self._config.import_paths
        raw_import_paths = settings.get("importPaths")
        if isinstance(raw_import_paths, list):
            import_paths = tuple(Path(item).expanduser() for item in raw_import_paths if isinstance(item, str) and item)

        log_level = self._config.log_level
        raw_log_level = settings.get("logLevel")
        if raw_log_level in {"debug", "info", "warning", "error"}:
            log_level = raw_log_level

        diagnostics = self._config.diagnostics
        raw_diagnostics = settings.get("diagnostics")
        if isinstance(raw_diagnostics, dict) and isinstance(raw_diagnostics.get("enable"), bool):
            diagnostics = replace(diagnostics, enable=raw_diagnostics["enable"])

        completion = self._config.completion
        raw_completion = settings.get("completion")
        if isinstance(raw_completion, dict) and isinstance(raw_completion.get("snippets"), bool):
            completion = replace(completion, snippets=raw_completion["snippets"])

        self._config = ServerConfig(
            import_paths=import_paths,
            log_level=log_level,
            diagnostics=diagnostics,
            completion=completion,
        )
        return self._config


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
    return any(key in raw for key in ["importPaths", "logLevel", "diagnostics", "completion"])
