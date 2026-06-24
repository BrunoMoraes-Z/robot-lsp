from robot_lsp.application.completion_service import CompletionService
from robot_lsp.application.parse_service import ParseService
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser
from robot_lsp.protocol.jsonrpc import create_notification, create_request
from robot_lsp.protocol.server import LspServer


def make_server(text: str):
    server = LspServer()
    parse_service = ParseService(server.document_store, RobotFrameworkParser())
    server.completion_service = CompletionService(server.document_store, parse_service)
    server.handle_message(create_request("initialize", id=1, params={"capabilities": {}}))
    uri = "file:///c:/projects/server-completion.robot"
    server.handle_message(
        create_notification(
            "textDocument/didOpen",
            params={
                "textDocument": {
                    "uri": uri,
                    "languageId": "robotframework",
                    "version": 1,
                    "text": text,
                }
            },
        )
    )
    return server, uri


class TestCompletionHandler:
    def test_text_document_completion(self):
        server, uri = make_server("*** Settings ***\n")

        response = server.handle_message(
            create_request(
                "textDocument/completion",
                id=2,
                params={
                    "textDocument": {"uri": uri},
                    "position": {"line": 1, "character": 0},
                },
            )
        )

        assert response is not None
        assert response.id == 2
        assert response.result["isIncomplete"] is False
        assert "Library" in [item["label"] for item in response.result["items"]]

    def test_text_document_completion_without_service_returns_empty_list(self):
        server = LspServer()
        server.handle_message(create_request("initialize", id=1, params={"capabilities": {}}))

        response = server.handle_message(
            create_request(
                "textDocument/completion",
                id=2,
                params={
                    "textDocument": {"uri": "file:///missing.robot"},
                    "position": {"line": 0, "character": 0},
                },
            )
        )

        assert response.result == {"isIncomplete": False, "items": []}
