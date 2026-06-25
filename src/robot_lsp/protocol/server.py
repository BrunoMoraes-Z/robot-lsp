from __future__ import annotations

from collections.abc import Callable
from typing import Any

from robot_lsp.application.completion_service import CompletionService
from robot_lsp.application.code_action_service import CodeActionService
from robot_lsp.application.configuration import ConfigurationService, LogLevel
from robot_lsp.application.diagnostic_service import DiagnosticService
from robot_lsp.application.document_store import DocumentStore
from robot_lsp.application.formatting_service import FormattingService
from robot_lsp.application.hover_service import HoverService
from robot_lsp.application.navigation_service import NavigationService
from robot_lsp.application.refactoring_service import RefactoringService
from robot_lsp.domain.diagnostics import LspDiagnostic
from robot_lsp.domain.models import LspPosition, LspRange

from .dispatch import CancelToken, MethodDispatcher
from .jsonrpc import (
    SERVER_NOT_INITIALIZED,
    SERVER_SHUTTING_DOWN,
    JsonRpcMessage,
    create_error_response,
    create_notification,
    create_request,
)
from .lsp_types import ServerState, initialize_result


class LspServer:
    def __init__(
        self,
        diagnostic_service: DiagnosticService | None = None,
        completion_service: CompletionService | None = None,
        hover_service: HoverService | None = None,
        navigation_service: NavigationService | None = None,
        refactoring_service: RefactoringService | None = None,
        formatting_service: FormattingService | None = None,
        code_action_service: CodeActionService | None = None,
        configuration_service: ConfigurationService | None = None,
        log_level_applier: Callable[[LogLevel], None] | None = None,
    ) -> None:
        self.state = ServerState.UNINITIALIZED
        self.process_id: int | None = None
        self.root_uri: str | None = None
        self.workspace_folders: list[dict[str, str]] = []
        self.client_capabilities: dict[str, Any] = {}
        self.exit_requested = False
        self.exit_code: int | None = None
        self.document_store = DocumentStore()
        self.diagnostic_service = diagnostic_service
        self.completion_service = completion_service
        self.hover_service = hover_service
        self.navigation_service = navigation_service
        self.refactoring_service = refactoring_service
        self.formatting_service = formatting_service
        self.code_action_service = code_action_service
        self.configuration_service = configuration_service or ConfigurationService()
        self.log_level_applier = log_level_applier
        self.outgoing_notifications: list[JsonRpcMessage] = []
        self.outgoing_requests: list[JsonRpcMessage] = []
        self._next_outgoing_request_id = 1
        self._next_progress_token_id = 1
        self._pending_configuration_requests: dict[int, list[str | None]] = {}

        self._dispatcher = MethodDispatcher()
        self._dispatcher.register("initialize", self._handle_initialize)
        self._dispatcher.register("initialized", self._handle_initialized)
        self._dispatcher.register("shutdown", self._handle_shutdown)
        self._dispatcher.register("exit", self._handle_exit)
        self._dispatcher.register("textDocument/didOpen", self._handle_did_open)
        self._dispatcher.register("textDocument/didChange", self._handle_did_change)
        self._dispatcher.register("textDocument/didClose", self._handle_did_close)
        self._dispatcher.register("textDocument/completion", self._handle_completion)
        self._dispatcher.register("textDocument/hover", self._handle_hover)
        self._dispatcher.register("textDocument/definition", self._handle_definition)
        self._dispatcher.register("textDocument/references", self._handle_references)
        self._dispatcher.register("textDocument/documentSymbol", self._handle_document_symbol)
        self._dispatcher.register("textDocument/foldingRange", self._handle_folding_range)
        self._dispatcher.register("textDocument/selectionRange", self._handle_selection_range)
        self._dispatcher.register("textDocument/prepareRename", self._handle_prepare_rename)
        self._dispatcher.register("textDocument/rename", self._handle_rename)
        self._dispatcher.register("textDocument/formatting", self._handle_formatting)
        self._dispatcher.register("textDocument/rangeFormatting", self._handle_range_formatting)
        self._dispatcher.register("textDocument/codeAction", self._handle_code_action)
        self._dispatcher.register("workspace/didChangeConfiguration", self._handle_did_change_configuration)

    def handle_message(self, message: JsonRpcMessage) -> JsonRpcMessage | None:
        if message.is_response:
            self._handle_response(message)
            return None

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
            self.workspace_folders = _workspace_folders(params.get("workspaceFolders"), self.root_uri)
            capabilities = params.get("capabilities")
            self.client_capabilities = capabilities if isinstance(capabilities, dict) else {}
            initialization_options = params.get("initializationOptions")
            if isinstance(initialization_options, dict):
                old_log_level = self.configuration_service.config.log_level
                self.configuration_service.update(initialization_options)
                self._apply_log_level_if_changed(old_log_level)

        self.state = ServerState.RUNNING
        return initialize_result()

    def _handle_initialized(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> None:
        self.request_workspace_configuration()
        return None

    def request_workspace_configuration(self) -> JsonRpcMessage | None:
        if not self._client_supports_workspace_configuration():
            return None
        progress_token = self.start_work_done_progress(
            "Load Robot Framework configuration",
            "Requesting workspace configuration",
        )
        scopes: list[str | None] = [None]
        scopes.extend(folder["uri"] for folder in self.workspace_folders if isinstance(folder.get("uri"), str))
        request_id = self._next_outgoing_id()
        self._pending_configuration_requests[request_id] = scopes
        request = create_request(
            "workspace/configuration",
            id=request_id,
            params={
                "items": [
                    ({"section": "robot.lsp"} if scope_uri is None else {"scopeUri": scope_uri, "section": "robot.lsp"})
                    for scope_uri in scopes
                ]
            },
        )
        self.outgoing_requests.append(request)
        if progress_token is not None:
            self.report_work_done_progress(progress_token, "Waiting for client settings")
            self.end_work_done_progress(progress_token, "Configuration request sent")
        return request

    def start_work_done_progress(self, title: str, message: str | None = None) -> str | None:
        if not self._client_supports_work_done_progress():
            return None
        token = f"robot-lsp-progress-{self._next_progress_token_id}"
        self._next_progress_token_id += 1
        self.outgoing_requests.append(
            create_request(
                "window/workDoneProgress/create",
                id=self._next_outgoing_id(),
                params={"token": token},
            )
        )
        value: dict[str, Any] = {"kind": "begin", "title": title}
        if message is not None:
            value["message"] = message
        self.outgoing_notifications.append(create_notification("$/progress", params={"token": token, "value": value}))
        return token

    def report_work_done_progress(self, token: str, message: str | None = None, percentage: int | None = None) -> None:
        value: dict[str, Any] = {"kind": "report"}
        if message is not None:
            value["message"] = message
        if percentage is not None:
            value["percentage"] = percentage
        self.outgoing_notifications.append(create_notification("$/progress", params={"token": token, "value": value}))

    def end_work_done_progress(self, token: str, message: str | None = None) -> None:
        value: dict[str, Any] = {"kind": "end"}
        if message is not None:
            value["message"] = message
        self.outgoing_notifications.append(create_notification("$/progress", params={"token": token, "value": value}))

    def _next_outgoing_id(self) -> int:
        request_id = self._next_outgoing_request_id
        self._next_outgoing_request_id += 1
        return request_id

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
        self._dispatcher.shutdown()
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
        if self._diagnostics_enabled(uri) and self.diagnostic_service is not None:
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
        if self._diagnostics_enabled(uri) and self.diagnostic_service is not None:
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

    def _handle_did_change_configuration(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> None:
        if not isinstance(params, dict):
            return None
        settings = params.get("settings")
        if not isinstance(settings, dict):
            return None
        old_diagnostics_enabled = {uri: self._diagnostics_enabled(uri) for uri in self.document_store.get_open_uris()}
        old_log_level = self.configuration_service.config.log_level
        self.configuration_service.update(settings)
        self._apply_log_level_if_changed(old_log_level)
        if self.diagnostic_service is not None:
            for uri in self.document_store.get_open_uris():
                if old_diagnostics_enabled.get(uri, True) and not self._diagnostics_enabled(uri):
                    self.diagnostic_service.clear(uri)
        return None

    def _diagnostics_enabled(self, uri: str | None = None) -> bool:
        return self.configuration_service.config_for_uri(uri).diagnostics.enable

    def _apply_log_level_if_changed(self, old_log_level: LogLevel) -> None:
        new_log_level = self.configuration_service.config.log_level
        if self.log_level_applier is not None and new_log_level != old_log_level:
            self.log_level_applier(new_log_level)

    def _handle_completion(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> dict[str, Any] | None:
        if self.completion_service is None or not isinstance(params, dict):
            return {"isIncomplete": False, "items": []}

        text_document = params.get("textDocument")
        position = params.get("position")
        context = params.get("context")
        if not isinstance(text_document, dict) or not isinstance(position, dict):
            return {"isIncomplete": False, "items": []}

        uri = text_document.get("uri")
        line = position.get("line")
        character = position.get("character")
        if not isinstance(uri, str) or not isinstance(line, int) or not isinstance(character, int):
            return {"isIncomplete": False, "items": []}

        trigger_character = None
        if isinstance(context, dict) and isinstance(context.get("triggerCharacter"), str):
            trigger_character = context["triggerCharacter"]

        completion = self.completion_service.compute_completion(
            uri,
            LspPosition(line=line, character=character),
            trigger_character=trigger_character,
            snippets_enabled=self.configuration_service.config_for_uri(uri).completion.snippets,
        )
        if completion is None:
            return {"isIncomplete": False, "items": []}
        return completion.to_lsp()

    def _handle_response(self, message: JsonRpcMessage) -> None:
        if not isinstance(message.id, int):
            return None
        scopes = self._pending_configuration_requests.pop(message.id, None)
        if scopes is None or message.error is not None or not isinstance(message.result, list):
            return None

        old_log_level = self.configuration_service.config.log_level
        old_diagnostics_enabled = {uri: self._diagnostics_enabled(uri) for uri in self.document_store.get_open_uris()}
        for scope_uri, raw_settings in zip(scopes, message.result):
            if isinstance(raw_settings, dict):
                self.configuration_service.update(raw_settings, scope_uri=scope_uri)
        self._apply_log_level_if_changed(old_log_level)
        if self.diagnostic_service is not None:
            for uri in self.document_store.get_open_uris():
                if old_diagnostics_enabled.get(uri, True) and not self._diagnostics_enabled(uri):
                    self.diagnostic_service.clear(uri)
        return None

    def _client_supports_workspace_configuration(self) -> bool:
        workspace = self.client_capabilities.get("workspace")
        return isinstance(workspace, dict) and workspace.get("configuration") is True

    def _client_supports_work_done_progress(self) -> bool:
        window = self.client_capabilities.get("window")
        return isinstance(window, dict) and window.get("workDoneProgress") is True

    def _handle_hover(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> dict[str, Any] | None:
        if self.hover_service is None or not isinstance(params, dict):
            return None

        text_document = params.get("textDocument")
        position = params.get("position")
        if not isinstance(text_document, dict) or not isinstance(position, dict):
            return None

        uri = text_document.get("uri")
        line = position.get("line")
        character = position.get("character")
        if not isinstance(uri, str) or not isinstance(line, int) or not isinstance(character, int):
            return None

        hover = self.hover_service.compute_hover(uri, LspPosition(line=line, character=character))
        return hover.to_lsp() if hover is not None else None

    def _handle_definition(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> list[dict[str, Any]]:
        parsed = self._text_document_position(params)
        if self.navigation_service is None or parsed is None:
            return []
        uri, position = parsed
        return self.navigation_service.definition(uri, position)

    def _handle_references(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> list[dict[str, Any]]:
        parsed = self._text_document_position(params)
        if self.navigation_service is None or parsed is None:
            return []
        uri, position = parsed
        include_declaration = True
        if isinstance(params, dict) and isinstance(params.get("context"), dict):
            include_declaration = params["context"].get("includeDeclaration", True) is not False
        return self.navigation_service.references(
            uri,
            position,
            include_declaration=include_declaration,
        )

    def _handle_document_symbol(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> list[dict[str, Any]]:
        uri = self._text_document_uri(params)
        if self.navigation_service is None or uri is None:
            return []
        return self.navigation_service.document_symbols(uri)

    def _handle_folding_range(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> list[dict[str, Any]]:
        uri = self._text_document_uri(params)
        if self.navigation_service is None or uri is None:
            return []
        return self.navigation_service.folding_ranges(uri)

    def _handle_selection_range(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> list[dict[str, Any]]:
        uri = self._text_document_uri(params)
        if self.navigation_service is None or uri is None or not isinstance(params, dict):
            return []
        raw_positions = params.get("positions")
        if not isinstance(raw_positions, list):
            return []
        positions = []
        for raw_position in raw_positions:
            if not isinstance(raw_position, dict):
                continue
            line = raw_position.get("line")
            character = raw_position.get("character")
            if isinstance(line, int) and isinstance(character, int):
                positions.append(LspPosition(line=line, character=character))
        return self.navigation_service.selection_ranges(uri, positions)

    def _text_document_position(
        self,
        params: dict[str, Any] | list[Any] | None,
    ) -> tuple[str, LspPosition] | None:
        if not isinstance(params, dict):
            return None
        uri = self._text_document_uri(params)
        position = params.get("position")
        if uri is None or not isinstance(position, dict):
            return None
        line = position.get("line")
        character = position.get("character")
        if not isinstance(line, int) or not isinstance(character, int):
            return None
        return uri, LspPosition(line=line, character=character)

    def _text_document_uri(self, params: dict[str, Any] | list[Any] | None) -> str | None:
        if not isinstance(params, dict):
            return None
        text_document = params.get("textDocument")
        if not isinstance(text_document, dict):
            return None
        uri = text_document.get("uri")
        return uri if isinstance(uri, str) else None

    def _handle_prepare_rename(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> dict[str, Any] | None:
        parsed = self._text_document_position(params)
        if self.refactoring_service is None or parsed is None:
            return None
        uri, position = parsed
        return self.refactoring_service.prepare_rename(uri, position)

    def _handle_rename(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> dict[str, Any] | None:
        parsed = self._text_document_position(params)
        if self.refactoring_service is None or parsed is None or not isinstance(params, dict):
            return None
        new_name = params.get("newName")
        if not isinstance(new_name, str):
            return None
        uri, position = parsed
        return self.refactoring_service.rename(uri, position, new_name)

    def _handle_formatting(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> list[dict[str, Any]]:
        uri = self._text_document_uri(params)
        if self.formatting_service is None or uri is None or not isinstance(params, dict):
            return []
        options = params.get("options") if isinstance(params.get("options"), dict) else None
        return self.formatting_service.format_document(uri, options)

    def _handle_range_formatting(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> list[dict[str, Any]]:
        uri = self._text_document_uri(params)
        if self.formatting_service is None or uri is None or not isinstance(params, dict):
            return []
        raw_range = params.get("range")
        if not isinstance(raw_range, dict):
            return []
        range_ = self._parse_range(raw_range)
        if range_ is None:
            return []
        options = params.get("options") if isinstance(params.get("options"), dict) else None
        return self.formatting_service.format_range(uri, range_, options)

    def _handle_code_action(
        self,
        params: dict[str, Any] | list[Any] | None,
        token: CancelToken,
    ) -> list[dict[str, Any]]:
        uri = self._text_document_uri(params)
        if self.code_action_service is None or uri is None or not isinstance(params, dict):
            return []
        raw_range = params.get("range") if isinstance(params.get("range"), dict) else None
        context = params.get("context") if isinstance(params.get("context"), dict) else None
        return self.code_action_service.code_actions(uri, raw_range, context)

    def _parse_range(self, raw_range: dict[str, Any]) -> LspRange | None:
        start = raw_range.get("start")
        end = raw_range.get("end")
        if not isinstance(start, dict) or not isinstance(end, dict):
            return None
        start_line = start.get("line")
        start_character = start.get("character")
        end_line = end.get("line")
        end_character = end.get("character")
        if not all(isinstance(value, int) for value in [start_line, start_character, end_line, end_character]):
            return None
        return LspRange(
            LspPosition(start_line, start_character),
            LspPosition(end_line, end_character),
        )


def _workspace_folders(raw: Any, root_uri: str | None) -> list[dict[str, str]]:
    folders: list[dict[str, str]] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            uri = item.get("uri")
            name = item.get("name")
            if isinstance(uri, str):
                folders.append({"uri": uri, "name": name if isinstance(name, str) else uri})
    if not folders and root_uri is not None:
        folders.append({"uri": root_uri, "name": root_uri})
    return folders
