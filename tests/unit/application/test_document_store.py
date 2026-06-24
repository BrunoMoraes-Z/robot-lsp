from pathlib import Path

from robot_lsp.application.document_store import DocumentStore, path_to_uri, uri_to_path
from robot_lsp.domain.models import LspPosition, LspRange


class TestDocumentStore:
    def test_open_document(self):
        store = DocumentStore()

        doc = store.open(
            uri="file:///c:/projects/test.robot",
            text="*** Test Cases ***\nExample\n",
            version=1,
            language_id="robotframework",
        )

        assert doc.uri == "file:///c:/projects/test.robot"
        assert doc.path == Path("c:/projects/test.robot")
        assert doc.version == 1
        assert doc.language_id == "robotframework"
        assert store.get(doc.uri) is doc

    def test_change_document_full(self):
        store = DocumentStore()
        uri = "file:///c:/projects/test.robot"
        store.open(uri=uri, text="old", version=1, language_id="robotframework")

        doc = store.change(uri=uri, text="new", version=2)

        assert doc is not None
        assert doc.text == "new"
        assert doc.version == 2

    def test_change_missing_document_returns_none(self):
        store = DocumentStore()

        assert store.change("file:///missing.robot", "x", 1) is None

    def test_close_document(self):
        store = DocumentStore()
        uri = "file:///c:/projects/test.robot"
        doc = store.open(uri=uri, text="x", version=1, language_id="robotframework")

        closed = store.close(uri)

        assert closed is doc
        assert store.get(uri) is None

    def test_get_all_and_open_uris(self):
        store = DocumentStore()
        uri1 = "file:///c:/projects/a.robot"
        uri2 = "file:///c:/projects/b.robot"
        doc1 = store.open(uri=uri1, text="a", version=1, language_id="robotframework")
        doc2 = store.open(uri=uri2, text="b", version=1, language_id="robotframework")

        assert store.get_open_uris() == [uri1, uri2]
        assert store.get_all() == [doc1, doc2]

    def test_uri_to_path(self):
        assert uri_to_path("file:///c:/projects/test.robot") == Path("c:/projects/test.robot")

    def test_uri_to_path_decodes_percent_encoding(self):
        assert uri_to_path("file:///c:/projects/my%20suite.robot") == Path(
            "c:/projects/my suite.robot"
        )

    def test_uri_to_path_returns_none_for_non_file_uri(self):
        assert uri_to_path("untitled:test.robot") is None

    def test_path_to_uri(self, tmp_path):
        file_path = tmp_path / "test.robot"

        assert path_to_uri(file_path).startswith("file://")
        assert path_to_uri(file_path).endswith("test.robot")

    def test_range_text_extraction(self):
        store = DocumentStore()
        doc = store.open(
            uri="file:///c:/projects/test.robot",
            text="*** Test Cases ***\nExample\n    Log    Hello\n",
            version=1,
            language_id="robotframework",
        )

        text = doc.text_for_range(
            LspRange(
                start=LspPosition(line=1, character=0),
                end=LspPosition(line=1, character=7),
            )
        )

        assert text == "Example"
