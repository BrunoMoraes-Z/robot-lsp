from robot_lsp.application.diagnostic_service import DiagnosticService
from robot_lsp.application.document_store import DocumentStore
from robot_lsp.application.parse_service import ParseService
from robot_lsp.domain.diagnostics import DiagnosticSeverity
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser


def make_service(debounce_seconds: float = 10.0):
    store = DocumentStore()
    published = []

    def publisher(uri, diagnostics):
        published.append((uri, diagnostics))

    service = DiagnosticService(
        ParseService(store, RobotFrameworkParser()),
        publisher,
        debounce_seconds=debounce_seconds,
    )
    return store, service, published


class TestDiagnosticService:
    def test_diagnostic_from_parse_error(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/bad.robot"
        store.open(
            uri=uri,
            text="*** Test Cases ***\nBroken\n    ELSE\n    Log    invalid\n",
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        assert len(published) == 1
        assert published[0][0] == uri
        assert len(published[0][1]) == 1
        diagnostic = published[0][1][0]
        assert diagnostic.severity == DiagnosticSeverity.ERROR
        assert diagnostic.code == "parse_error"
        assert diagnostic.range.start.line >= 0

    def test_diagnostic_cleared_on_fix(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/fix.robot"
        store.open(uri=uri, text="*** Test Cases ***\nBroken\n    ELSE\n", version=1, language_id="robotframework")
        service.flush(uri)

        store.change(uri=uri, text="*** Test Cases ***\nFixed\n    Log    ok\n", version=2)
        service.flush(uri)

        assert len(published) == 2
        assert len(published[0][1]) == 1
        assert published[1][1] == []

    def test_diagnostic_debounce(self):
        store, service, published = make_service(debounce_seconds=999.0)
        uri = "file:///c:/projects/debounce.robot"
        store.open(uri=uri, text="*** Test Cases ***\nT\n    ELSE\n", version=1, language_id="robotframework")

        service.schedule_diagnostics(uri)

        assert published == []
        service.cancel_pending(uri)

    def test_diagnostic_cancel(self):
        store, service, published = make_service(debounce_seconds=999.0)
        uri = "file:///c:/projects/cancel.robot"
        store.open(uri=uri, text="*** Test Cases ***\nT\n    ELSE\n", version=1, language_id="robotframework")

        service.schedule_diagnostics(uri)
        assert service.cancel_pending(uri) is True

        assert published == []

    def test_diagnostic_no_duplicate_publish_when_unchanged(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/dup.robot"
        store.open(uri=uri, text="*** Test Cases ***\nT\n    ELSE\n", version=1, language_id="robotframework")

        service.flush(uri)
        service.flush(uri)

        assert len(published) == 1

    def test_diagnostic_fallback_empty_when_document_missing(self):
        _store, service, published = make_service()

        service.flush("file:///c:/projects/missing.robot")

        assert published == [("file:///c:/projects/missing.robot", [])]
