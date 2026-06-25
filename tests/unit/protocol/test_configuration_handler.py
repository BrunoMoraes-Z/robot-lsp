from robot_lsp.application.diagnostic_service import DiagnosticService
from robot_lsp.application.parse_service import ParseService
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser
from robot_lsp.protocol.jsonrpc import create_notification, create_request, create_response
from robot_lsp.protocol.server import LspServer


def make_server(initialization_options=None, log_levels=None):
    server = LspServer(log_level_applier=log_levels.append if log_levels is not None else None)
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
        assert capabilities["workspace"]["workspaceFolders"] == {"supported": True, "changeNotifications": False}

    def test_initialized_requests_workspace_configuration_when_supported(self):
        server = LspServer()
        server.handle_message(
            create_request(
                "initialize",
                id=1,
                params={
                    "capabilities": {"workspace": {"configuration": True}},
                    "workspaceFolders": [{"uri": "file:///c:/projects/app", "name": "app"}],
                },
            )
        )

        server.handle_message(create_notification("initialized", params={}))

        assert len(server.outgoing_requests) == 1
        request = server.outgoing_requests[0]
        assert request.method == "workspace/configuration"
        assert request.params == {
            "items": [
                {"section": "robot.lsp"},
                {"scopeUri": "file:///c:/projects/app", "section": "robot.lsp"},
            ]
        }

    def test_workspace_configuration_reports_progress_when_supported(self):
        server = LspServer()
        server.handle_message(
            create_request(
                "initialize",
                id=1,
                params={
                    "capabilities": {
                        "workspace": {"configuration": True},
                        "window": {"workDoneProgress": True},
                    },
                    "workspaceFolders": [{"uri": "file:///c:/projects/app", "name": "app"}],
                },
            )
        )

        server.handle_message(create_notification("initialized", params={}))

        assert [request.method for request in server.outgoing_requests] == [
            "window/workDoneProgress/create",
            "workspace/configuration",
        ]
        token = server.outgoing_requests[0].params["token"]
        assert [notification.method for notification in server.outgoing_notifications] == [
            "$/progress",
            "$/progress",
            "$/progress",
        ]
        assert [notification.params["value"]["kind"] for notification in server.outgoing_notifications] == [
            "begin",
            "report",
            "end",
        ]
        assert all(notification.params["token"] == token for notification in server.outgoing_notifications)

    def test_workspace_configuration_response_updates_global_and_folder_config(self):
        log_levels = []
        server = LspServer(log_level_applier=log_levels.append)
        server.handle_message(
            create_request(
                "initialize",
                id=1,
                params={
                    "capabilities": {"workspace": {"configuration": True}},
                    "workspaceFolders": [{"uri": "file:///c:/projects/app", "name": "app"}],
                },
            )
        )
        server.handle_message(create_notification("initialized", params={}))
        request_id = server.outgoing_requests[0].id

        response = server.handle_message(
            create_response(
                request_id,
                result=[
                    {"logLevel": "debug"},
                    {"diagnostics": {"enable": False}, "completion": {"snippets": False}},
                ],
            )
        )

        assert response is None
        assert server.configuration_service.config.log_level == "debug"
        assert log_levels == ["debug"]
        folder_config = server.configuration_service.config_for_uri("file:///c:/projects/app/tests/example.robot")
        assert folder_config.diagnostics.enable is False
        assert folder_config.completion.snippets is False

    def test_workspace_folder_diagnostics_config_is_used_on_did_open(self):
        server, _capabilities = make_server()
        server.configuration_service.update({"diagnostics": {"enable": False}}, scope_uri="file:///c:/projects/app")

        server.handle_message(
            create_notification(
                "textDocument/didOpen",
                params={
                    "textDocument": {
                        "uri": "file:///c:/projects/app/no-diagnostics.robot",
                        "languageId": "robotframework",
                        "version": 1,
                        "text": "*** Test Cases ***\nBroken\n    ELSE\n",
                    }
                },
            )
        )

        assert server.diagnostic_service.cancel_pending("file:///c:/projects/app/no-diagnostics.robot") is False

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

    def test_initialize_applies_configured_log_level(self):
        log_levels = []

        make_server({"robot": {"lsp": {"logLevel": "debug"}}}, log_levels=log_levels)

        assert log_levels == ["debug"]

    def test_did_change_configuration_applies_log_level_at_runtime(self):
        log_levels = []
        server, _capabilities = make_server(log_levels=log_levels)

        server.handle_message(
            create_notification(
                "workspace/didChangeConfiguration",
                params={"settings": {"robot": {"lsp": {"logLevel": "error"}}}},
            )
        )

        assert log_levels == ["error"]

    def test_did_change_configuration_does_not_reapply_same_log_level(self):
        log_levels = []
        server, _capabilities = make_server({"logLevel": "debug"}, log_levels=log_levels)
        log_levels.clear()

        server.handle_message(
            create_notification(
                "workspace/didChangeConfiguration",
                params={"settings": {"robot": {"lsp": {"logLevel": "debug"}}}},
            )
        )

        assert log_levels == []

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
