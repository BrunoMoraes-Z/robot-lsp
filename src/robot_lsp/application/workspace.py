from __future__ import annotations

import ast
import hashlib
import importlib.util
import threading
from dataclasses import dataclass
from pathlib import Path

from robot_lsp.domain.models import LspPosition, LspRange, RobotImport, RobotSuite, RobotVariable
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser
from robot_lsp.infrastructure.robotframework.variable_files import parse_python_variable_file, parse_yaml_variable_file

from .document_store import path_to_uri

_CACHE_MISSING: object = object()


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


@dataclass(frozen=True)
class VariableFileEntry:
    path: Path
    variables: list[RobotVariable]
    mtime: float
    content_hash: str


class WorkspaceIndex:
    SUPPORTED_SUFFIXES = {".robot", ".resource"}
    SUPPORTED_VARIABLE_FILE_SUFFIXES = {".py", ".yaml", ".yml"}

    def __init__(self, parser: RobotFrameworkParser | None = None, import_paths: list[Path] | None = None) -> None:
        self._parser = parser or RobotFrameworkParser()
        self._entries: dict[str, WorkspaceEntry] = {}
        self._import_paths = tuple(path.resolve() for path in import_paths or [])
        self._lock = threading.RLock()
        self._library_keywords_cache: dict[str, list[str] | None] = {}
        self._library_keyword_locations_cache: dict[str, list[SymbolLocation] | None] = {}
        self._variable_file_cache: dict[str, VariableFileEntry] = {}

    @property
    def entries(self) -> dict[str, WorkspaceEntry]:
        with self._lock:
            return dict(self._entries)

    @property
    def import_paths(self) -> tuple[Path, ...]:
        return self._import_paths

    def set_import_paths(self, import_paths: list[Path] | tuple[Path, ...]) -> None:
        self._import_paths = tuple(path.resolve() for path in import_paths)

    def scan(self, root: Path) -> None:
        root = root.resolve()
        queue: list[Path] = []
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in self.SUPPORTED_SUFFIXES:
                queue.append(path)

        visited: set[str] = set()
        while queue:
            path = queue.pop(0)
            uri = path_to_uri(path)
            if uri in visited:
                continue
            visited.add(uri)
            entry = self.update_file(path)
            if entry is None:
                continue
            for import_ in entry.suite.imports:
                if import_.type not in {"resource", "variables"}:
                    continue
                resolved = self._resolve_file_import(entry.path, import_)
                if resolved is not None and path_to_uri(resolved) not in visited:
                    queue.append(resolved)

    def update_file(self, path: Path) -> WorkspaceEntry | None:
        path = path.resolve()
        if not path.exists() or path.suffix.lower() not in self.SUPPORTED_SUFFIXES:
            return None

        text = path.read_text(encoding="utf-8")
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        uri = path_to_uri(path)
        with self._lock:
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
        with self._lock:
            self._entries[uri] = entry
        return entry

    def update_from_text(self, path: Path, text: str) -> WorkspaceEntry | None:
        """Index a file from in-memory text (e.g. an unsaved editor buffer)."""
        path = path.resolve()
        if path.suffix.lower() not in self.SUPPORTED_SUFFIXES:
            return None
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        uri = path_to_uri(path)
        with self._lock:
            existing = self._entries.get(uri)
        if existing is not None and existing.content_hash == content_hash:
            return existing
        result = self._parser.parse_text(text, source_name=path.name)
        if result.suite is None:
            return None
        entry = WorkspaceEntry(uri=uri, path=path, suite=result.suite, mtime=0.0, content_hash=content_hash)
        with self._lock:
            self._entries[uri] = entry
        return entry

    def remove_file(self, path: Path) -> None:
        with self._lock:
            self._entries.pop(path_to_uri(path.resolve()), None)

    def find_keyword(self, name: str) -> list[SymbolLocation]:
        with self._lock:
            entries = list(self._entries.values())
        return [
            SymbolLocation(
                name=keyword.name,
                uri=entry.uri,
                range=keyword.range,
                source_uri=entry.uri,
            )
            for entry in entries
            for keyword in entry.suite.keywords
            if keyword.name == name
        ]

    def find_variable(self, name: str) -> list[SymbolLocation]:
        with self._lock:
            entries = list(self._entries.values())
        return [
            SymbolLocation(
                name=variable.name,
                uri=entry.uri,
                range=variable.range,
                source_uri=entry.uri,
            )
            for entry in entries
            for variable in entry.suite.variables
            if variable.name == name
        ]

    def resolve_import(self, source_path: Path, import_: RobotImport) -> ImportResolution:
        resolved_path = None
        if import_.type in {"resource", "variables"}:
            resolved_path = self._resolve_file_import(source_path, import_)
        elif import_.type == "library":
            resolved_path = self._resolve_library_import(import_, source_path)

        return ImportResolution(
            import_=import_,
            resolved_path=resolved_path,
            resolved_uri=path_to_uri(resolved_path) if resolved_path is not None else None,
        )

    def imported_keyword_locations(self, source_path: Path, suite: RobotSuite) -> list[SymbolLocation]:
        locations: list[SymbolLocation] = []
        visited: set[str] = set()

        def _collect(path: Path, s: RobotSuite) -> None:
            for import_ in s.imports:
                if import_.type != "resource":
                    continue
                resolution = self.resolve_import(path, import_)
                if resolution.resolved_uri is None or resolution.resolved_uri in visited:
                    continue
                visited.add(resolution.resolved_uri)
                with self._lock:
                    entry = self._entries.get(resolution.resolved_uri)
                if entry is None and resolution.resolved_path is not None:
                    entry = self.update_file(resolution.resolved_path)
                if entry is None:
                    continue
                locations.extend(
                    SymbolLocation(keyword.name, entry.uri, keyword.range, resolution.resolved_uri)
                    for keyword in entry.suite.keywords
                )
                _collect(entry.path, entry.suite)

        _collect(source_path, suite)
        return locations

    def imported_variable_locations(self, source_path: Path, suite: RobotSuite) -> list[SymbolLocation]:
        locations: list[SymbolLocation] = []
        visited: set[str] = set()

        def _collect(path: Path, s: RobotSuite) -> None:
            for import_ in s.imports:
                if import_.type not in {"resource", "variables"}:
                    continue
                resolution = self.resolve_import(path, import_)
                if resolution.resolved_uri is None or resolution.resolved_uri in visited:
                    continue
                visited.add(resolution.resolved_uri)
                if resolution.resolved_path is not None and resolution.resolved_path.suffix.lower() in self.SUPPORTED_VARIABLE_FILE_SUFFIXES:
                    uri = path_to_uri(resolution.resolved_path)
                    locations.extend(
                        SymbolLocation(variable.name, uri, variable.range, uri)
                        for variable in self._load_variable_file(resolution.resolved_path)
                    )
                    continue
                with self._lock:
                    entry = self._entries.get(resolution.resolved_uri)
                if entry is None and resolution.resolved_path is not None:
                    entry = self.update_file(resolution.resolved_path)
                if entry is None:
                    continue
                locations.extend(
                    SymbolLocation(variable.name, entry.uri, variable.range, resolution.resolved_uri)
                    for variable in entry.suite.variables
                )
                if import_.type == "resource":
                    _collect(entry.path, entry.suite)

        _collect(source_path, suite)
        return locations

    def imported_variables(self, source_path: Path, suite: RobotSuite) -> list[RobotVariable]:
        variables: list[RobotVariable] = []
        visited: set[str] = set()

        def _collect(path: Path, s: RobotSuite) -> None:
            for import_ in s.imports:
                if import_.type not in {"resource", "variables"}:
                    continue
                resolution = self.resolve_import(path, import_)
                if resolution.resolved_uri is None or resolution.resolved_uri in visited:
                    continue
                visited.add(resolution.resolved_uri)
                if resolution.resolved_path is not None and resolution.resolved_path.suffix.lower() in self.SUPPORTED_VARIABLE_FILE_SUFFIXES:
                    variables.extend(self._load_variable_file(resolution.resolved_path))
                    continue
                with self._lock:
                    entry = self._entries.get(resolution.resolved_uri)
                if entry is None and resolution.resolved_path is not None:
                    entry = self.update_file(resolution.resolved_path)
                if entry is None:
                    continue
                variables.extend(entry.suite.variables)
                if import_.type == "resource":
                    _collect(entry.path, entry.suite)

        _collect(source_path, suite)
        return variables

    def _load_variable_file(self, path: Path) -> list[RobotVariable]:
        path = path.resolve()
        if not path.exists() or path.suffix.lower() not in self.SUPPORTED_VARIABLE_FILE_SUFFIXES:
            return []

        try:
            content = path.read_bytes()
            mtime = path.stat().st_mtime
        except OSError:
            return []
        content_hash = hashlib.sha256(content).hexdigest()
        key = str(path)
        with self._lock:
            cached = self._variable_file_cache.get(key)
        if cached is not None and cached.content_hash == content_hash and cached.mtime == mtime:
            return cached.variables

        suffix = path.suffix.lower()
        if suffix == ".py":
            variables = parse_python_variable_file(path)
        elif suffix in {".yaml", ".yml"}:
            variables = parse_yaml_variable_file(path)
        else:
            variables = []
        entry = VariableFileEntry(path=path, variables=variables, mtime=mtime, content_hash=content_hash)
        with self._lock:
            self._variable_file_cache[key] = entry
        return variables

    def imported_library_keywords(
        self, source_path: Path, suite: RobotSuite
    ) -> tuple[list[str], bool]:
        """Return (keyword_names, has_unresolvable_library) for all libraries in the import chain.

        Traverses resource imports transitively so that libraries declared in hub resource files
        (e.g. main.resource) are visible in test files that import that hub.
        has_unresolvable_library is True when at least one library could not be introspected,
        which callers use to suppress false-positive keyword diagnostics.
        """
        names: list[str] = []
        has_unloadable = False
        seen_lib_keys: set[str] = set()
        visited_resources: set[str] = set()

        def _collect_libs(path: Path, s: RobotSuite) -> None:
            nonlocal has_unloadable
            for import_ in s.imports:
                if import_.type == "library":
                    result = self._get_library_keywords(import_, path)
                    key = self._library_cache_key(import_, path)
                    if key not in seen_lib_keys:
                        seen_lib_keys.add(key)
                        if result is None:
                            has_unloadable = True
                        else:
                            names.extend(result)
                elif import_.type == "resource":
                    resolution = self.resolve_import(path, import_)
                    if resolution.resolved_uri is None or resolution.resolved_uri in visited_resources:
                        continue
                    visited_resources.add(resolution.resolved_uri)
                    with self._lock:
                        entry = self._entries.get(resolution.resolved_uri)
                    if entry is None and resolution.resolved_path is not None:
                        entry = self.update_file(resolution.resolved_path)
                    if entry is None:
                        continue
                    _collect_libs(entry.path, entry.suite)

        _collect_libs(source_path, suite)
        return names, has_unloadable

    def imported_library_keyword_locations(
        self,
        source_path: Path,
        suite: RobotSuite,
    ) -> tuple[list[SymbolLocation], bool]:
        locations: list[SymbolLocation] = []
        has_unloadable = False
        seen_lib_keys: set[str] = set()
        visited_resources: set[str] = set()

        def _collect_libs(path: Path, s: RobotSuite) -> None:
            nonlocal has_unloadable
            for import_ in s.imports:
                if import_.type == "library":
                    key = self._library_cache_key(import_, path)
                    if key in seen_lib_keys:
                        continue
                    seen_lib_keys.add(key)
                    result = self._get_library_keyword_locations(import_, path)
                    if result is None:
                        has_unloadable = True
                    else:
                        locations.extend(result)
                elif import_.type == "resource":
                    resolution = self.resolve_import(path, import_)
                    if resolution.resolved_uri is None or resolution.resolved_uri in visited_resources:
                        continue
                    visited_resources.add(resolution.resolved_uri)
                    with self._lock:
                        entry = self._entries.get(resolution.resolved_uri)
                    if entry is None and resolution.resolved_path is not None:
                        entry = self.update_file(resolution.resolved_path)
                    if entry is None:
                        continue
                    _collect_libs(entry.path, entry.suite)

        _collect_libs(source_path, suite)
        return locations, has_unloadable

    def _library_cache_key(self, import_: RobotImport, source_path: Path | None) -> str:
        resolved = self._resolve_library_import(import_, source_path)
        return str(resolved) if resolved is not None else import_.name

    def _get_library_keywords(self, import_: RobotImport, source_path: Path | None = None) -> list[str] | None:
        """Return keyword names for a library, loading via RF libdoc. Cached per resolved path."""
        key = self._library_cache_key(import_, source_path)
        with self._lock:
            cached = self._library_keywords_cache.get(key, _CACHE_MISSING)
        if cached is not _CACHE_MISSING:
            return cached  # type: ignore[return-value]

        resolved = self._resolve_library_import(import_, source_path)
        target = str(resolved) if resolved is not None else import_.name
        names = _load_library_keywords(target)
        with self._lock:
            self._library_keywords_cache[key] = names
        return names

    def _get_library_keyword_locations(
        self, import_: RobotImport, source_path: Path | None = None
    ) -> list[SymbolLocation] | None:
        key = self._library_cache_key(import_, source_path)
        with self._lock:
            cached = self._library_keyword_locations_cache.get(key, _CACHE_MISSING)
        if cached is not _CACHE_MISSING:
            return cached  # type: ignore[return-value]

        resolved = self._resolve_library_import(import_, source_path)
        target = str(resolved) if resolved is not None else import_.name
        locations = _load_library_keyword_locations(target)
        with self._lock:
            self._library_keyword_locations_cache[key] = locations
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
            if import_.type == "variables" and candidate.suffix == "":
                for suffix in (".robot", ".resource", ".py", ".yaml", ".yml"):
                    with_suffix = candidate.with_suffix(suffix)
                    if with_suffix.exists():
                        return with_suffix
        return None

    def _resolve_library_import(self, import_: RobotImport, source_path: Path | None = None) -> Path | None:
        name = import_.name
        if _is_path_import(name):
            bases = [source_path.parent] if source_path is not None else []
            bases.extend(self._import_paths)
            for base in bases:
                candidate = (base / name).resolve()
                if candidate.exists():
                    return candidate
            candidate = Path(name).resolve()
            return candidate if candidate.exists() else None

        try:
            spec = importlib.util.find_spec(name)
        except (ImportError, ValueError, ModuleNotFoundError):
            return None
        if spec is None:
            try:
                spec = importlib.util.find_spec(f"robot.libraries.{name}")
            except (ImportError, ValueError, ModuleNotFoundError):
                return None
        if spec is None or spec.origin is None or spec.origin == "built-in":
            return None
        return Path(spec.origin).resolve()


