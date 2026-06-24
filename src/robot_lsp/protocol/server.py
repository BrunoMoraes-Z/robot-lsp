from __future__ import annotations

from typing import Any

from .dispatch import CancelToken, MethodDispatcher
from .jsonrpc import (
    SERVER_NOT_INITIALIZED,
    SERVER_SHUTTING_DOWN,
    JsonRpcMessage,
    create_error_response,
)
from .lsp_types import ServerState, initialize_result


class LspServer:
    def __init__(self) -> None:
        self.state = ServerState.UNINITIALIZED
        self.process_id: int | None = None
        self.root_uri: str | None = None
        self.client_capabilities: dict[str, Any] = {}
        self.exit_requested = False
        self.exit_code: int | None = None

        self._dispatcher = MethodDispatcher()
        self._dispatcher.register("initialize", self._handle_initialize)
        self._dispatcher.register("initialized", self._handle_initialized)
        self._dispatcher.register("shutdown", self._handle_shutdown)
        self._dispatcher.register("exit", self._handle_exit)

    def handle_message(self, message: JsonRpcMessage) -> JsonRpcMessage | None:
        if message.method == "exit":
            return self._dispatcher.dispatch(message)

        if self.state == ServerState.EXITED:
            return None

        if self.state == ServerState.UNINITIALIZED and message.method != "initialize":
            if message.is_request:
                return create_error_response(
                    message.id,
                    SERVER_NOT_INITIALIZED,
                    "Server not initialized",
                )
            return None

        if self.state == ServerState.SHUTTING_DOWN:
            if message.is_request:
                return create_error_response(
                    message.id,
                    SERVER_SHUTTING_DOWN,
                    "Server is shutting down",
                )
            return None

        return self._dispatcher.dispatch(message)

    def _handle_initialize(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> dict[str, Any]:
        if isinstance(params, dict):
            process_id = params.get("processId")
            self.process_id = process_id if isinstance(process_id, int) else None
            root_uri = params.get("rootUri")
            self.root_uri = root_uri if isinstance(root_uri, str) else None
            capabilities = params.get("capabilities")
            self.client_capabilities = capabilities if isinstance(capabilities, dict) else {}

        self.state = ServerState.RUNNING
        return initialize_result()

    def _handle_initialized(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> None:
        return None

    def _handle_shutdown(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> None:
        self.state = ServerState.SHUTTING_DOWN
        return None

    def _handle_exit(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> None:
        self.exit_requested = True
        self.exit_code = 0 if self.state == ServerState.SHUTTING_DOWN else 1
        self.state = ServerState.EXITED
        return None
