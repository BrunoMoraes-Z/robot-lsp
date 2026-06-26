from robot_lsp.application.navigation_service import NavigationService
from robot_lsp.application.parse_service import ParseService
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser
from robot_lsp.protocol.jsonrpc import create_notification, create_request
from robot_lsp.protocol.server import LspServer


TEXT = """*** Variables ***
${MESSAGE}    Hello

*** Test Cases ***
My Test
    Log    ${MESSAGE}
"""


def make_server():
    server = LspServer()
    parse_service = ParseService(server.document_store, RobotFrameworkParser())
    server.navigation_service = NavigationService(server.document_store, parse_service)
    response = server.handle_message(create_request("initialize", id=1, params={"capabilities": {}}))
    uri = "file:///c:/projects/navigation-handler.robot"
    server.handle_message(
        create_notification(
            "textDocument/didOpen",
            params={
                "textDocument": {
                    "uri": uri,
                    "languageId": "robotframework",
                    "version": 1,
                    "text": TEXT,
                }
            },
        )
    )
    return server, uri, response.result["capabilities"]


class TestNavigationHandlers:
    def test_initialize_navigation_capabilities(self):
        _server, _uri, capabilities = make_server()

        assert capabilities["definitionProvider"] is True
        assert capabilities["referencesProvider"] is True
        assert capabilities["documentSymbolProvider"] is True
        assert capabilities["foldingRangeProvider"] is True
        assert capabilities["selectionRangeProvider"] is True

    def test_text_document_definition(self):
        server, uri, _capabilities = make_server()

        response = server.handle_message(
            create_request(
                "textDocument/definition",
                id=2,
                params={"textDocument": {"uri": uri}, "position": {"line": 5, "character": 12}},
            )
        )

        assert response.result[0]["uri"] == uri
        assert response.result[0]["range"]["start"] == {"line": 1, "character": 0}

    def test_text_document_definition_returns_location_link_when_supported(self):
        server, uri, _capabilities = make_server()
        server.client_capabilities = {"textDocument": {"definition": {"linkSupport": True}}}

        response = server.handle_message(
            create_request(
                "textDocument/definition",
                id=2,
                params={"textDocument": {"uri": uri}, "position": {"line": 5, "character": 12}},
            )
        )

        assert response.result[0]["targetUri"] == uri
        assert response.result[0]["targetSelectionRange"]["start"] == {"line": 1, "character": 0}
        assert response.result[0]["originSelectionRange"] == {
            "start": {"line": 5, "character": 11},
            "end": {"line": 5, "character": 21},
        }

    def test_text_document_references(self):
        server, uri, _capabilities = make_server()

        response = server.handle_message(
            create_request(
                "textDocument/references",
                id=2,
                params={
                    "textDocument": {"uri": uri},
                    "position": {"line": 5, "character": 12},
                    "context": {"includeDeclaration": False},
                },
            )
        )

        assert len(response.result) == 1
        assert response.result[0]["range"]["start"]["line"] == 5

    def test_text_document_document_symbol(self):
        server, uri, _capabilities = make_server()

        response = server.handle_message(
            create_request("textDocument/documentSymbol", id=2, params={"textDocument": {"uri": uri}})
        )

        assert [symbol["name"] for symbol in response.result] == ["${MESSAGE}", "My Test"]

    def test_text_document_folding_range(self):
        server, uri, _capabilities = make_server()

        response = server.handle_message(
            create_request("textDocument/foldingRange", id=2, params={"textDocument": {"uri": uri}})
        )

        assert any(item["startLine"] == 0 for item in response.result)

    def test_text_document_selection_range(self):
        server, uri, _capabilities = make_server()

        response = server.handle_message(
            create_request(
                "textDocument/selectionRange",
                id=2,
                params={"textDocument": {"uri": uri}, "positions": [{"line": 5, "character": 12}]},
            )
        )

        assert response.result[0]["range"]["start"] == {"line": 5, "character": 11}

    def test_navigation_without_service_returns_empty_results(self):
        server = LspServer()
        server.handle_message(create_request("initialize", id=1, params={"capabilities": {}}))

        response = server.handle_message(
            create_request(
                "textDocument/definition",
                id=2,
                params={"textDocument": {"uri": "file:///missing.robot"}, "position": {"line": 0, "character": 0}},
            )
        )

        assert response.result == []
