from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from robot_lsp.application.workspace import WorkspaceIndex
from robot_lsp.protocol.jsonrpc import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    JsonRpcMessage,
    JsonRpcProtocolError,
    create_error_response,
    create_response,
    encode_message,
    parse_message,
    protocol_error_to_response,
)
from robot_lsp.protocol.transport_stdio import TransportStdio


class WorkerServer:
    def __init__(self) -> None:
        self.exit_requested = False

    def handle_message(self, message: JsonRpcMessage) -> JsonRpcMessage | None:
        if message.is_notification:
            if message.method == "exit":
                self.exit_requested = True
            return None
        if not message.is_request:
            return create_error_response(message.id, METHOD_NOT_FOUND, "Expected request")
        try:
            if message.method == "worker/ping":
                return create_response(message.id, {"ok": True, "pid": os.getpid()})
            if message.method == "workspace/scan":
                return create_response(message.id, self._scan_workspace(message.params))
            if message.method == "shutdown":
                self.exit_requested = True
                return create_response(message.id, None)
        except JsonRpcProtocolError as exc:
            return protocol_error_to_response(exc, id=message.id)
        except Exception as exc:
            return create_error_response(message.id, INTERNAL_ERROR, "Internal error", str(exc))
        return create_error_response(message.id, METHOD_NOT_FOUND, f"Method not found: {message.method}")

    def _scan_workspace(self, params: dict[str, Any] | list[Any] | None) -> dict[str, Any]:
        if not isinstance(params, dict) or not isinstance(params.get("root"), str):
            raise JsonRpcProtocolError(INVALID_PARAMS, "workspace/scan requires root")
        root = Path(params["root"])
        if not root.exists() or not root.is_dir():
            raise JsonRpcProtocolError(INVALID_PARAMS, "workspace/scan root must be an existing directory")

        index = WorkspaceIndex()
        index.scan(root)
        entries = index.entries
        return {
            "files": len(entries),
            "keywords": sum(len(entry.suite.keywords) for entry in entries.values()),
            "variables": sum(len(entry.suite.variables) for entry in entries.values()),
        }


def run_worker_loop(transport: TransportStdio | None = None, server: WorkerServer | None = None) -> int:
    transport = transport or TransportStdio()
    server = server or WorkerServer()
    while not server.exit_requested:
        try:
            raw_message = transport.read_message()
        except Exception as exc:
            response = create_error_response(None, INTERNAL_ERROR, "Failed to read worker message", str(exc))
            transport.write_message(encode_message(response))
            return 1
        if raw_message is None:
            break
        try:
            response = server.handle_message(parse_message(raw_message))
        except JsonRpcProtocolError as exc:
            response = protocol_error_to_response(exc)
        if response is not None:
            transport.write_message(encode_message(response))
    return 0


def main() -> int:
    return run_worker_loop()


if __name__ == "__main__":
    sys.exit(main())
