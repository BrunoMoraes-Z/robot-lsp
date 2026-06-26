from pathlib import Path

from robot_lsp.application.completion_service import CompletionService
from robot_lsp.application.document_store import DocumentStore, path_to_uri
from robot_lsp.application.navigation_service import NavigationService
from robot_lsp.application.parse_service import ParseService
from robot_lsp.application.workspace import WorkspaceIndex, _is_path_import
from robot_lsp.domain.models import LspPosition, LspRange, RobotImport
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser


def _dummy_import(name: str, type_: str = "library") -> RobotImport:
    dummy_range = LspRange(LspPosition(0, 0), LspPosition(0, len(name)))
    return RobotImport(type=type_, name=name, args=[], alias=None, range=dummy_range)  # type: ignore[arg-type]


def write_workspace(root: Path):
    main = root / "main.robot"
    resource = root / "keywords.resource"
    variables = root / "vars.robot"
    main.write_text(
        "*** Settings ***\n"
        "Resource    keywords.resource\n"
        "Variables   vars.robot\n"
        "Library     Collections\n"
        "\n"
        "*** Test Cases ***\n"
        "Case\n"
        "    Resource Keyword    ${RESOURCE_VAR}\n",
        encoding="utf-8",
    )
    resource.write_text(
        "*** Variables ***\n"
        "${RESOURCE_VAR}    value\n"
        "\n"
        "*** Keywords ***\n"
        "Resource Keyword\n"
        "    Log    from resource\n",
        encoding="utf-8",
    )
    variables.write_text("*** Variables ***\n${VAR_FILE_VALUE}    x\n", encoding="utf-8")
    return main, resource, variables


class TestWorkspaceIndex:
    def test_scan_indexes_robot_and_resource_files(self, tmp_path):
        main, resource, _variables = write_workspace(tmp_path)
        index = WorkspaceIndex()

        index.scan(tmp_path)

        assert path_to_uri(main.resolve()) in index.entries
        assert path_to_uri(resource.resolve()) in index.entries
        assert len(index.entries) == 3

    def test_find_keyword_and_variable(self, tmp_path):
        _main, _resource, _variables = write_workspace(tmp_path)
        index = WorkspaceIndex()
        index.scan(tmp_path)

        keywords = index.find_keyword("Resource Keyword")
        variables = index.find_variable("${RESOURCE_VAR}")

        assert len(keywords) == 1
        assert keywords[0].name == "Resource Keyword"
        assert len(variables) == 1
        assert variables[0].name == "${RESOURCE_VAR}"

    def test_resolve_resource_import(self, tmp_path):
        main, resource, _variables = write_workspace(tmp_path)
        index = WorkspaceIndex()
        index.scan(tmp_path)
        suite = index.entries[path_to_uri(main.resolve())].suite

        resolution = index.resolve_import(main, suite.imports[0])

        assert resolution.resolved_path == resource.resolve()
        assert resolution.resolved_uri == path_to_uri(resource.resolve())

    def test_resolve_variables_import(self, tmp_path):
        main, _resource, variables = write_workspace(tmp_path)
        index = WorkspaceIndex()
        index.scan(tmp_path)
        suite = index.entries[path_to_uri(main.resolve())].suite

        resolution = index.resolve_import(main, suite.imports[1])

        assert resolution.resolved_path == variables.resolve()

    def test_resolve_resource_import_from_configured_import_path(self, tmp_path):
        workspace = tmp_path / "workspace"
        resources = tmp_path / "resources"
        workspace.mkdir()
        resources.mkdir()
        main = workspace / "main.robot"
        resource = resources / "shared.resource"
        main.write_text("*** Settings ***\nResource    shared.resource\n", encoding="utf-8")
        resource.write_text("*** Keywords ***\nShared Keyword\n    Log    ok\n", encoding="utf-8")
        index = WorkspaceIndex(import_paths=[resources])
        index.update_file(main)
        suite = index.entries[path_to_uri(main.resolve())].suite

        resolution = index.resolve_import(main, suite.imports[0])

        assert resolution.resolved_path == resource.resolve()

    def test_resolve_library_import(self, tmp_path):
        main, _resource, _variables = write_workspace(tmp_path)
        index = WorkspaceIndex()
        index.scan(tmp_path)
        suite = index.entries[path_to_uri(main.resolve())].suite

        resolution = index.resolve_import(main, suite.imports[2])

        assert resolution.resolved_path is not None
        assert resolution.resolved_path.name == "Collections.py"

    def test_imported_keyword_locations(self, tmp_path):
        main, resource, _variables = write_workspace(tmp_path)
        index = WorkspaceIndex()
        index.scan(tmp_path)
        suite = index.entries[path_to_uri(main.resolve())].suite

        locations = index.imported_keyword_locations(main, suite)

        assert len(locations) == 1
        assert locations[0].name == "Resource Keyword"
        assert locations[0].uri == path_to_uri(resource.resolve())

    def test_imported_variable_locations(self, tmp_path):
        main, resource, variables = write_workspace(tmp_path)
        index = WorkspaceIndex()
        index.scan(tmp_path)
        suite = index.entries[path_to_uri(main.resolve())].suite

        locations = index.imported_variable_locations(main, suite)

        names = {loc.name for loc in locations}
        # variables from Resource import
        assert "${RESOURCE_VAR}" in names
        assert any(loc.uri == path_to_uri(resource.resolve()) for loc in locations if loc.name == "${RESOURCE_VAR}")
        # variables from Variables import
        assert "${VAR_FILE_VALUE}" in names

    def test_update_file_reuses_cache_when_unchanged(self, tmp_path):
        main, _resource, _variables = write_workspace(tmp_path)
        index = WorkspaceIndex()

        first = index.update_file(main)
        second = index.update_file(main)

        assert first is second

    def test_remove_file(self, tmp_path):
        main, _resource, _variables = write_workspace(tmp_path)
        index = WorkspaceIndex()
        index.scan(tmp_path)

        index.remove_file(main)

        assert path_to_uri(main.resolve()) not in index.entries


