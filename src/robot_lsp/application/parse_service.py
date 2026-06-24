from __future__ import annotations

import hashlib
from collections import OrderedDict
from dataclasses import dataclass
from typing import Protocol

from .document_store import Document, DocumentStore
from robot_lsp.domain.models import ParseResult


class TextParser(Protocol):
    def parse_text(self, text: str, *, source_name: str = "document.robot") -> ParseResult:
        ...


@dataclass(frozen=True)
class ParseCacheEntry:
    uri: str
    version: int
    content_hash: str
    result: ParseResult


class ParseService:
    def __init__(self, document_store: DocumentStore, parser: TextParser, *, max_cache_entries: int = 50) -> None:
        self._document_store = document_store
        self._parser = parser
        self._max_cache_entries = max(0, max_cache_entries)
        self._cache: OrderedDict[str, ParseCacheEntry] = OrderedDict()

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    def parse_uri(self, uri: str) -> ParseResult | None:
        document = self._document_store.get(uri)
        if document is None:
            return None
        return self.parse_document(document)

    def parse_document(self, document: Document) -> ParseResult:
        content_hash = _content_hash(document.text)
        cached = self._cache.get(document.uri)
        if (
            cached is not None
            and cached.version == document.version
            and cached.content_hash == content_hash
        ):
            self._cache.move_to_end(document.uri)
            return cached.result

        source_name = document.path.name if document.path is not None else "document.robot"
        result = self._parser.parse_text(document.text, source_name=source_name)
        self._set_cache(document, content_hash, result)
        return result

    def clear_uri(self, uri: str) -> None:
        self._cache.pop(uri, None)

    def clear(self) -> None:
        self._cache.clear()

    def _set_cache(self, document: Document, content_hash: str, result: ParseResult) -> None:
        if self._max_cache_entries == 0:
            return
        self._cache[document.uri] = ParseCacheEntry(
            uri=document.uri,
            version=document.version,
            content_hash=content_hash,
            result=result,
        )
        self._cache.move_to_end(document.uri)
        while len(self._cache) > self._max_cache_entries:
            self._cache.popitem(last=False)


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
