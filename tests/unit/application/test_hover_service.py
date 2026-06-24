from robot_lsp.application.document_store import DocumentStore
from robot_lsp.application.hover_service import HoverService
from robot_lsp.application.parse_service import ParseService
from robot_lsp.domain.models import LspPosition
from robot_lsp.infrastructure.robotframework.parser import RobotFrameworkParser


TEXT = """*** Settings ***
Library    Collections    WITH NAME    Col
Resource   resource.robot

*** Variables ***
${MESSAGE}    Hello

*** Test Cases ***
My Test
    My Keyword    ${MESSAGE}

*** Keywords ***
My Keyword
    [Arguments]    ${arg}=default
    [Documentation]    Keyword docs
    Log    ${arg}
"""


def make_service(text: str = TEXT):
    store = DocumentStore()
    parser = RobotFrameworkParser()
    service = HoverService(store, ParseService(store, parser))
    uri = "file:///c:/projects/hover.robot"
    store.open(uri=uri, text=text, version=1, language_id="robotframework")
    return service, uri


class TestHoverService:
    def test_hover_local_keyword(self):
        service, uri = make_service()

        hover = service.compute_hover(uri, LspPosition(line=9, character=7))

        assert hover is not None
        assert hover.contents.kind == "markdown"
        assert hover.contents.value == "**My Keyword(${arg}=default)**\n\nKeyword docs"

    def test_hover_variable(self):
        service, uri = make_service()

        hover = service.compute_hover(uri, LspPosition(line=9, character=21))

        assert hover is not None
        assert hover.contents.kind == "markdown"
        assert "**${MESSAGE}**" in hover.contents.value
        assert "Type: scalar" in hover.contents.value
        assert "Value: Hello" in hover.contents.value

    def test_hover_import(self):
        service, uri = make_service()

        hover = service.compute_hover(uri, LspPosition(line=1, character=14))

        assert hover is not None
        assert hover.contents.value == "**Library**: `Collections` as Col"

    def test_hover_empty(self):
        service, uri = make_service()

        assert service.compute_hover(uri, LspPosition(line=0, character=0)) is None

    def test_hover_range(self):
        service, uri = make_service()

        hover = service.compute_hover(uri, LspPosition(line=9, character=7))

        assert hover is not None
        assert hover.range.start.line == 9
        assert hover.range.start.character == 4
        assert hover.range.end.character == 14

    def test_hover_markdown_format(self):
        service, uri = make_service()

        hover = service.compute_hover(uri, LspPosition(line=5, character=4))

        assert hover is not None
        assert hover.to_lsp()["contents"]["kind"] == "markdown"
        assert hover.to_lsp()["range"]["start"] == {"line": 5, "character": 0}

    def test_hover_missing_document_returns_none(self):
        service, _uri = make_service()

        assert service.compute_hover("file:///missing.robot", LspPosition(0, 0)) is None
