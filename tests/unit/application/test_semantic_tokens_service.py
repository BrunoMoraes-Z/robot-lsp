from robot_lsp.application.document_store import DocumentStore
from robot_lsp.application.semantic_tokens_service import SemanticToken, SemanticTokensService, encode_semantic_tokens


class StubTokenProvider:
    def semantic_tokens(self, text: str, *, source_name: str = "document.robot") -> list[SemanticToken]:
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
