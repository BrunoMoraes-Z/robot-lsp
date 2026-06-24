from pathlib import Path

from robot_lsp.application.document_store import DocumentStore, path_to_uri
from robot_lsp.application.parse_service import ParseService
from robot_lsp.application.refactoring_service import RefactoringService
from robot_lsp.application.workspace import WorkspaceIndex
from robot_lsp.domain.models import LspPosition
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser


TEXT = """*** Variables ***
${MESSAGE}    Hello

*** Test Cases ***
My Test
    My Keyword    ${MESSAGE}

*** Keywords ***
My Keyword
    Log    ${MESSAGE}
"""


def make_service(text: str = TEXT):
    store = DocumentStore()
    parser = RobotFrameworkParser()
    service = RefactoringService(store, ParseService(store, parser))
    uri = "file:///c:/projects/refactor.robot"
    store.open(uri=uri, text=text, version=1, language_id="robotframework")
    return service, uri


class TestRefactoringService:
    def test_prepare_rename_variable(self):
        service, uri = make_service()

        result = service.prepare_rename(uri, LspPosition(line=5, character=21))

        assert result == {
            "range": {
                "start": {"line": 5, "character": 18},
                "end": {"line": 5, "character": 28},
            },
            "placeholder": "${MESSAGE}",
        }

    def test_prepare_rename_unknown_symbol_returns_none(self):
        service, uri = make_service()

        assert service.prepare_rename(uri, LspPosition(line=0, character=0)) is None

    def test_rename_variable_local_document(self):
        service, uri = make_service()

        edit = service.rename(uri, LspPosition(line=5, character=21), "${NEW_MESSAGE}")

        assert edit is not None
        assert list(edit["changes"].keys()) == [uri]
        edits = edit["changes"][uri]
        assert len(edits) == 3
        assert edits[0]["newText"] == "${NEW_MESSAGE}"

    def test_rename_keyword_local_document(self):
        service, uri = make_service()

        edit = service.rename(uri, LspPosition(line=5, character=7), "Renamed Keyword")

        assert edit is not None
        edits = edit["changes"][uri]
        assert len(edits) == 2
        assert all(item["newText"] == "Renamed Keyword" for item in edits)

    def test_rename_empty_new_name_returns_none(self):
        service, uri = make_service()

        assert service.rename(uri, LspPosition(line=5, character=7), "") is None

    def test_rename_with_workspace_index_updates_indexed_files(self, tmp_path):
        main = tmp_path / "main.robot"
        resource = tmp_path / "resource.resource"
        main.write_text(
            "*** Settings ***\nResource    resource.resource\n\n*** Test Cases ***\nT\n    Shared Keyword\n",
            encoding="utf-8",
        )
        resource.write_text(
            "*** Keywords ***\nShared Keyword\n    Log    ok\n",
            encoding="utf-8",
        )
        index = WorkspaceIndex()
        index.scan(tmp_path)
        store = DocumentStore()
        parser = RobotFrameworkParser()
        uri = path_to_uri(resource.resolve())
        store.open(uri=uri, text=resource.read_text(encoding="utf-8"), version=1, language_id="robotframework")
        service = RefactoringService(store, ParseService(store, parser), index)

        edit = service.rename(uri, LspPosition(line=1, character=2), "Better Keyword")

        assert edit is not None
        assert path_to_uri(main.resolve()) in edit["changes"]
        assert path_to_uri(resource.resolve()) in edit["changes"]
        assert sum(len(items) for items in edit["changes"].values()) == 2
