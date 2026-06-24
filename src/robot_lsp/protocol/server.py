from __future__ import annotations

from typing import Any

from robot_lsp.application.diagnostic_service import DiagnosticService
from robot_lsp.application.document_store import DocumentStore
from robot_lsp.domain.diagnostics import LspDiagnostic

from .dispatch import CancelToken, MethodDispatcher
from .jsonrpc import (
    SERVER_NOT_INITIALIZED,
    SERVER_SHUTTING_DOWN,
    JsonRpcMessage,
    create_error_response,
    create_notification,
)
from .lsp_types import ServerState, initialize_result


class LspServer:
    def __init__(self, diagnostic_service: DiagnosticService | None = None) -> None:
        self.state = ServerState.UNINITIALIZED
        self.process_id: int | None = None
        self.root_uri: str | None = None
        self.client_capabilities: dict[str, Any] = {}
        self.exit_requested = False
        self.exit_code: int | None = None
        self.document_store = DocumentStore()
        self.diagnostic_service = diagnostic_service
        self.outgoing_notifications: list[JsonRpcMessage] = []

        self._dispatcher = MethodDispatcher()
        self._dispatcher.register("initialize", self._handle_initialize)
        self._dispatcher.register("initialized", self._handle_initialized)
        self._dispatcher.register("shutdown", self._handle_shutdown)
        self._dispatcher.register("exit", self._handle_exit)
        self._dispatcher.register("textDocument/didOpen", self._handle_did_open)
        self._dispatcher.register("textDocument/didChange", self._handle_did_change)
        self._dispatcher.register("textDocument/didClose", self._handle_did_close)

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

    def _handle_did_open(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> None:
        if not isinstance(params, dict):
            return None
        text_document = params.get("textDocument")
        if not isinstance(text_document, dict):
            return None

        uri = text_document.get("uri")
        language_id = text_document.get("languageId")
        version = text_document.get("version")
        text = text_document.get("text")
        if not isinstance(uri, str) or not isinstance(text, str):
            return None

        self.document_store.open(
            uri=uri,
            text=text,
            version=version if isinstance(version, int) else 0,
            language_id=language_id if isinstance(language_id, str) else "robotframework",
        )
        if self.diagnostic_service is not None:
            self.diagnostic_service.schedule_diagnostics(uri)
        return None

    def _handle_did_change(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> None:
        if not isinstance(params, dict):
            return None

        text_document = params.get("textDocument")
        content_changes = params.get("contentChanges")
        if not isinstance(text_document, dict) or not isinstance(content_changes, list):
            return None

        uri = text_document.get("uri")
        version = text_document.get("version")
        if not isinstance(uri, str):
            return None

        text = None
        for change in content_changes:
            if isinstance(change, dict) and isinstance(change.get("text"), str):
                text = change["text"]
        if text is None:
            return None

        self.document_store.change(
            uri=uri,
            text=text,
            version=version if isinstance(version, int) else 0,
        )
        if self.diagnostic_service is not None:
            self.diagnostic_service.schedule_diagnostics(uri)
        return None

    def _handle_did_close(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> None:
        if not isinstance(params, dict):
            return None
        text_document = params.get("textDocument")
        if not isinstance(text_document, dict):
            return None
        uri = text_document.get("uri")
        if isinstance(uri, str):
            self.document_store.close(uri)
            if self.diagnostic_service is not None:
                self.diagnostic_service.clear(uri)
        return None

    def publish_diagnostics(self, uri: str, diagnostics: list[LspDiagnostic]) -> None:
        self.outgoing_notifications.append(
            create_notification(
                "textDocument/publishDiagnostics",
                params={
                    "uri": uri,
                    "diagnostics": [diagnostic.to_lsp() for diagnostic in diagnostics],
                },
            )
        )
