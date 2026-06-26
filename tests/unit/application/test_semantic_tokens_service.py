from robot_lsp.application.document_store import DocumentStore
from robot_lsp.application.semantic_tokens_service import SemanticToken, SemanticTokensService, encode_semantic_tokens


class StubTokenProvider:
    def __init__(self) -> None:
        self.calls = 0

    def semantic_tokens(self, text: str, *, source_name: str = "document.robot") -> list[SemanticToken]:
        self.calls += 1
        return [
            SemanticToken(line=0, start=0, length=3, token_type="header"),
            SemanticToken(line=0, start=5, length=4, token_type="variable"),
            SemanticToken(line=2, start=2, length=7, token_type="keywordNameCall"),
        ]


class TestSemanticTokensService:
    def test_encode_semantic_tokens_uses_lsp_delta_format(self):
        data = encode_semantic_tokens(StubTokenProvider().semantic_tokens(""))

        assert data == [0, 0, 3, 2, 0, 0, 5, 4, 0, 0, 2, 2, 7, 7, 0]

    def test_full_returns_none_for_missing_document(self):
        service = SemanticTokensService(DocumentStore(), StubTokenProvider())

        assert service.full("file:///missing.robot") is None

    def test_full_returns_data_for_open_document(self):
        store = DocumentStore()
        store.open("file:///c:/projects/example.robot", "*** Settings ***\n", 1, "robotframework")
        service = SemanticTokensService(store, StubTokenProvider())

        assert service.full("file:///c:/projects/example.robot") == {
            "data": [0, 0, 3, 2, 0, 0, 5, 4, 0, 0, 2, 2, 7, 7, 0]
        }

    def test_full_reuses_cache_for_unchanged_document(self):
        store = DocumentStore()
        store.open("file:///c:/projects/example.robot", "*** Settings ***\n", 1, "robotframework")
        provider = StubTokenProvider()
        service = SemanticTokensService(store, provider)

        first = service.full("file:///c:/projects/example.robot")
        second = service.full("file:///c:/projects/example.robot")

        assert first == second
        assert provider.calls == 1
        assert service.cache_size == 1

    def test_full_invalidates_cache_when_document_changes(self):
        store = DocumentStore()
        uri = "file:///c:/projects/example.robot"
        store.open(uri, "*** Settings ***\n", 1, "robotframework")
        provider = StubTokenProvider()
        service = SemanticTokensService(store, provider)

        service.full(uri)
        store.change(uri, "*** Variables ***\n", 2)
        service.full(uri)

        assert provider.calls == 2
        assert service.cache_size == 1

    def test_clear_uri_removes_cached_document(self):
        store = DocumentStore()
        uri = "file:///c:/projects/example.robot"
        store.open(uri, "*** Settings ***\n", 1, "robotframework")
        provider = StubTokenProvider()
        service = SemanticTokensService(store, provider)

        service.full(uri)
        service.clear_uri(uri)
        service.full(uri)

        assert provider.calls == 2
        assert service.cache_size == 1

    def test_cache_respects_max_entries(self):
        store = DocumentStore()
        first_uri = "file:///c:/projects/one.robot"
        second_uri = "file:///c:/projects/two.robot"
        store.open(first_uri, "*** Settings ***\n", 1, "robotframework")
        store.open(second_uri, "*** Variables ***\n", 1, "robotframework")
        provider = StubTokenProvider()
        service = SemanticTokensService(store, provider, max_cache_entries=1)

        service.full(first_uri)
        service.full(second_uri)
        service.full(first_uri)

        assert provider.calls == 3
        assert service.cache_size == 1
