from robot_lsp.protocol.jsonrpc import (
    SERVER_NOT_INITIALIZED,
    SERVER_SHUTTING_DOWN,
    create_notification,
    create_request,
)
from robot_lsp.protocol.lsp_types import ServerState, TextDocumentSyncKind
from robot_lsp.protocol.server import LspServer


def initialize(server: LspServer):
    return server.handle_message(
        create_request(
            "initialize",
            id=1,
            params={
                "processId": 1234,
                "rootUri": "file:///c:/projects/robot",
                "capabilities": {"workspace": {}},
            },
        )
    )


class TestLspServerLifecycle:
    def test_initialize(self):
        server = LspServer()

        response = initialize(server)

        assert response is not None
        assert response.id == 1
        assert response.result["serverInfo"] == {
            "name": "robot-lsp",
            "version": "0.1.0",
        }
        assert server.state == ServerState.RUNNING
        assert server.process_id == 1234
        assert server.root_uri == "file:///c:/projects/robot"
        assert server.client_capabilities == {"workspace": {}}

    def test_capabilities_format(self):
        server = LspServer()

        response = initialize(server)

        capabilities = response.result["capabilities"]

        assert capabilities["textDocumentSync"] == {
            "openClose": True,
            "change": TextDocumentSyncKind.FULL,
        }
        assert capabilities["textDocumentSync"]["change"] == 1
        assert capabilities["completionProvider"] == {
            "triggerCharacters": [" ", "$", "@", "&", "%"],
            "resolveProvider": False,
        }
        assert capabilities["hoverProvider"] is True

    def test_initialized(self):
        server = LspServer()
        initialize(server)

        response = server.handle_message(create_notification("initialized", params={}))

        assert response is None
        assert server.state == ServerState.RUNNING

    def test_shutdown(self):
        server = LspServer()
        initialize(server)

        response = server.handle_message(create_request("shutdown", id=2))

        assert response is not None
        assert response.id == 2
        assert response.result is None
        assert server.state == ServerState.SHUTTING_DOWN

    def test_exit(self):
        server = LspServer()
        initialize(server)
        server.handle_message(create_request("shutdown", id=2))

        response = server.handle_message(create_notification("exit"))

        assert response is None
        assert server.exit_requested is True
        assert server.exit_code == 0
        assert server.state == ServerState.EXITED

    def test_exit_before_shutdown_sets_error_exit_code(self):
        server = LspServer()
        initialize(server)

        response = server.handle_message(create_notification("exit"))

        assert response is None
        assert server.exit_requested is True
        assert server.exit_code == 1
        assert server.state == ServerState.EXITED

    def test_request_before_initialize(self):
        server = LspServer()

        response = server.handle_message(create_request("shutdown", id=1))

        assert response is not None
        assert response.error is not None
        assert response.error.code == SERVER_NOT_INITIALIZED
        assert response.error.message == "Server not initialized"
        assert server.state == ServerState.UNINITIALIZED

    def test_notification_before_initialize_is_ignored(self):
        server = LspServer()

        response = server.handle_message(create_notification("initialized"))

        assert response is None
        assert server.state == ServerState.UNINITIALIZED

    def test_request_after_shutdown(self):
        server = LspServer()
        initialize(server)
        server.handle_message(create_request("shutdown", id=2))

        response = server.handle_message(create_request("initialize", id=3))

        assert response is not None
        assert response.error is not None
        assert response.error.code == SERVER_SHUTTING_DOWN
        assert response.error.message == "Server is shutting down"
        assert server.state == ServerState.SHUTTING_DOWN

    def test_notification_after_shutdown_is_ignored(self):
        server = LspServer()
        initialize(server)
        server.handle_message(create_request("shutdown", id=2))

        response = server.handle_message(create_notification("initialized"))

        assert response is None
        assert server.state == ServerState.SHUTTING_DOWN
