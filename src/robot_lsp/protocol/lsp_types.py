from __future__ import annotations

from enum import Enum, IntEnum
from typing import Any, Final

SERVER_NAME: Final = "robot-lsp"
SERVER_VERSION: Final = "0.1.0"


class ServerState(Enum):
    UNINITIALIZED = "uninitialized"
    RUNNING = "running"
    SHUTTING_DOWN = "shuttingDown"
    EXITED = "exited"


class TextDocumentSyncKind(IntEnum):
    NONE = 0
    FULL = 1
    INCREMENTAL = 2


def server_capabilities() -> dict[str, Any]:
    return {
        "textDocumentSync": {
            "openClose": True,
            "change": TextDocumentSyncKind.FULL,
        },
        "completionProvider": {
            "triggerCharacters": [" ", "$", "@", "&", "%"],
            "resolveProvider": False,
        },
        "hoverProvider": True,
        "definitionProvider": True,
        "referencesProvider": True,
        "documentSymbolProvider": True,
        "foldingRangeProvider": True,
        "selectionRangeProvider": True,
        "renameProvider": {"prepareProvider": True},
        "documentFormattingProvider": True,
        "documentRangeFormattingProvider": True,
        "codeActionProvider": {
            "codeActionKinds": ["quickfix"],
            "resolveProvider": False,
        },
        "workspace": {
            "didChangeConfiguration": {"dynamicRegistration": False},
        },
    }


def initialize_result() -> dict[str, Any]:
    return {
        "capabilities": server_capabilities(),
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
    }
