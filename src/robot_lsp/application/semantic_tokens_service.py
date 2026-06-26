from __future__ import annotations

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


class SemanticTokensService:
    def __init__(self, document_store: DocumentStore, token_provider: SemanticTokenProvider) -> None:
        self._document_store = document_store
        self._token_provider = token_provider

    def full(self, uri: str) -> dict[str, list[int]] | None:
        document = self._document_store.get(uri)
        if document is None:
            return None
        source_name = document.path.name if document.path is not None else "document.robot"
        tokens = self._token_provider.semantic_tokens(document.text, source_name=source_name)
        return {"data": encode_semantic_tokens(tokens)}


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
