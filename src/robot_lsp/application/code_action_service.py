from __future__ import annotations

from typing import Any

from .document_store import DocumentStore


class CodeActionService:
    def __init__(self, document_store: DocumentStore) -> None:
        self._document_store = document_store

    def code_actions(
        self,
        uri: str,
        range_: dict[str, Any] | None,
        context: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if self._document_store.get(uri) is None:
            return []
        diagnostics = [] if context is None else context.get("diagnostics", [])
        actions: list[dict[str, Any]] = []
        for diagnostic in diagnostics if isinstance(diagnostics, list) else []:
            if not isinstance(diagnostic, dict):
                continue
            code = diagnostic.get("code")
            if code == "parse_error":
                actions.append(
                    {
                        "title": "Show Robot Framework parse error",
                        "kind": "quickfix",
                        "diagnostics": [diagnostic],
                        "isPreferred": False,
                    }
                )
            elif code == "import_not_found":
                actions.append(
                    {
                        "title": "Check import path",
                        "kind": "quickfix",
                        "diagnostics": [diagnostic],
                        "isPreferred": False,
                    }
                )
        return actions
