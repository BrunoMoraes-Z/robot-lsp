from robot_lsp.application.semantic_tokens_service import SemanticTokensService, TOKEN_TYPES
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser
from robot_lsp.protocol.jsonrpc import create_notification, create_request
from robot_lsp.protocol.server import LspServer


def make_server(text: str):
    server = LspServer()
    server.semantic_tokens_service = SemanticTokensService(server.document_store, RobotFrameworkParser())
    server.handle_message(create_request("initialize", id=1, params={"capabilities": {}}))
    uri = "file:///c:/projects/semantic.robot"
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


def token_types(data: list[int]) -> list[str]:
    return [TOKEN_TYPES[data[index + 3]] for index in range(0, len(data), 5)]


class TestSemanticTokensHandler:
    def test_semantic_tokens_full_returns_tokens_for_open_document(self):
        server, uri = make_server(
            "*** Settings ***\n"
            "Library    Collections\n"
            "\n"
            "*** Variables ***\n"
            "${value}    1\n"
            "\n"
            "*** Test Cases ***\n"
            "Example\n"
            "    Log    ${value}    # inline\n"
        )

        response = server.handle_message(
            create_request(
                "textDocument/semanticTokens/full",
                id=2,
                params={"textDocument": {"uri": uri}},
            )
        )

        assert response is not None
        assert response.result is not None
        data = response.result["data"]
        assert len(data) % 5 == 0
        assert {"header", "setting", "name", "testCaseName", "keywordNameCall", "argumentValue", "variable", "comment"}.issubset(
            set(token_types(data))
        )

    def test_semantic_tokens_full_for_missing_document_returns_none(self):
        server = LspServer()
        server.semantic_tokens_service = SemanticTokensService(server.document_store, RobotFrameworkParser())
        server.handle_message(create_request("initialize", id=1, params={"capabilities": {}}))

        response = server.handle_message(
            create_request(
                "textDocument/semanticTokens/full",
                id=2,
                params={"textDocument": {"uri": "file:///missing.robot"}},
            )
        )

        assert response is not None
        assert response.result is None
