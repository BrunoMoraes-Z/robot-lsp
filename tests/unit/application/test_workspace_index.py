from pathlib import Path

from robot_lsp.application.completion_service import CompletionService
from robot_lsp.application.document_store import DocumentStore, path_to_uri
from robot_lsp.application.navigation_service import NavigationService
from robot_lsp.application.parse_service import ParseService
from robot_lsp.application.workspace import WorkspaceIndex
from robot_lsp.domain.models import LspPosition
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser


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
        main, resource, _variables = write_workspace(tmp_path)
        index = WorkspaceIndex()
        index.scan(tmp_path)
        suite = index.entries[path_to_uri(main.resolve())].suite

        locations = index.imported_variable_locations(main, suite)

        assert len(locations) == 1
        assert locations[0].name == "${RESOURCE_VAR}"
        assert locations[0].uri == path_to_uri(resource.resolve())

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
