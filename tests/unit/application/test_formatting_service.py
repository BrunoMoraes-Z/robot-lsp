from robot_lsp.application.document_store import DocumentStore
from robot_lsp.application.formatting_service import FormattingService, format_robot_text
from robot_lsp.domain.models import LspPosition, LspRange


class TestFormattingService:
    def test_format_robot_text_normalizes_cell_spacing(self):
        text = "*** Settings ***   \nLibrary\tCollections\n*** Test Cases ***\nT\n  Log  hello   \n"

        assert format_robot_text(text) == "*** Settings ***\nLibrary    Collections\n*** Test Cases ***\nT\n  Log    hello\n"

    def test_format_document_returns_single_full_document_edit(self):
        store = DocumentStore()
        uri = "file:///c:/projects/format.robot"
        store.open(uri=uri, text="*** Test Cases ***\nT\n    Log  hello\n", version=1, language_id="robotframework")
        service = FormattingService(store)

        edits = service.format_document(uri)

        assert edits == [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 3, "character": 0},
                },
                "newText": "*** Test Cases ***\nT\n    Log    hello\n",
            }
        ]

    def test_format_document_returns_no_edits_when_unchanged(self):
        store = DocumentStore()
        uri = "file:///c:/projects/format.robot"
        store.open(uri=uri, text="*** Test Cases ***\nT\n    Log    hello\n", version=1, language_id="robotframework")
        service = FormattingService(store)

        assert service.format_document(uri) == []

    def test_format_range_formats_whole_touched_lines(self):
        store = DocumentStore()
        uri = "file:///c:/projects/format.robot"
        store.open(uri=uri, text="*** Test Cases ***\nT\n    Log  hello\n", version=1, language_id="robotframework")
        service = FormattingService(store)

        edits = service.format_range(uri, LspRange(LspPosition(2, 0), LspPosition(2, 15)))

        assert edits == [
            {
                "range": {
                    "start": {"line": 2, "character": 0},
                    "end": {"line": 2, "character": 14},
                },
                "newText": "    Log    hello",
            }
        ]
