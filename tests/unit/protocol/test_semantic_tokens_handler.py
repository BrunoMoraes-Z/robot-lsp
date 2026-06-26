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


def decoded_tokens(data: list[int]) -> list[tuple[int, int, int, str]]:
    tokens: list[tuple[int, int, int, str]] = []
    line = 0
    start = 0
    for index in range(0, len(data), 5):
        delta_line, delta_start, length, token_type_index, _modifiers = data[index : index + 5]
        line += delta_line
        start = delta_start if delta_line else start + delta_start
        tokens.append((line, start, length, TOKEN_TYPES[token_type_index]))
    return tokens


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

    def test_semantic_tokens_split_variables_inside_arguments(self):
        server, uri = make_server(
            "*** Test Cases ***\n"
            "Example\n"
            "    Log    prefix ${value} suffix\n"
        )

        response = server.handle_message(
            create_request(
                "textDocument/semanticTokens/full",
                id=2,
                params={"textDocument": {"uri": uri}},
            )
        )

        tokens = decoded_tokens(response.result["data"])
        assert (2, 18, 2, "variableOperator") in tokens
        assert (2, 20, 5, "variable") in tokens
        assert (2, 25, 1, "variableOperator") in tokens
        assert (2, 11, 7, "argumentValue") in tokens
        assert (2, 26, 7, "argumentValue") in tokens

    def test_semantic_tokens_split_bracket_settings(self):
        server, uri = make_server(
            "*** Keywords ***\n"
            "Keyword\n"
            "    [Arguments]    ${value}\n"
        )

        response = server.handle_message(
            create_request(
                "textDocument/semanticTokens/full",
                id=2,
                params={"textDocument": {"uri": uri}},
            )
        )

        tokens = decoded_tokens(response.result["data"])
        assert (2, 4, 1, "settingOperator") in tokens
        assert (2, 5, 9, "setting") in tokens
        assert (2, 14, 1, "settingOperator") in tokens
        assert (2, 19, 2, "variableOperator") in tokens
        assert (2, 21, 5, "variable") in tokens
        assert (2, 26, 1, "variableOperator") in tokens

    def test_semantic_tokens_split_named_arguments(self):
        server, uri = make_server(
            "*** Test Cases ***\n"
            "Example\n"
            "    Log    name=value\n"
        )

        response = server.handle_message(
            create_request(
                "textDocument/semanticTokens/full",
                id=2,
                params={"textDocument": {"uri": uri}},
            )
        )

        tokens = decoded_tokens(response.result["data"])
        assert (2, 11, 4, "parameterName") in tokens
        assert (2, 15, 1, "variableOperator") in tokens
        assert (2, 16, 5, "argumentValue") in tokens

    def test_semantic_tokens_split_named_arguments_with_variable_value(self):
        server, uri = make_server(
            "*** Test Cases ***\n"
            "Example\n"
            "    Log    name=${value}\n"
        )

        response = server.handle_message(
            create_request(
                "textDocument/semanticTokens/full",
                id=2,
                params={"textDocument": {"uri": uri}},
            )
        )

        tokens = decoded_tokens(response.result["data"])
        assert (2, 11, 4, "parameterName") in tokens
        assert (2, 15, 1, "variableOperator") in tokens
        assert (2, 16, 2, "variableOperator") in tokens
        assert (2, 18, 5, "variable") in tokens
        assert (2, 23, 1, "variableOperator") in tokens

    def test_semantic_tokens_do_not_split_escaped_equals(self):
        server, uri = make_server(
            "*** Test Cases ***\n"
            "Example\n"
            "    Log    name\\=value\n"
        )

        response = server.handle_message(
            create_request(
                "textDocument/semanticTokens/full",
                id=2,
                params={"textDocument": {"uri": uri}},
            )
        )

        tokens = decoded_tokens(response.result["data"])
        assert (2, 11, 11, "argumentValue") in tokens
        assert "parameterName" not in [token_type for _line, _start, _length, token_type in tokens]

    def test_semantic_tokens_split_bdd_keyword_prefix(self):
        server, uri = make_server(
            "*** Test Cases ***\n"
            "Example\n"
            "    When Log    done\n"
        )

        response = server.handle_message(
            create_request(
                "textDocument/semanticTokens/full",
                id=2,
                params={"textDocument": {"uri": uri}},
            )
        )

        tokens = decoded_tokens(response.result["data"])
        assert (2, 4, 4, "control") in tokens
        assert (2, 9, 3, "keywordNameCall") in tokens

    def test_semantic_tokens_split_library_qualified_keyword_call(self):
        server, uri = make_server(
            "*** Test Cases ***\n"
            "Example\n"
            "    Collections.Append To List    item\n"
        )

        response = server.handle_message(
            create_request(
                "textDocument/semanticTokens/full",
                id=2,
                params={"textDocument": {"uri": uri}},
            )
        )

        tokens = decoded_tokens(response.result["data"])
        assert (2, 4, 12, "name") in tokens
        assert (2, 16, 14, "keywordNameCall") in tokens

    def test_semantic_tokens_split_bdd_and_library_qualified_keyword_call(self):
        server, uri = make_server(
            "*** Test Cases ***\n"
            "Example\n"
            "    Given Collections.Append To List    item\n"
        )

        response = server.handle_message(
            create_request(
                "textDocument/semanticTokens/full",
                id=2,
                params={"textDocument": {"uri": uri}},
            )
        )

        tokens = decoded_tokens(response.result["data"])
        assert (2, 4, 5, "control") in tokens
        assert (2, 10, 12, "name") in tokens
        assert (2, 22, 14, "keywordNameCall") in tokens
