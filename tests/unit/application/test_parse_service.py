from robot_lsp.application.document_store import DocumentStore
from robot_lsp.application.parse_service import ParseService
from robot_lsp.domain.models import ParseResult


class CountingParser:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def parse_text(self, text: str, *, source_name: str = "document.robot") -> ParseResult:
        self.calls.append((text, source_name))
        return ParseResult(suite=None)


class TestParseService:
    def test_parse_document_reuses_cached_result_for_unchanged_document(self):
        store = DocumentStore()
        parser = CountingParser()
        service = ParseService(store, parser)
        document = store.open(
            uri="file:///c:/projects/cache.robot",
            text="*** Test Cases ***\nT\n",
            version=1,
            language_id="robotframework",
        )

        first = service.parse_document(document)
        second = service.parse_document(document)

        assert first is second
        assert len(parser.calls) == 1
        assert service.cache_size == 1

    def test_parse_document_invalidates_cache_when_text_changes(self):
        store = DocumentStore()
        parser = CountingParser()
        service = ParseService(store, parser)
        uri = "file:///c:/projects/cache.robot"
        document = store.open(uri=uri, text="*** Test Cases ***\nT\n", version=1, language_id="robotframework")
        service.parse_document(document)

        changed = store.change(uri=uri, text="*** Test Cases ***\nChanged\n", version=2)
        assert changed is not None
        service.parse_document(changed)

        assert len(parser.calls) == 2

    def test_parse_document_invalidates_cache_when_version_changes(self):
        store = DocumentStore()
        parser = CountingParser()
        service = ParseService(store, parser)
        uri = "file:///c:/projects/cache.robot"
        document = store.open(uri=uri, text="*** Test Cases ***\nT\n", version=1, language_id="robotframework")
        service.parse_document(document)

        changed = store.change(uri=uri, text="*** Test Cases ***\nT\n", version=2)
        assert changed is not None
        service.parse_document(changed)

        assert len(parser.calls) == 2

    def test_parse_cache_evicts_least_recently_used_entry(self):
        store = DocumentStore()
        parser = CountingParser()
        service = ParseService(store, parser, max_cache_entries=1)
        first = store.open("file:///c:/projects/one.robot", "*** Test Cases ***\nOne\n", 1, "robotframework")
        second = store.open("file:///c:/projects/two.robot", "*** Test Cases ***\nTwo\n", 1, "robotframework")

        service.parse_document(first)
        service.parse_document(second)
        service.parse_document(first)

        assert len(parser.calls) == 3
        assert service.cache_size == 1

    def test_clear_uri_removes_cached_entry(self):
        store = DocumentStore()
        parser = CountingParser()
        service = ParseService(store, parser)
        uri = "file:///c:/projects/cache.robot"
        document = store.open(uri=uri, text="*** Test Cases ***\nT\n", version=1, language_id="robotframework")
        service.parse_document(document)

        service.clear_uri(uri)
        service.parse_document(document)

        assert len(parser.calls) == 2
