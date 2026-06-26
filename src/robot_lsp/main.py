from __future__ import annotations

import argparse
import logging
from collections.abc import Callable

from robot_lsp.application.code_action_service import CodeActionService
from robot_lsp.application.completion_service import CompletionService
from robot_lsp.application.configuration import ConfigurationService
from robot_lsp.application.diagnostic_service import DiagnosticService
from robot_lsp.application.formatting_service import FormattingService
from robot_lsp.application.hover_service import HoverService
from robot_lsp.application.logging_config import apply_log_level, configure_logging
from robot_lsp.application.navigation_service import NavigationService
from robot_lsp.application.parse_service import ParseService
from robot_lsp.application.refactoring_service import RefactoringService
from robot_lsp.application.semantic_tokens_service import SemanticTokensService
from robot_lsp.application.workspace import WorkspaceIndex
from robot_lsp.domain.diagnostics import LspDiagnostic
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser
from robot_lsp.protocol.jsonrpc import (
    JsonRpcMessage,
    JsonRpcProtocolError,
    encode_message,
    parse_message,
    protocol_error_to_response,
)
from robot_lsp.protocol.lsp_types import SERVER_NAME, SERVER_VERSION
from robot_lsp.protocol.server import LspServer
from robot_lsp.protocol.transport_stdio import TransportStdio

LOGGER = logging.getLogger("robot_lsp")
PublishDiagnostics = Callable[[str, list[LspDiagnostic]], None]


def create_server(publish_diagnostics: PublishDiagnostics | None = None) -> LspServer:
    server = LspServer(
        configuration_service=ConfigurationService(),
        log_level_applier=apply_log_level,
    )
    parser = RobotFrameworkParser()
    parse_service = ParseService(server.document_store, parser)
    workspace_index = WorkspaceIndex(parser=parser)

    server.workspace_index = workspace_index
    server.diagnostic_service = DiagnosticService(
        parse_service,
        publish_diagnostics or server.publish_diagnostics,
        workspace_index=workspace_index,
        config_provider=server.configuration_service.config_for_uri,
    )
    server.completion_service = CompletionService(server.document_store, parse_service, workspace_index)
    server.hover_service = HoverService(server.document_store, parse_service)
    server.navigation_service = NavigationService(server.document_store, parse_service, workspace_index)
    server.refactoring_service = RefactoringService(server.document_store, parse_service, workspace_index)
    server.formatting_service = FormattingService(server.document_store)
    server.code_action_service = CodeActionService(server.document_store)
    server.semantic_tokens_service = SemanticTokensService(server.document_store, parser)
    return server


def run_lsp_loop(transport: TransportStdio | None = None, server: LspServer | None = None) -> int:
    transport = transport or TransportStdio()

    def publish(uri: str, diagnostics: list[LspDiagnostic]) -> None:
        notification = JsonRpcMessage(
            method="textDocument/publishDiagnostics",
            params={"uri": uri, "diagnostics": [diagnostic.to_lsp() for diagnostic in diagnostics]},
        )
        transport.write_message(encode_message(notification))

    server = server or create_server(publish)
    LOGGER.info("%s %s started", SERVER_NAME, SERVER_VERSION)

    while not server.exit_requested:
        try:
            raw_message = transport.read_message()
        except Exception:
            LOGGER.exception("Failed to read LSP message")
            return 1

        if raw_message is None:
            break

        try:
            response = server.handle_message(parse_message(raw_message))
        except JsonRpcProtocolError as exc:
            response = protocol_error_to_response(exc)

        if response is not None:
            transport.write_message(encode_message(response))
        _flush_outgoing_messages(server, transport)

    _flush_outgoing_messages(server, transport)
    return server.exit_code if server.exit_code is not None else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Robot Framework Language Server")
    parser.add_argument("--version", action="store_true", help="Print server version and exit")
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="warning",
        help="Log level for stderr logging",
    )
    args = parser.parse_args(argv)

    if args.version:
        print(f"{SERVER_NAME} {SERVER_VERSION}")
        return 0

    configure_logging(args.log_level)
    return run_lsp_loop()


def _flush_outgoing_messages(server: LspServer, transport: TransportStdio) -> None:
    while server.outgoing_requests:
        transport.write_message(encode_message(server.outgoing_requests.pop(0)))
    while server.outgoing_notifications:
        transport.write_message(encode_message(server.outgoing_notifications.pop(0)))
