from __future__ import annotations

from typing import Protocol

from .document_store import Document, DocumentStore
from robot_lsp.domain.models import ParseResult


class TextParser(Protocol):
    def parse_text(self, text: str, *, source_name: str = "document.robot") -> ParseResult:
        ...


class ParseService:
    def __init__(self, document_store: DocumentStore, parser: TextParser) -> None:
        self._document_store = document_store
        self._parser = parser

    def parse_uri(self, uri: str) -> ParseResult | None:
        document = self._document_store.get(uri)
        if document is None:
            return None
        return self.parse_document(document)

    def parse_document(self, document: Document) -> ParseResult:
        source_name = document.path.name if document.path is not None else "document.robot"
        return self._parser.parse_text(document.text, source_name=source_name)
