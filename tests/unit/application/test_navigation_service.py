from robot_lsp.application.document_store import DocumentStore
from robot_lsp.application.navigation_service import NavigationService, SymbolKind
from robot_lsp.application.parse_service import ParseService
from robot_lsp.domain.models import LspPosition
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser


TEXT = """*** Settings ***
Library    Collections

*** Variables ***
${MESSAGE}    Hello

*** Test Cases ***
My Test
    My Keyword    ${MESSAGE}

*** Keywords ***
My Keyword
    [Documentation]    Keyword docs
    Log    ${MESSAGE}
"""


def make_service(text: str = TEXT):
    store = DocumentStore()
    parser = RobotFrameworkParser()
    service = NavigationService(store, ParseService(store, parser))
    uri = "file:///c:/projects/navigation.robot"
    store.open(uri=uri, text=text, version=1, language_id="robotframework")
    return service, uri


class TestNavigationService:
    def test_definition_local_keyword(self):
        service, uri = make_service()

        locations = service.definition(uri, LspPosition(line=8, character=7))

        assert len(locations) == 1
        assert locations[0]["uri"] == uri
        assert locations[0]["range"]["start"]["line"] == 11

    def test_definition_variable(self):
        service, uri = make_service()

        locations = service.definition(uri, LspPosition(line=8, character=21))

        assert len(locations) == 1
        assert locations[0]["range"]["start"] == {"line": 4, "character": 0}

    def test_references_variable(self):
        service, uri = make_service()

        locations = service.references(uri, LspPosition(line=8, character=21))

        assert len(locations) == 3
        assert all(location["uri"] == uri for location in locations)

    def test_references_excluding_declaration(self):
        service, uri = make_service()

        locations = service.references(
            uri,
            LspPosition(line=4, character=3),
            include_declaration=False,
        )

        assert len(locations) == 2
        assert all(location["range"]["start"]["line"] != 4 for location in locations)

    def test_document_symbols(self):
        service, uri = make_service()

        symbols = service.document_symbols(uri)
        names = [symbol["name"] for symbol in symbols]

        assert "Collections" in names
        assert "${MESSAGE}" in names
        assert "My Test" in names
        assert "My Keyword" in names
        variable = next(symbol for symbol in symbols if symbol["name"] == "${MESSAGE}")
        assert variable["kind"] == SymbolKind.VARIABLE

    def test_folding_ranges(self):
        service, uri = make_service()

        ranges = service.folding_ranges(uri)

        assert {"startLine": 0, "endLine": 2, "kind": "region"} in ranges
        assert any(item["startLine"] == 7 for item in ranges)
        assert any(item["startLine"] == 11 for item in ranges)

    def test_selection_ranges_symbol_and_line_parent(self):
        service, uri = make_service()

        ranges = service.selection_ranges(uri, [LspPosition(line=8, character=7)])

        assert len(ranges) == 1
        assert ranges[0]["range"]["start"] == {"line": 8, "character": 4}
        assert ranges[0]["parent"]["range"]["start"] == {"line": 8, "character": 0}

    def test_selection_ranges_line_fallback(self):
        service, uri = make_service()

        ranges = service.selection_ranges(uri, [LspPosition(line=0, character=0)])

        assert ranges == [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 16},
                }
            }
        ]

    def test_missing_document_returns_empty_results(self):
        service, _uri = make_service()

        assert service.definition("file:///missing.robot", LspPosition(0, 0)) == []
        assert service.references("file:///missing.robot", LspPosition(0, 0)) == []
        assert service.document_symbols("file:///missing.robot") == []
        assert service.folding_ranges("file:///missing.robot") == []
        assert service.selection_ranges("file:///missing.robot", [LspPosition(0, 0)]) == []
