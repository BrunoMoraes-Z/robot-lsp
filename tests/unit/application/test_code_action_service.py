from robot_lsp.application.code_action_service import CodeActionService
from robot_lsp.application.document_store import DocumentStore


class TestCodeActionService:
    def test_parse_error_diagnostic_returns_quick_fix_action(self):
        store = DocumentStore()
        uri = "file:///c:/projects/action.robot"
        diagnostic = {"code": "parse_error", "message": "Invalid syntax"}
        store.open(uri=uri, text="*** Test Cases ***\n", version=1, language_id="robotframework")
        service = CodeActionService(store)

        actions = service.code_actions(uri, None, {"diagnostics": [diagnostic]})

        assert actions == [
            {
                "title": "Show Robot Framework parse error",
                "kind": "quickfix",
                "diagnostics": [diagnostic],
                "isPreferred": False,
            }
        ]

    def test_missing_document_returns_no_actions(self):
        service = CodeActionService(DocumentStore())

        assert service.code_actions("file:///missing.robot", None, {"diagnostics": [{"code": "parse_error"}]}) == []
