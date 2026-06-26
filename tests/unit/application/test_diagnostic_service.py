from robot_lsp.application.diagnostic_service import DiagnosticService
from robot_lsp.application.configuration import ConfigurationService
from robot_lsp.application.document_store import DocumentStore, path_to_uri
from robot_lsp.application.parse_service import ParseService
from robot_lsp.application.workspace import WorkspaceIndex
from robot_lsp.domain.diagnostics import DiagnosticSeverity
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser


def make_service(debounce_seconds: float = 10.0, workspace_index=None, config_service=None):
    store = DocumentStore()
    published = []

    def publisher(uri, diagnostics):
        published.append((uri, diagnostics))

    service = DiagnosticService(
        ParseService(store, RobotFrameworkParser()),
        publisher,
        workspace_index=workspace_index,
        config_provider=None if config_service is None else config_service.config_for_uri,
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

    def test_semantic_diagnostic_for_missing_keyword(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/missing-keyword.robot"
        store.open(
            uri=uri,
            text="*** Test Cases ***\nT\n    Missing Keyword\n",
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        diagnostic = published[0][1][0]
        assert diagnostic.severity == DiagnosticSeverity.WARNING
        assert diagnostic.code == "keyword_not_found"
        assert diagnostic.message == "Keyword not found: Missing Keyword"

    def test_semantic_diagnostic_for_missing_variable(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/missing-variable.robot"
        store.open(
            uri=uri,
            text="*** Test Cases ***\nT\n    Log    ${MISSING}\n",
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        diagnostic = published[0][1][0]
        assert diagnostic.severity == DiagnosticSeverity.WARNING
        assert diagnostic.code == "variable_not_found"
        assert diagnostic.message == "Variable not found: ${MISSING}"

    def test_configured_variable_does_not_report_missing(self):
        config_service = ConfigurationService()
        config_service.update({"variables": {"RUNTIME_VALUE": "ok"}})
        store, service, published = make_service(config_service=config_service)
        uri = "file:///c:/projects/configured-variable.robot"
        store.open(
            uri=uri,
            text="*** Test Cases ***\nT\n    Log    ${RUNTIME_VALUE}\n",
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        assert published == [(uri, [])]

    def test_step_assignment_defines_variable_for_later_steps(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/local-variable.robot"
        store.open(
            uri=uri,
            text="*** Test Cases ***\nT\n    ${value}=    Set Variable    ok\n    Log    ${value}\n",
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        assert published == [(uri, [])]

    def test_var_syntax_defines_variable_for_later_steps(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/var-syntax.robot"
        store.open(
            uri=uri,
            text="*** Test Cases ***\nT\n    VAR    ${value}    ok\n    Log    ${value}\n",
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        assert published == [(uri, [])]

    def test_var_syntax_does_not_define_variable_for_earlier_steps(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/var-syntax-before.robot"
        store.open(
            uri=uri,
            text="*** Test Cases ***\nT\n    Log    ${value}\n    VAR    ${value}    ok\n",
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        diagnostic = published[0][1][0]
        assert diagnostic.code == "variable_not_found"
        assert diagnostic.message == "Variable not found: ${value}"

    def test_eval_variable_does_not_report_inner_variables(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/eval-variable.robot"
        store.open(
            uri=uri,
            text='*** Test Cases ***\nT\n    Log    ${{ $URL.tcode.format("${tcode}") }}\n',
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        assert published == [(uri, [])]

    def test_dictionary_variable_cross_type_access_does_not_report_missing(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/dictionary-cross-type.robot"
        store.open(
            uri=uri,
            text="*** Variables ***\n&{USER}    name=Ana\n*** Test Cases ***\nT\n    Log    ${USER.name}\n",
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        assert published == [(uri, [])]

    def test_empty_test_case_local_settings_do_not_report_diagnostics(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/empty-test-settings.robot"
        store.open(
            uri=uri,
            text=(
                "*** Test Cases ***\n"
                "T\n"
                "    [Documentation]\n"
                "    [Tags]\n"
                "    [Setup]\n"
                "    [Teardown]\n"
                "    [Template]\n"
                "    [Timeout]\n"
                "    No Operation\n"
            ),
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        assert published == [(uri, [])]

    def test_empty_keyword_local_settings_do_not_report_diagnostics(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/empty-keyword-settings.robot"
        store.open(
            uri=uri,
            text=(
                "*** Keywords ***\n"
                "Keyword\n"
                "    [Documentation]\n"
                "    [Arguments]\n"
                "    [Setup]\n"
                "    [Teardown]\n"
                "    [Timeout]\n"
                "    [Tags]\n"
                "    [Return]\n"
                "    No Operation\n"
            ),
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        assert published == [(uri, [])]

    def test_unknown_variable_type_diagnostic(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/unknown-type.robot"
        store.open(
            uri=uri,
            text="*** Variables ***\n${value: MissingType}    ok\n",
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        diagnostic = published[0][1][0]
        assert diagnostic.severity == DiagnosticSeverity.WARNING
        assert diagnostic.code == "unknown_variable_type"
        assert diagnostic.message == "Unknown variable type: MissingType"

    def test_importable_variable_type_does_not_report_diagnostic(self):
        store, service, published = make_service()
        uri = "file:///c:/projects/importable-type.robot"
        store.open(
            uri=uri,
            text="*** Variables ***\n${value: pathlib.PurePath}    path\n",
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        assert published == [(uri, [])]

    def test_semantic_diagnostic_for_missing_import(self, tmp_path):
        index = WorkspaceIndex()
        store, service, published = make_service(workspace_index=index)
        path = tmp_path / "missing-import.robot"
        uri = path_to_uri(path)
        store.open(
            uri=uri,
            text="*** Settings ***\nResource    missing.resource\n",
            version=1,
            language_id="robotframework",
        )

        service.flush(uri)

        diagnostic = published[0][1][0]
        assert diagnostic.severity == DiagnosticSeverity.ERROR
        assert diagnostic.code == "import_not_found"
        assert diagnostic.message == "Import not found: missing.resource"

    def test_yaml_variable_file_without_pyyaml_reports_diagnostic(self, tmp_path, monkeypatch):
        monkeypatch.setattr("robot_lsp.application.diagnostic_service.has_yaml_support", lambda: False)
        index = WorkspaceIndex()
        variable_file = tmp_path / "vars.yaml"
        variable_file.write_text("USER:\n  name: Ana\n", encoding="utf-8")
        path = tmp_path / "suite.robot"
        uri = path_to_uri(path)
        text = "*** Settings ***\nVariables    vars.yaml\n"
        path.write_text(text, encoding="utf-8")
        index.update_file(path)
        store, service, published = make_service(workspace_index=index)
        store.open(uri=uri, text=text, version=1, language_id="robotframework")

        service.flush(uri)

        diagnostic = published[0][1][0]
        assert diagnostic.severity == DiagnosticSeverity.ERROR
        assert diagnostic.code == "yaml_support_missing"
        assert diagnostic.message == "YAML variable files require PyYAML to be installed."

    def test_imported_resource_symbols_do_not_report_missing(self, tmp_path):
        main = tmp_path / "main.robot"
        resource = tmp_path / "keywords.resource"
        main.write_text(
            "*** Settings ***\n"
            "Resource    keywords.resource\n"
            "*** Test Cases ***\n"
            "T\n"
            "    Resource Keyword    ${RESOURCE_VAR}\n",
            encoding="utf-8",
        )
        resource.write_text(
            "*** Variables ***\n"
            "${RESOURCE_VAR}    ok\n"
            "*** Keywords ***\n"
            "Resource Keyword\n"
            "    Log    ${RESOURCE_VAR}\n",
            encoding="utf-8",
        )
        index = WorkspaceIndex()
        index.scan(tmp_path)
        store, service, published = make_service(workspace_index=index)
        uri = path_to_uri(main)
        store.open(uri=uri, text=main.read_text(encoding="utf-8"), version=1, language_id="robotframework")

        service.flush(uri)

        assert published == [(uri, [])]
