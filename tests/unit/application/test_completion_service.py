from robot_lsp.application.completion_service import CompletionItemKind, CompletionService
from robot_lsp.application.document_store import DocumentStore, path_to_uri
from robot_lsp.application.parse_service import ParseService
from robot_lsp.application.workspace import WorkspaceIndex
from robot_lsp.domain.models import LspPosition
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser


def make_service(text: str):
    store = DocumentStore()
    parser = RobotFrameworkParser()
    service = CompletionService(store, ParseService(store, parser))
    uri = "file:///c:/projects/completion.robot"
    store.open(uri=uri, text=text, version=1, language_id="robotframework")
    return service, uri


def labels(completion):
    return [item.label for item in completion.items]


class TestCompletionService:
    def test_completion_sections(self):
        service, uri = make_service("")

        completion = service.compute_completion(uri, LspPosition(line=0, character=0))

        assert completion is not None
        assert completion.is_incomplete is False
        assert labels(completion) == [
            "*** Settings ***",
            "*** Variables ***",
            "*** Test Cases ***",
            "*** Keywords ***",
        ]
        assert completion.items[0].kind == CompletionItemKind.SNIPPET
        assert completion.items[0].detail == "Robot Framework section"
        assert completion.items[0].to_lsp()["insertText"] == "*** Settings ***\n$0"
        assert completion.items[0].to_lsp()["insertTextFormat"] == 2

    def test_completion_sections_without_snippets(self):
        service, uri = make_service("")

        completion = service.compute_completion(
            uri,
            LspPosition(line=0, character=0),
            snippets_enabled=False,
        )

        assert completion is not None
        assert labels(completion) == [
            "*** Settings ***",
            "*** Variables ***",
            "*** Test Cases ***",
            "*** Keywords ***",
        ]
        assert completion.items[0].kind == CompletionItemKind.TEXT
        assert "insertText" not in completion.items[0].to_lsp()
        assert "insertTextFormat" not in completion.items[0].to_lsp()

    def test_completion_sections_after_prefix(self):
        service, uri = make_service("***")

        completion = service.compute_completion(uri, LspPosition(line=0, character=3))

        assert "*** Settings ***" in labels(completion)

    def test_completion_settings(self):
        service, uri = make_service("*** Settings ***\n")

        completion = service.compute_completion(uri, LspPosition(line=1, character=0))

        result = labels(completion)

        assert "Library" in result
        assert "Resource" in result
        assert "Suite Setup" in result
        assert completion.items[0].kind == CompletionItemKind.KEYWORD
        assert completion.items[0].detail == "Robot Framework setting"

    def test_completion_local_keyword(self):
        service, uri = make_service(
            "*** Test Cases ***\n"
            "T\n"
            "    \n"
            "*** Keywords ***\n"
            "My Keyword\n"
            "    [Documentation]    Docs\n"
            "    Log    ok\n"
        )

        completion = service.compute_completion(uri, LspPosition(line=2, character=4))

        assert labels(completion) == ["My Keyword"]
        assert completion.items[0].kind == CompletionItemKind.FUNCTION
        assert completion.items[0].detail == "Local keyword"
        assert completion.items[0].documentation == "Docs"

    def test_completion_local_variable(self):
        service, uri = make_service(
            "*** Variables ***\n"
            "${MESSAGE}    Hello\n"
            "@{ITEMS}      one    two\n"
            "*** Test Cases ***\n"
            "T\n"
            "    Log    $"
        )

        completion = service.compute_completion(
            uri,
            LspPosition(line=5, character=12),
            trigger_character="$",
        )

        assert labels(completion) == ["${MESSAGE}", "@{ITEMS}"]
        assert completion.items[0].kind == CompletionItemKind.VARIABLE
        assert completion.items[0].detail == "Local scalar variable"

    def test_completion_var_syntax_scoped_variable(self):
        service, uri = make_service(
            "*** Test Cases ***\n"
            "T\n"
            "    VAR    ${local}    value\n"
            "    Log    $"
        )

        completion = service.compute_completion(
            uri,
            LspPosition(line=3, character=12),
            trigger_character="$",
        )

        assert "${local}" in labels(completion)

    def test_completion_does_not_include_later_var_syntax_variable(self):
        service, uri = make_service(
            "*** Test Cases ***\n"
            "T\n"
            "    Log    $\n"
            "    VAR    ${later}    value\n"
        )

        completion = service.compute_completion(
            uri,
            LspPosition(line=2, character=12),
            trigger_character="$",
        )

        assert "${later}" not in labels(completion)

    def test_completion_variable_type_annotation(self):
        service, uri = make_service("*** Test Cases ***\nT\n    VAR    ${value: ")

        completion = service.compute_completion(uri, LspPosition(line=2, character=20))

        assert "int" in labels(completion)
        assert "Secret" in labels(completion)
        assert completion.items[0].detail == "Robot Framework variable type"

    def test_completion_trigger_characters(self):
        service, uri = make_service(
            "*** Variables ***\n${VAR}    value\n*** Test Cases ***\nT\n    Log    @"
        )

        completion = service.compute_completion(
            uri,
            LspPosition(line=4, character=12),
            trigger_character="@",
        )

        assert labels(completion) == ["${VAR}"]

    def test_completion_empty_result(self):
        service, uri = make_service("*** Variables ***\n${VAR}    value\n")

        completion = service.compute_completion(uri, LspPosition(line=1, character=0))

        assert completion is not None
        assert completion.to_lsp() == {"isIncomplete": False, "items": []}

    def test_completion_missing_document_returns_none(self):
        service, _uri = make_service("")

        assert service.compute_completion("file:///missing.robot", LspPosition(0, 0)) is None

    def test_completion_dictionary_key_bracket(self):
        text = (
            "*** Variables ***\n"
            "&{USER}    name=Ana    email=ana@example.com\n"
            "*** Test Cases ***\n"
            "T\n"
            "    Log    ${USER}["
        )
        service, uri = make_service(text)

        completion = service.compute_completion(uri, LspPosition(line=4, character=len("    Log    ${USER}[")))

        assert labels(completion) == ["name", "email"]
        assert completion.items[0].kind == CompletionItemKind.FIELD
        assert completion.items[0].detail == "Dictionary key"
        assert completion.items[0].documentation == "Ana"

    def test_completion_dictionary_key_bracket_with_filter(self):
        text = (
            "*** Variables ***\n"
            "&{USER}    name=Ana    email=ana@example.com\n"
            "*** Test Cases ***\n"
            "T\n"
            "    Log    ${USER}[em"
        )
        service, uri = make_service(text)

        completion = service.compute_completion(uri, LspPosition(line=4, character=len("    Log    ${USER}[em")))

        assert labels(completion) == ["email"]

    def test_completion_dictionary_key_ampersand_bracket(self):
        text = (
            "*** Variables ***\n"
            "&{USER}    name=Ana\n"
            "*** Test Cases ***\n"
            "T\n"
            "    Log    &{USER}["
        )
        service, uri = make_service(text)

        completion = service.compute_completion(uri, LspPosition(line=4, character=len("    Log    &{USER}[")))

        assert labels(completion) == ["name"]

    def test_completion_dictionary_key_dot(self):
        text = (
            "*** Variables ***\n"
            "&{USER}    name=Ana    email=ana@example.com\n"
            "*** Test Cases ***\n"
            "T\n"
            "    Log    ${USER}.e"
        )
        service, uri = make_service(text)

        completion = service.compute_completion(uri, LspPosition(line=4, character=len("    Log    ${USER}.e")))

        assert labels(completion) == ["email"]

    def test_completion_dictionary_key_ignores_non_dict(self):
        text = (
            "*** Variables ***\n"
            "@{ITEMS}    one    two\n"
            "*** Test Cases ***\n"
            "T\n"
            "    Log    ${ITEMS}["
        )
        service, uri = make_service(text)

        completion = service.compute_completion(uri, LspPosition(line=4, character=len("    Log    ${ITEMS}[")))

        assert labels(completion) == []

    def test_completion_dictionary_key_scoped_variable(self):
        text = (
            "*** Test Cases ***\n"
            "T\n"
            "    VAR    &{USER}    name=Ana    email=ana@example.com\n"
            "    Log    ${USER}["
        )
        service, uri = make_service(text)

        completion = service.compute_completion(uri, LspPosition(line=3, character=len("    Log    ${USER}[")))

        assert labels(completion) == ["name", "email"]

    def test_completion_dictionary_key_imported_resource(self, tmp_path):
        resource = tmp_path / "vars.resource"
        resource.write_text("*** Variables ***\n&{USER}    name=Ana    email=ana@example.com\n", encoding="utf-8")
        suite = tmp_path / "suite.robot"
        suite_text = "*** Settings ***\nResource    vars.resource\n*** Test Cases ***\nT\n    Log    ${USER}["
        suite.write_text(suite_text, encoding="utf-8")
        index = WorkspaceIndex()
        index.scan(tmp_path)
        store = DocumentStore()
        parser = RobotFrameworkParser()
        service = CompletionService(store, ParseService(store, parser), index)
        uri = path_to_uri(suite.resolve())
        store.open(uri=uri, text=suite_text, version=1, language_id="robotframework")

        completion = service.compute_completion(uri, LspPosition(line=4, character=len("    Log    ${USER}[")))

        assert labels(completion) == ["name", "email"]

    def test_completion_dictionary_key_imported_python_variable_file(self, tmp_path):
        var_file = tmp_path / "vars.py"
        var_file.write_text('USER = {"name": "Ana", "email": "ana@example.com"}\n', encoding="utf-8")
        suite = tmp_path / "suite.robot"
        suite_text = "*** Settings ***\nVariables    vars.py\n*** Test Cases ***\nT\n    Log    ${USER}[na"
        suite.write_text(suite_text, encoding="utf-8")
        index = WorkspaceIndex()
        index.scan(tmp_path)
        store = DocumentStore()
        parser = RobotFrameworkParser()
        service = CompletionService(store, ParseService(store, parser), index)
        uri = path_to_uri(suite.resolve())
        store.open(uri=uri, text=suite_text, version=1, language_id="robotframework")

        completion = service.compute_completion(uri, LspPosition(line=4, character=len("    Log    ${USER}[na")))

        assert labels(completion) == ["name"]

    def test_completion_dictionary_key_imported_yaml_variable_file(self, tmp_path):
        var_file = tmp_path / "vars.yaml"
        var_file.write_text("USER:\n  name: Ana\n  email: ana@example.com\n", encoding="utf-8")
        suite = tmp_path / "suite.robot"
        suite_text = "*** Settings ***\nVariables    vars.yaml\n*** Test Cases ***\nT\n    Log    ${USER}["
        suite.write_text(suite_text, encoding="utf-8")
        index = WorkspaceIndex()
        index.scan(tmp_path)
        store = DocumentStore()
        parser = RobotFrameworkParser()
        service = CompletionService(store, ParseService(store, parser), index)
        uri = path_to_uri(suite.resolve())
        store.open(uri=uri, text=suite_text, version=1, language_id="robotframework")

        completion = service.compute_completion(uri, LspPosition(line=4, character=len("    Log    ${USER}[")))

        assert labels(completion) == ["name", "email"]