class TestWorkspaceIndexIntegration:
    def test_completion_includes_imported_resource_keyword(self, tmp_path):
        main, _resource, _variables = write_workspace(tmp_path)
        index = WorkspaceIndex()
        index.scan(tmp_path)
        store = DocumentStore()
        parser = RobotFrameworkParser()
        service = CompletionService(store, ParseService(store, parser), index)
        uri = path_to_uri(main.resolve())
        store.open(uri=uri, text=main.read_text(encoding="utf-8"), version=1, language_id="robotframework")

        completion = service.compute_completion(uri, LspPosition(line=7, character=4))

        assert completion is not None
        assert "Resource Keyword" in [item.label for item in completion.items]

    def test_definition_points_to_imported_resource_keyword(self, tmp_path):
        main, resource, _variables = write_workspace(tmp_path)
        index = WorkspaceIndex()
        index.scan(tmp_path)
        store = DocumentStore()
        parser = RobotFrameworkParser()
        service = NavigationService(store, ParseService(store, parser), index)
        uri = path_to_uri(main.resolve())
        store.open(uri=uri, text=main.read_text(encoding="utf-8"), version=1, language_id="robotframework")

        locations = service.definition(uri, LspPosition(line=7, character=8))

        assert len(locations) == 1
        assert locations[0]["uri"] == path_to_uri(resource.resolve())
        assert locations[0]["range"]["start"]["line"] == 4


