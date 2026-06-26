from robot_lsp.application.completion_service import CompletionService
from robot_lsp.application.parse_service import ParseService
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser
from robot_lsp.protocol.jsonrpc import create_notification, create_request
from robot_lsp.protocol.server import LspServer


def make_server(text: str, initialization_options=None):
    server = LspServer()
    parse_service = ParseService(server.document_store, RobotFrameworkParser())
    server.completion_service = CompletionService(server.document_store, parse_service)
    params = {"capabilities": {}}
    if initialization_options is not None:
        params["initializationOptions"] = initialization_options
    server.handle_message(create_request("initialize", id=1, params=params))
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

    def test_text_document_completion_applies_snippets_config(self):
        server, uri = make_server("", {"completion": {"snippets": False}})

        response = server.handle_message(
            create_request(
                "textDocument/completion",
                id=2,
                params={
                    "textDocument": {"uri": uri},
                    "position": {"line": 0, "character": 0},
                },
            )
        )

        first_item = response.result["items"][0]
        assert first_item["label"] == "*** Settings ***"
        assert first_item["kind"] == 1
        assert "insertTextFormat" not in first_item

    def test_text_document_completion_applies_workspace_folder_snippets_config(self):
        server, uri = make_server("")
        server.configuration_service.update({"completion": {"snippets": False}}, scope_uri="file:///c:/projects")

        response = server.handle_message(
            create_request(
                "textDocument/completion",
                id=2,
                params={
                    "textDocument": {"uri": uri},
                    "position": {"line": 0, "character": 0},
                },
            )
        )

        first_item = response.result["items"][0]
        assert first_item["label"] == "*** Settings ***"
        assert first_item["kind"] == 1
        assert "insertTextFormat" not in first_item

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

    def test_text_document_completion_dictionary_keys_uses_explicit_text_edit(self):
        text = (
            "*** Variables ***\n"
            "&{DISPLAY_SALES_ORDER}\n"
            "...    input_sales_order=id=M0:46:::2:22\n"
            "...    btn_continue=id=M0:50::btn[0]\n"
            "...    input_payment_terms=id=M0:46:2:3B256:1::4:17\n"
            "*** Test Cases ***\n"
            "T\n"
            "    Log    ${DISPLAY_SALES_ORDER.}\n"
        )
        server, uri = make_server(text)
        character = len("    Log    ${DISPLAY_SALES_ORDER.")

        response = server.handle_message(
            create_request(
                "textDocument/completion",
                id=2,
                params={
                    "textDocument": {"uri": uri},
                    "position": {"line": 7, "character": character},
                    "context": {"triggerCharacter": "."},
                },
            )
        )

        items = response.result["items"]
        assert [item["label"] for item in items] == [
            "input_sales_order",
            "btn_continue",
            "input_payment_terms",
        ]
        assert items[0]["textEdit"] == {
            "range": {
                "start": {"line": 7, "character": character},
                "end": {"line": 7, "character": character},
            },
            "newText": "input_sales_order",
        }

    def test_text_document_completion_dictionary_bracket_keys_quotes_and_closes_bracket(self):
        text = (
            "*** Variables ***\n"
            "&{DISPLAY_SALES_ORDER}\n"
            "...    input_sales_order=id=M0:46:::2:22\n"
            "...    btn_continue=id=M0:50::btn[0]\n"
            "*** Test Cases ***\n"
            "T\n"
            "    Log    ${DISPLAY_SALES_ORDER[}\n"
        )
        server, uri = make_server(text)
        character = len("    Log    ${DISPLAY_SALES_ORDER[")

        response = server.handle_message(
            create_request(
                "textDocument/completion",
                id=2,
                params={
                    "textDocument": {"uri": uri},
                    "position": {"line": 6, "character": character},
                    "context": {"triggerCharacter": "["},
                },
            )
        )

        first_item = response.result["items"][0]
        assert first_item["label"] == "input_sales_order"
        assert first_item["textEdit"] == {
            "range": {
                "start": {"line": 6, "character": character},
                "end": {"line": 6, "character": character},
            },
            "newText": '"input_sales_order"]',
        }

    def test_text_document_completion_dictionary_bracket_keys_reuses_auto_closed_bracket(self):
        text = (
            "*** Variables ***\n"
            "&{DISPLAY_SALES_ORDER}\n"
            "...    input_sales_order=id=M0:46:::2:22\n"
            "...    btn_continue=id=M0:50::btn[0]\n"
            "*** Test Cases ***\n"
            "T\n"
            "    Log    ${DISPLAY_SALES_ORDER[]}\n"
        )
        server, uri = make_server(text)
        character = len("    Log    ${DISPLAY_SALES_ORDER[")

        response = server.handle_message(
            create_request(
                "textDocument/completion",
                id=2,
                params={
                    "textDocument": {"uri": uri},
                    "position": {"line": 6, "character": character},
                    "context": {"triggerCharacter": "["},
                },
            )
        )

        first_item = response.result["items"][0]
        assert first_item["label"] == "input_sales_order"
        assert first_item["textEdit"] == {
            "range": {
                "start": {"line": 6, "character": character},
                "end": {"line": 6, "character": character},
            },
            "newText": '"input_sales_order"',
        }
