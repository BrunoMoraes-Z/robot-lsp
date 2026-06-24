from robot_lsp.application.parse_service import ParseService
from robot_lsp.application.refactoring_service import RefactoringService
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser
from robot_lsp.protocol.jsonrpc import create_notification, create_request
from robot_lsp.protocol.server import LspServer


TEXT = """*** Variables ***
${MESSAGE}    Hello

*** Test Cases ***
T
    Log    ${MESSAGE}
"""


def make_server():
    server = LspServer()
    parse_service = ParseService(server.document_store, RobotFrameworkParser())
    server.refactoring_service = RefactoringService(server.document_store, parse_service)
    init_response = server.handle_message(create_request("initialize", id=1, params={"capabilities": {}}))
    uri = "file:///c:/projects/refactoring-handler.robot"
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
    return server, uri, init_response.result["capabilities"]


class TestRefactoringHandlers:
    def test_initialize_rename_capability(self):
        _server, _uri, capabilities = make_server()

        assert capabilities["renameProvider"] == {"prepareProvider": True}

    def test_text_document_prepare_rename(self):
        server, uri, _capabilities = make_server()

        response = server.handle_message(
            create_request(
                "textDocument/prepareRename",
                id=2,
                params={"textDocument": {"uri": uri}, "position": {"line": 5, "character": 12}},
            )
        )

        assert response.result["placeholder"] == "${MESSAGE}"

    def test_text_document_rename(self):
        server, uri, _capabilities = make_server()

        response = server.handle_message(
            create_request(
                "textDocument/rename",
                id=2,
                params={
                    "textDocument": {"uri": uri},
                    "position": {"line": 5, "character": 12},
                    "newName": "${RENAMED}",
                },
            )
        )

        assert uri in response.result["changes"]
        assert len(response.result["changes"][uri]) == 2

    def test_rename_without_service_returns_null(self):
        server = LspServer()
        server.handle_message(create_request("initialize", id=1, params={"capabilities": {}}))

        response = server.handle_message(
            create_request(
                "textDocument/rename",
                id=2,
                params={
                    "textDocument": {"uri": "file:///missing.robot"},
                    "position": {"line": 0, "character": 0},
                    "newName": "x",
                },
            )
        )

        assert response.result is None