class TestScanFollowsImports:
    def test_scan_indexes_resource_outside_root(self, tmp_path):
        workspace = tmp_path / "workspace"
        shared = tmp_path / "shared"
        workspace.mkdir()
        shared.mkdir()
        resource = shared / "shared.resource"
        resource.write_text("*** Keywords ***\nShared Keyword\n    Log    ok\n", encoding="utf-8")
        main = workspace / "main.robot"
        main.write_text("*** Settings ***\nResource    ../shared/shared.resource\n", encoding="utf-8")
        index = WorkspaceIndex()

        index.scan(workspace)

        assert path_to_uri(resource.resolve()) in index.entries

    def test_scan_follows_transitive_imports(self, tmp_path):
        workspace = tmp_path / "ws"
        external = tmp_path / "ext"
        workspace.mkdir()
        external.mkdir()
        deep = external / "deep.resource"
        deep.write_text("*** Keywords ***\nDeep Keyword\n    Log    deep\n", encoding="utf-8")
        middle = workspace / "middle.resource"
        middle.write_text("*** Settings ***\nResource    ../ext/deep.resource\n", encoding="utf-8")
        main = workspace / "main.robot"
        main.write_text("*** Settings ***\nResource    middle.resource\n", encoding="utf-8")
        index = WorkspaceIndex()

        index.scan(workspace)

        assert path_to_uri(deep.resolve()) in index.entries


