from robot_lsp.protocol.jsonrpc import create_notification, create_request
from robot_lsp.protocol.lsp_types import ServerState
from robot_lsp.protocol.server import LspServer


def initialize(server: LspServer) -> None:
    server.handle_message(create_request("initialize", id=1, params={"capabilities": {}}))


class TestDocumentSync:
    def test_did_open(self):
        server = LspServer()
        initialize(server)

        response = server.handle_message(
            create_notification(
                "textDocument/didOpen",
                params={
                    "textDocument": {
                        "uri": "file:///c:/projects/test.robot",
                        "languageId": "robotframework",
                        "version": 1,
                        "text": "*** Test Cases ***\nExample\n",
                    }
                },
            )
        )

        doc = server.document_store.get("file:///c:/projects/test.robot")
        assert response is None
        assert doc is not None
        assert doc.version == 1
        assert doc.text == "*** Test Cases ***\nExample\n"

    def test_did_change_full(self):
        server = LspServer()
        initialize(server)
        server.handle_message(
            create_notification(
                "textDocument/didOpen",
                params={
                    "textDocument": {
                        "uri": "file:///c:/projects/test.robot",
                        "languageId": "robotframework",
                        "version": 1,
                        "text": "old",
                    }
                },
            )
        )

        response = server.handle_message(
            create_notification(
                "textDocument/didChange",
                params={
                    "textDocument": {
                        "uri": "file:///c:/projects/test.robot",
                        "version": 2,
                    },
                    "contentChanges": [{"text": "new"}],
                },
            )
        )

        doc = server.document_store.get("file:///c:/projects/test.robot")
        assert response is None
        assert doc is not None
        assert doc.text == "new"
        assert doc.version == 2

    def test_did_close(self):
        server = LspServer()
        initialize(server)
        uri = "file:///c:/projects/test.robot"
        server.document_store.open(uri=uri, text="x", version=1, language_id="robotframework")

        response = server.handle_message(
            create_notification(
                "textDocument/didClose",
                params={"textDocument": {"uri": uri}},
            )
        )

        assert response is None
        assert server.document_store.get(uri) is None

    def test_document_notifications_before_initialize_are_ignored(self):
        server = LspServer()

        response = server.handle_message(
            create_notification(
                "textDocument/didOpen",
                params={
                    "textDocument": {
                        "uri": "file:///c:/projects/test.robot",
                        "languageId": "robotframework",
                        "version": 1,
                        "text": "x",
                    }
                },
            )
        )

        assert response is None
        assert server.state == ServerState.UNINITIALIZED
        assert server.document_store.get("file:///c:/projects/test.robot") is None
