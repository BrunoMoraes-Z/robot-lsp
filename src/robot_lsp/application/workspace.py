from __future__ import annotations

import hashlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path

from robot_lsp.domain.models import LspRange, RobotImport, RobotSuite
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser

from .document_store import path_to_uri


@dataclass(frozen=True)
class SymbolLocation:
    name: str
    uri: str
    range: LspRange
    source_uri: str

    def to_lsp(self) -> dict:
        return {
            "uri": self.uri,
            "range": {
                "start": {
                    "line": self.range.start.line,
                    "character": self.range.start.character,
                },
                "end": {
                    "line": self.range.end.line,
                    "character": self.range.end.character,
                },
            },
        }


@dataclass(frozen=True)
class ImportResolution:
    import_: RobotImport
    resolved_uri: str | None
    resolved_path: Path | None


@dataclass(frozen=True)
class WorkspaceEntry:
    uri: str
    path: Path
    suite: RobotSuite
    mtime: float
    content_hash: str


class WorkspaceIndex:
    SUPPORTED_SUFFIXES = {".robot", ".resource"}

    def __init__(self, parser: RobotFrameworkParser | None = None, import_paths: list[Path] | None = None) -> None:
        self._parser = parser or RobotFrameworkParser()
        self._entries: dict[str, WorkspaceEntry] = {}
        self._import_paths = tuple(path.resolve() for path in import_paths or [])

    @property
    def entries(self) -> dict[str, WorkspaceEntry]:
        return dict(self._entries)

    @property
    def import_paths(self) -> tuple[Path, ...]:
        return self._import_paths

    def set_import_paths(self, import_paths: list[Path] | tuple[Path, ...]) -> None:
        self._import_paths = tuple(path.resolve() for path in import_paths)

    def scan(self, root: Path) -> None:
        root = root.resolve()
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in self.SUPPORTED_SUFFIXES:
                self.update_file(path)

    def update_file(self, path: Path) -> WorkspaceEntry | None:
        path = path.resolve()
        if not path.exists() or path.suffix.lower() not in self.SUPPORTED_SUFFIXES:
            return None

        text = path.read_text(encoding="utf-8")
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        uri = path_to_uri(path)
        existing = self._entries.get(uri)
        mtime = path.stat().st_mtime
        if existing is not None and existing.content_hash == content_hash and existing.mtime == mtime:
            return existing

        result = self._parser.parse_file(path)
        if result.suite is None:
            return None
        entry = WorkspaceEntry(
            uri=uri,
            path=path,
            suite=result.suite,
            mtime=mtime,
            content_hash=content_hash,
        )
        self._entries[uri] = entry
        return entry

    def remove_file(self, path: Path) -> None:
        self._entries.pop(path_to_uri(path.resolve()), None)

    def find_keyword(self, name: str) -> list[SymbolLocation]:
        return [
            SymbolLocation(
                name=keyword.name,
                uri=entry.uri,
                range=keyword.range,
                source_uri=entry.uri,
            )
            for entry in self._entries.values()
            for keyword in entry.suite.keywords
            if keyword.name == name
        ]

    def find_variable(self, name: str) -> list[SymbolLocation]:
        return [
            SymbolLocation(
                name=variable.name,
                uri=entry.uri,
                range=variable.range,
                source_uri=entry.uri,
            )
            for entry in self._entries.values()
            for variable in entry.suite.variables
            if variable.name == name
        ]

    def resolve_import(self, source_path: Path, import_: RobotImport) -> ImportResolution:
        resolved_path = None
        if import_.type in {"resource", "variables"}:
            resolved_path = self._resolve_file_import(source_path, import_)
        elif import_.type == "library":
            resolved_path = self._resolve_library_import(import_)

        return ImportResolution(
            import_=import_,
            resolved_path=resolved_path,
            resolved_uri=path_to_uri(resolved_path) if resolved_path is not None else None,
        )

    def imported_keyword_locations(self, source_path: Path, suite: RobotSuite) -> list[SymbolLocation]:
        locations: list[SymbolLocation] = []
        for import_ in suite.imports:
            if import_.type != "resource":
                continue
            resolution = self.resolve_import(source_path, import_)
            if resolution.resolved_uri is None:
                continue
            entry = self._entries.get(resolution.resolved_uri)
            if entry is None:
                continue
            locations.extend(
                SymbolLocation(keyword.name, entry.uri, keyword.range, resolution.resolved_uri)
                for keyword in entry.suite.keywords
            )
        return locations

    def imported_variable_locations(self, source_path: Path, suite: RobotSuite) -> list[SymbolLocation]:
        locations: list[SymbolLocation] = []
        for import_ in suite.imports:
            if import_.type != "resource":
                continue
            resolution = self.resolve_import(source_path, import_)
            if resolution.resolved_uri is None:
                continue
            entry = self._entries.get(resolution.resolved_uri)
            if entry is None:
                continue
            locations.extend(
                SymbolLocation(variable.name, entry.uri, variable.range, resolution.resolved_uri)
                for variable in entry.suite.variables
            )
        return locations

    def _resolve_file_import(self, source_path: Path, import_: RobotImport) -> Path | None:
        for base_path in (source_path.parent, *self._import_paths):
            candidate = (base_path / import_.name).resolve()
            if candidate.exists():
                return candidate
            if import_.type == "resource" and candidate.suffix == "":
                for suffix in (".resource", ".robot"):
                    with_suffix = candidate.with_suffix(suffix)
                    if with_suffix.exists():
                        return with_suffix
        return None

    def _resolve_library_import(self, import_: RobotImport) -> Path | None:
        spec = importlib.util.find_spec(import_.name)
        if spec is None:
            spec = importlib.util.find_spec(f"robot.libraries.{import_.name}")
        if spec is None or spec.origin is None or spec.origin == "built-in":
            return None
        return Path(spec.origin).resolve()
