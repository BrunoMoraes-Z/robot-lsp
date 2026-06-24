from robot_lsp.application.diagnostic_service import DiagnosticService
from robot_lsp.application.parse_service import ParseService
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser
from robot_lsp.protocol.jsonrpc import create_notification, create_request
from robot_lsp.protocol.server import LspServer


def make_server(initialization_options=None):
    server = LspServer()
    server.diagnostic_service = DiagnosticService(
        ParseService(server.document_store, RobotFrameworkParser()),
        server.publish_diagnostics,
        debounce_seconds=999.0,
    )
    params = {"capabilities": {}}
    if initialization_options is not None:
        params["initializationOptions"] = initialization_options
    init_response = server.handle_message(create_request("initialize", id=1, params=params))
    return server, init_response.result["capabilities"]


class TestConfigurationHandler:
    def test_initialize_applies_initialization_options(self):
        server, capabilities = make_server({"robot": {"lsp": {"diagnostics": {"enable": False}}}})

        assert server.configuration_service.config.diagnostics.enable is False
        assert capabilities["workspace"]["didChangeConfiguration"] == {"dynamicRegistration": False}

    def test_did_change_configuration_updates_settings(self):
        server, _capabilities = make_server()

        response = server.handle_message(
            create_notification(
                "workspace/didChangeConfiguration",
                params={"settings": {"robot": {"lsp": {"logLevel": "debug"}}}},
            )
        )

        assert response is None
        assert server.configuration_service.config.log_level == "debug"

    def test_diagnostics_disabled_does_not_schedule_on_did_open(self):
        server, _capabilities = make_server({"diagnostics": {"enable": False}})
        uri = "file:///c:/projects/no-diagnostics.robot"

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

        assert server.outgoing_notifications == []
        assert server.diagnostic_service.cancel_pending(uri) is False

    def test_disabling_diagnostics_clears_open_document_diagnostics(self):
        server, _capabilities = make_server()
        uri = "file:///c:/projects/clear-diagnostics.robot"
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
                "workspace/didChangeConfiguration",
                params={"settings": {"diagnostics": {"enable": False}}},
            )
        )

        assert len(server.outgoing_notifications) == 2
        assert server.outgoing_notifications[1].params == {"uri": uri, "diagnostics": []}
