from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlparse


@dataclass
class Document:
    uri: str
    path: Path | None
    language_id: str
    version: int
    text: str

    @property
    def lines(self) -> list[str]:
        return self.text.splitlines(keepends=True)


class DocumentStore:
    _documents: dict[str, Document] = field(default_factory=dict)

    def open(self, uri: str, text: str, version: int, language_id: str) -> Document:
        doc = Document(
            uri=uri,
            path=uri_to_path(uri),
            language_id=language_id,
            version=version,
            text=text,
        )
        self._documents[uri] = doc
        return doc

    def change(self, uri: str, text: str, version: int) -> Document | None:
        doc = self._documents.get(uri)
        if doc is None:
            return None
        doc.text = text
        doc.version = version
        return doc

    def close(self, uri: str) -> Document | None:
        return self._documents.pop(uri, None)

    def get(self, uri: str) -> Document | None:
        return self._documents.get(uri)

    def get_open_uris(self) -> list[str]:
        return list(self._documents.keys())


def uri_to_path(uri: str) -> Path | None:
    if not uri.startswith("file://"):
        return None
    path_str = unquote(urlparse(uri).path)
    if path_str.startswith("/") and ":" in path_str:
        path_str = path_str.lstrip("/")
    return Path(path_str)


def path_to_uri(path: Path) -> str:
    return path.resolve().as_uri()
