from robot_lsp.application.diagnostic_service import DiagnosticService
from robot_lsp.application.parse_service import ParseService
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser
from robot_lsp.protocol.jsonrpc import create_notification, create_request
from robot_lsp.protocol.server import LspServer


def make_server():
    server = LspServer()
    parse_service = ParseService(server.document_store, RobotFrameworkParser())
    server.diagnostic_service = DiagnosticService(
        parse_service,
        server.publish_diagnostics,
        debounce_seconds=999.0,
    )
    server.handle_message(create_request("initialize", id=1, params={"capabilities": {}}))
    return server


class TestPublishDiagnostics:
    def test_did_open_publishes_diagnostics_when_flushed(self):
        server = make_server()
        uri = "file:///c:/projects/bad.robot"

        server.handle_message(
            create_notification(
                "textDocument/didOpen",
                params={
                    "textDocument": {
                        "uri": uri,
                        "languageId": "robotframework",
                        "version": 1,
                        "text": "*** Test Cases ***\nBroken\n    ELSE\n",
                    }
                },
            )
        )
        server.diagnostic_service.flush(uri)

        assert len(server.outgoing_notifications) == 1
        notification = server.outgoing_notifications[0]
        assert notification.method == "textDocument/publishDiagnostics"
        assert notification.params["uri"] == uri
        assert len(notification.params["diagnostics"]) == 1
        assert notification.params["diagnostics"][0]["severity"] == 1

    def test_did_change_clears_diagnostics_when_flushed(self):
        server = make_server()
        uri = "file:///c:/projects/fixed.robot"
        server.handle_message(
            create_notification(
                "textDocument/didOpen",
                params={
                    "textDocument": {
                        "uri": uri,
                        "languageId": "robotframework",
                        "version": 1,
                        "text": "*** Test Cases ***\nBroken\n    ELSE\n",
                    }
                },
            )
        )
        server.diagnostic_service.flush(uri)

        server.handle_message(
            create_notification(
                "textDocument/didChange",
                params={
                    "textDocument": {"uri": uri, "version": 2},
                    "contentChanges": [{"text": "*** Test Cases ***\nFixed\n    Log    ok\n"}],
                },
            )
        )
        server.diagnostic_service.flush(uri)

        assert len(server.outgoing_notifications) == 2
        assert server.outgoing_notifications[1].params["diagnostics"] == []

    def test_did_close_clears_diagnostics(self):
        server = make_server()
        uri = "file:///c:/projects/closed.robot"
        server.document_store.open(uri=uri, text="x", version=1, language_id="robotframework")
        server.publish_diagnostics(uri, [])
        server.outgoing_notifications.clear()

        server.handle_message(
            create_notification("textDocument/didClose", params={"textDocument": {"uri": uri}})
        )

        assert server.document_store.get(uri) is None
        assert len(server.outgoing_notifications) == 1
        assert server.outgoing_notifications[0].params == {"uri": uri, "diagnostics": []}
