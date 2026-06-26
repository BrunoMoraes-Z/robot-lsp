from __future__ import annotations

import hashlib
from collections import OrderedDict
from dataclasses import dataclass
from typing import Protocol

from .document_store import DocumentStore


TOKEN_TYPES: list[str] = [
    "variable",
    "comment",
    "header",
    "setting",
    "name",
    "keywordNameDefinition",
    "variableOperator",
    "keywordNameCall",
    "settingOperator",
    "control",
    "testCaseName",
    "parameterName",
    "argumentValue",
    "error",
    "documentation",
]
TOKEN_MODIFIERS: list[str] = []
TOKEN_TYPE_INDEX: dict[str, int] = {token_type: index for index, token_type in enumerate(TOKEN_TYPES)}


@dataclass(frozen=True)
class SemanticToken:
    line: int
    start: int
    length: int
    token_type: str
    token_modifiers: int = 0


class SemanticTokenProvider(Protocol):
    def semantic_tokens(self, text: str, *, source_name: str = "document.robot") -> list[SemanticToken]:
        ...


@dataclass(frozen=True)
class SemanticTokensCacheEntry:
    uri: str
    version: int
    content_hash: str
    data: list[int]


class SemanticTokensService:
    def __init__(
        self,
        document_store: DocumentStore,
        token_provider: SemanticTokenProvider,
        *,
        max_cache_entries: int = 50,
    ) -> None:
        self._document_store = document_store
        self._token_provider = token_provider
        self._max_cache_entries = max(0, max_cache_entries)
        self._cache: OrderedDict[str, SemanticTokensCacheEntry] = OrderedDict()

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    def full(self, uri: str) -> dict[str, list[int]] | None:
        document = self._document_store.get(uri)
        if document is None:
            return None
        content_hash = _content_hash(document.text)
        cached = self._cache.get(uri)
        if cached is not None and cached.version == document.version and cached.content_hash == content_hash:
            self._cache.move_to_end(uri)
            return {"data": list(cached.data)}
        source_name = document.path.name if document.path is not None else "document.robot"
        tokens = self._token_provider.semantic_tokens(document.text, source_name=source_name)
        data = encode_semantic_tokens(tokens)
        self._set_cache(uri, document.version, content_hash, data)
        return {"data": data}

    def clear_uri(self, uri: str) -> None:
        self._cache.pop(uri, None)

    def clear(self) -> None:
        self._cache.clear()

    def _set_cache(self, uri: str, version: int, content_hash: str, data: list[int]) -> None:
        if self._max_cache_entries == 0:
            return
        self._cache[uri] = SemanticTokensCacheEntry(
            uri=uri,
            version=version,
            content_hash=content_hash,
            data=list(data),
        )
        self._cache.move_to_end(uri)
        while len(self._cache) > self._max_cache_entries:
            self._cache.popitem(last=False)


def encode_semantic_tokens(tokens: list[SemanticToken]) -> list[int]:
    encoded: list[int] = []
    previous_line = 0
    previous_start = 0
    first = True
    for semantic_token in sorted(tokens, key=lambda token: (token.line, token.start, token.length)):
        token_type_index = TOKEN_TYPE_INDEX.get(semantic_token.token_type)
        if token_type_index is None or semantic_token.length <= 0:
            continue
        delta_line = semantic_token.line if first else semantic_token.line - previous_line
        delta_start = semantic_token.start if first or delta_line != 0 else semantic_token.start - previous_start
        if delta_line < 0 or delta_start < 0:
            continue
        encoded.extend(
            [
                delta_line,
                delta_start,
                semantic_token.length,
                token_type_index,
                semantic_token.token_modifiers,
            ]
        )
        previous_line = semantic_token.line
        previous_start = semantic_token.start
        first = False
    return encoded


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