class TestLazyLoadingImports:
    def test_imported_keyword_locations_lazy_loads_unindexed_file(self, tmp_path):
        shared = tmp_path / "shared"
        shared.mkdir()
        resource = shared / "kw.resource"
        resource.write_text("*** Keywords ***\nExternal Keyword\n    Log    hi\n", encoding="utf-8")
        tests = tmp_path / "tests"
        tests.mkdir()
        suite = tests / "suite.robot"
        suite.write_text("*** Settings ***\nResource    ../shared/kw.resource\n", encoding="utf-8")

        index = WorkspaceIndex()
        index.update_file(suite)
        entry = index.entries[path_to_uri(suite.resolve())]

        # resource is NOT in the index yet (scan was never called on shared/)
        assert path_to_uri(resource.resolve()) not in index.entries

        locations = index.imported_keyword_locations(suite, entry.suite)

        assert len(locations) == 1
        assert locations[0].name == "External Keyword"
        # and it was lazily indexed
        assert path_to_uri(resource.resolve()) in index.entries

    def test_imported_keyword_locations_transitive(self, tmp_path):
        # A imports B (hub), B imports C (has keywords) — A should see C's keywords
        c = tmp_path / "c.resource"
        c.write_text("*** Keywords ***\nDeep Keyword\n    Log    deep\n", encoding="utf-8")
        b = tmp_path / "b.resource"
        b.write_text("*** Settings ***\nResource    c.resource\n", encoding="utf-8")
        a = tmp_path / "a.robot"
        a.write_text("*** Settings ***\nResource    b.resource\n", encoding="utf-8")

        index = WorkspaceIndex()
        index.scan(tmp_path)
        entry = index.entries[path_to_uri(a.resolve())]

        locations = index.imported_keyword_locations(a, entry.suite)

        assert any(loc.name == "Deep Keyword" for loc in locations)

    def test_imported_keyword_locations_circular_safe(self, tmp_path):
        # A imports B, B imports A — must not recurse infinitely
        a = tmp_path / "a.resource"
        b = tmp_path / "b.resource"
        a.write_text("*** Settings ***\nResource    b.resource\n*** Keywords ***\nKw A\n    Log    a\n", encoding="utf-8")
        b.write_text("*** Settings ***\nResource    a.resource\n*** Keywords ***\nKw B\n    Log    b\n", encoding="utf-8")
        suite = tmp_path / "suite.robot"
        suite.write_text("*** Settings ***\nResource    a.resource\n", encoding="utf-8")

        index = WorkspaceIndex()
        index.scan(tmp_path)
        entry = index.entries[path_to_uri(suite.resolve())]

        locations = index.imported_keyword_locations(suite, entry.suite)
        names = {loc.name for loc in locations}

        assert "Kw A" in names
        assert "Kw B" in names

    def test_imported_variable_locations_handles_variables_import(self, tmp_path):
        var_file = tmp_path / "vars.resource"
        var_file.write_text("*** Variables ***\n${MY_VAR}    hello\n", encoding="utf-8")
        suite_file = tmp_path / "suite.robot"
        suite_file.write_text(
            "*** Settings ***\nVariables    vars.resource\n*** Test Cases ***\nT\n    Log    ${MY_VAR}\n",
            encoding="utf-8",
        )

        index = WorkspaceIndex()
        index.update_file(suite_file)
        entry = index.entries[path_to_uri(suite_file.resolve())]

        locations = index.imported_variable_locations(suite_file, entry.suite)

        assert any(loc.name == "${MY_VAR}" for loc in locations)

    def test_imported_variables_from_python_file_dict(self, tmp_path):
        var_file = tmp_path / "vars.py"
        var_file.write_text('USER = {"name": "Ana", "email": "ana@example.com"}\n', encoding="utf-8")
        suite_file = tmp_path / "suite.robot"
        suite_file.write_text("*** Settings ***\nVariables    vars.py\n", encoding="utf-8")
        index = WorkspaceIndex()
        index.update_file(suite_file)
        entry = index.entries[path_to_uri(suite_file.resolve())]

        variables = index.imported_variables(suite_file, entry.suite)

        assert len(variables) == 1
        assert variables[0].name == "${USER}"
        assert variables[0].kind == "dict"
        assert variables[0].value == {"name": "Ana", "email": "ana@example.com"}

    def test_imported_variables_from_python_get_variables(self, tmp_path):
        var_file = tmp_path / "vars.py"
        var_file.write_text(
            'def get_variables():\n    return {"USER": {"name": "Ana"}, "VALUE": "x"}\n',
            encoding="utf-8",
        )
        suite_file = tmp_path / "suite.robot"
        suite_file.write_text("*** Settings ***\nVariables    vars.py\n", encoding="utf-8")
        index = WorkspaceIndex()
        index.update_file(suite_file)
        entry = index.entries[path_to_uri(suite_file.resolve())]

        variables = index.imported_variables(suite_file, entry.suite)

        names = {variable.name: variable for variable in variables}
        assert names["${USER}"].kind == "dict"
        assert names["${USER}"].value == {"name": "Ana"}
        assert names["${VALUE}"].kind == "scalar"
        assert names["${VALUE}"].value == "x"

    def test_imported_variables_from_python_ignores_dynamic_values(self, tmp_path):
        var_file = tmp_path / "vars.py"
        var_file.write_text('USER = dict(name="Ana")\n', encoding="utf-8")
        suite_file = tmp_path / "suite.robot"
        suite_file.write_text("*** Settings ***\nVariables    vars.py\n", encoding="utf-8")
        index = WorkspaceIndex()
        index.update_file(suite_file)
        entry = index.entries[path_to_uri(suite_file.resolve())]

        variables = index.imported_variables(suite_file, entry.suite)

        assert variables == []

    def test_imported_variables_from_yaml_file_dict(self, tmp_path):
        var_file = tmp_path / "vars.yaml"
        var_file.write_text("USER:\n  name: Ana\n  email: ana@example.com\n", encoding="utf-8")
        suite_file = tmp_path / "suite.robot"
        suite_file.write_text("*** Settings ***\nVariables    vars.yaml\n", encoding="utf-8")
        index = WorkspaceIndex()
        index.update_file(suite_file)
        entry = index.entries[path_to_uri(suite_file.resolve())]

        variables = index.imported_variables(suite_file, entry.suite)

        assert len(variables) == 1
        assert variables[0].name == "${USER}"
        assert variables[0].kind == "dict"
        assert variables[0].value == {"name": "Ana", "email": "ana@example.com"}

    def test_imported_variables_resolves_variable_file_without_suffix(self, tmp_path):
        var_file = tmp_path / "vars.yml"
        var_file.write_text("USER:\n  name: Ana\n", encoding="utf-8")
        suite_file = tmp_path / "suite.robot"
        suite_file.write_text("*** Settings ***\nVariables    vars\n", encoding="utf-8")
        index = WorkspaceIndex()
        index.update_file(suite_file)
        entry = index.entries[path_to_uri(suite_file.resolve())]

        variables = index.imported_variables(suite_file, entry.suite)

        assert variables[0].name == "${USER}"
        assert variables[0].value == {"name": "Ana"}

    def test_imported_variable_locations_transitive(self, tmp_path):
        # a.robot imports b.resource (hub) which imports c.resource (has vars)
        c = tmp_path / "c.resource"
        c.write_text("*** Variables ***\n${DEEP_VAR}    value\n", encoding="utf-8")
        b = tmp_path / "b.resource"
        b.write_text("*** Settings ***\nResource    c.resource\n", encoding="utf-8")
        a = tmp_path / "a.robot"
        a.write_text("*** Settings ***\nResource    b.resource\n", encoding="utf-8")

        index = WorkspaceIndex()
        index.scan(tmp_path)
        entry = index.entries[path_to_uri(a.resolve())]

        locations = index.imported_variable_locations(a, entry.suite)

        assert any(loc.name == "${DEEP_VAR}" for loc in locations)