def _load_library_keywords(target: str) -> list[str] | None:
    try:
        from robot.libdocpkg import LibraryDocumentation  # type: ignore[import]
        libdoc = LibraryDocumentation(target)
        return [kw.name for kw in libdoc.keywords]
    except Exception:
        return None


def _load_library_keyword_locations(target: str) -> list[SymbolLocation] | None:
    try:
        from robot.libdocpkg import LibraryDocumentation  # type: ignore[import]

        libdoc = LibraryDocumentation(target)
        locations: list[SymbolLocation] = []
        for keyword in libdoc.keywords:
            source = getattr(keyword, "source", None) or getattr(libdoc, "source", None)
            if not source:
                continue
            path = Path(source).resolve()
            lineno = getattr(keyword, "lineno", None)
            line = max(0, lineno - 1) if isinstance(lineno, int) and lineno > 0 else 0
            range_ = _python_keyword_range(path, line, keyword.name)
            uri = path_to_uri(path)
            locations.append(SymbolLocation(keyword.name, uri, range_, uri))
        return locations
    except Exception:
        return None


def _python_keyword_range(path: Path, line: int, keyword_name: str) -> LspRange:
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return LspRange(LspPosition(line, 0), LspPosition(line, 0))

    normalized_keyword = _normalize_robot_name(keyword_name)
    fallback = LspRange(LspPosition(line, 0), LspPosition(line, 0))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        node_line = max(0, getattr(node, "lineno", 1) - 1)
        node_range = LspRange(
            LspPosition(node_line, getattr(node, "col_offset", 0) + 4),
            LspPosition(node_line, getattr(node, "col_offset", 0) + 4 + len(node.name)),
        )
        if node_line == line:
            return node_range
        decorator_name = _robot_keyword_decorator_name(node)
        if decorator_name is not None and _normalize_robot_name(decorator_name) == normalized_keyword:
            return node_range
        if _normalize_robot_name(node.name) == normalized_keyword:
            fallback = node_range
    return fallback


def _robot_keyword_decorator_name(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        function = decorator.func
        function_name = function.id if isinstance(function, ast.Name) else getattr(function, "attr", None)
        if function_name != "keyword":
            continue
        for arg in decorator.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return arg.value
        for keyword in decorator.keywords:
            if keyword.arg == "name" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                return keyword.value.value
    return None


def _normalize_robot_name(name: str) -> str:
    return "".join(char for char in name.casefold() if char not in " _")


def _is_path_import(name: str) -> bool:
    return (
        name.endswith(".py")
        or name.startswith(".")
        or "/" in name
        or "\\" in name
    )
