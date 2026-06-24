from robot_lsp.application.code_action_service import CodeActionService
from robot_lsp.application.formatting_service import FormattingService
from robot_lsp.protocol.jsonrpc import create_notification, create_request
from robot_lsp.protocol.server import LspServer


def make_server():
    server = LspServer()
    server.formatting_service = FormattingService(server.document_store)
    server.code_action_service = CodeActionService(server.document_store)
    init_response = server.handle_message(create_request("initialize", id=1, params={"capabilities": {}}))
    uri = "file:///c:/projects/format-handler.robot"
    server.handle_message(
        create_notification(
            "textDocument/didOpen",
            params={
                "textDocument": {
                    "uri": uri,
                    "languageId": "robotframework",
                    "version": 1,
                    "text": "*** Test Cases ***\nT\n    Log  hello\n",
                }
            },
        )
    )
    return server, uri, init_response.result["capabilities"]


class TestFormattingAndCodeActionHandlers:
    def test_initialize_capabilities(self):
        _server, _uri, capabilities = make_server()

        assert capabilities["documentFormattingProvider"] is True
        assert capabilities["documentRangeFormattingProvider"] is True
        assert capabilities["codeActionProvider"] == {
            "codeActionKinds": ["quickfix"],
            "resolveProvider": False,
        }

    def test_text_document_formatting(self):
        server, uri, _capabilities = make_server()

        response = server.handle_message(
            create_request(
                "textDocument/formatting",
                id=2,
                params={"textDocument": {"uri": uri}, "options": {"tabSize": 4, "insertSpaces": True}},
            )
        )

        assert response.result[0]["newText"] == "*** Test Cases ***\nT\n    Log    hello\n"

    def test_text_document_range_formatting(self):
        server, uri, _capabilities = make_server()

        response = server.handle_message(
            create_request(
                "textDocument/rangeFormatting",
                id=2,
                params={
                    "textDocument": {"uri": uri},
                    "range": {"start": {"line": 2, "character": 0}, "end": {"line": 2, "character": 14}},
                    "options": {"tabSize": 4, "insertSpaces": True},
                },
            )
        )

        assert response.result == [
            {
                "range": {"start": {"line": 2, "character": 0}, "end": {"line": 2, "character": 14}},
                "newText": "    Log    hello",
            }
        ]

    def test_text_document_code_action(self):
        server, uri, _capabilities = make_server()
        diagnostic = {"code": "parse_error", "message": "Invalid syntax"}

        response = server.handle_message(
            create_request(
                "textDocument/codeAction",
                id=2,
                params={
                    "textDocument": {"uri": uri},
                    "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
                    "context": {"diagnostics": [diagnostic]},
                },
            )
        )

        assert response.result[0]["kind"] == "quickfix"
        assert response.result[0]["diagnostics"] == [diagnostic]