class TestIsPathImport:
    def test_py_extension_is_path(self):
        assert _is_path_import("../../libs/Looper.py") is True

    def test_relative_dotslash_is_path(self):
        assert _is_path_import("./libs/Looper.py") is True

    def test_forward_slash_is_path(self):
        assert _is_path_import("src/libs/MyLib.py") is True

    def test_backslash_is_path(self):
        assert _is_path_import("src\\libs\\MyLib.py") is True

    def test_module_name_is_not_path(self):
        assert _is_path_import("Collections") is False
        assert _is_path_import("SeleniumLibrary") is False
        assert _is_path_import("robot.libraries.BuiltIn") is False

    def test_dotted_module_is_not_path(self):
        assert _is_path_import("my.company.Library") is False


class TestPathBasedLibraryImport:
    def test_resolves_relative_py_library(self, tmp_path):
        libs = tmp_path / "libs"
        libs.mkdir()
        lib_file = libs / "Looper.py"
        lib_file.write_text("# dummy library\n", encoding="utf-8")
        suite_dir = tmp_path / "tests"
        suite_dir.mkdir()
        suite = suite_dir / "suite.robot"
        suite.write_text("*** Settings ***\nLibrary    ../libs/Looper.py\n", encoding="utf-8")

        index = WorkspaceIndex()
        import_ = _dummy_import("../libs/Looper.py")
        resolution = index.resolve_import(suite, import_)

        assert resolution.resolved_path == lib_file.resolve()

    def test_resolves_absolute_py_library(self, tmp_path):
        lib_file = tmp_path / "MyLib.py"
        lib_file.write_text("# dummy\n", encoding="utf-8")
        suite = tmp_path / "suite.robot"
        suite.write_text("*** Test Cases ***\n", encoding="utf-8")

        index = WorkspaceIndex()
        import_ = _dummy_import(str(lib_file))
        resolution = index.resolve_import(suite, import_)

        assert resolution.resolved_path == lib_file.resolve()

    def test_returns_none_for_nonexistent_path(self, tmp_path):
        suite = tmp_path / "suite.robot"
        suite.write_text("*** Test Cases ***\n", encoding="utf-8")
        index = WorkspaceIndex()
        import_ = _dummy_import("../../nonexistent/Lib.py")
        resolution = index.resolve_import(suite, import_)

        assert resolution.resolved_path is None

    def test_does_not_raise_for_path_with_dotdot(self, tmp_path):
        suite = tmp_path / "suite.robot"
        suite.write_text("*** Test Cases ***\n", encoding="utf-8")
        index = WorkspaceIndex()
        import_ = _dummy_import("../../src/libs/Looper.py")

        resolution = index.resolve_import(suite, import_)

        assert resolution.resolved_path is None  # doesn't exist, but no exception

    def test_module_name_still_resolves(self, tmp_path):
        main, _resource, _variables = write_workspace(tmp_path)
        index = WorkspaceIndex()
        index.scan(tmp_path)
        suite = index.entries[path_to_uri(main.resolve())].suite

        resolution = index.resolve_import(main, suite.imports[2])

        assert resolution.resolved_path is not None
        assert resolution.resolved_path.name == "Collections.py"
