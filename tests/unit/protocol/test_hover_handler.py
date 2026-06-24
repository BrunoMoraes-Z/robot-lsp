from robot_lsp.application.hover_service import HoverService
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
    server.hover_service = HoverService(server.document_store, parse_service)
    server.handle_message(create_request("initialize", id=1, params={"capabilities": {}}))
    uri = "file:///c:/projects/server-hover.robot"
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
    return server, uri


class TestHoverHandler:
    def test_text_document_hover(self):
        server, uri = make_server()

        response = server.handle_message(
            create_request(
                "textDocument/hover",
                id=2,
                params={
                    "textDocument": {"uri": uri},
                    "position": {"line": 5, "character": 12},
                },
            )
        )

        assert response is not None
        assert response.id == 2
        assert response.result["contents"]["kind"] == "markdown"
        assert "**${MESSAGE}**" in response.result["contents"]["value"]

    def test_text_document_hover_without_service_returns_null(self):
        server = LspServer()
        server.handle_message(create_request("initialize", id=1, params={"capabilities": {}}))

        response = server.handle_message(
            create_request(
                "textDocument/hover",
                id=2,
                params={
                    "textDocument": {"uri": "file:///missing.robot"},
                    "position": {"line": 0, "character": 0},
                },
            )
        )

        assert response is not None
        assert response.result is None
