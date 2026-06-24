from robot_lsp.domain.models import LspPosition, LspRange
from robot_lsp.domain.positions import (
    calculate_lsp_range,
    position_to_utf16_offset,
    range_text,
    utf16_offset_to_position,
)


class TestPositions:
    def test_lsp_position_utf16_ascii(self):
        text = "abc\ndef"

        assert position_to_utf16_offset(text, 0, 2) == 2
        assert utf16_offset_to_position(text, 2) == LspPosition(line=0, character=2)
        assert position_to_utf16_offset(text, 1, 1) == 5
        assert utf16_offset_to_position(text, 5) == LspPosition(line=1, character=1)

    def test_lsp_position_utf16_accent(self):
        text = "olá\nmundo"

        assert position_to_utf16_offset(text, 0, 3) == 3
        assert utf16_offset_to_position(text, 3) == LspPosition(line=0, character=3)

    def test_lsp_position_utf16_emoji(self):
        text = "a🤖b\nnext"


        assert position_to_utf16_offset(text, 0, 0) == 0
        assert position_to_utf16_offset(text, 0, 1) == 1
        assert position_to_utf16_offset(text, 0, 2) == 2
        assert position_to_utf16_offset(text, 0, 3) == 2
        assert position_to_utf16_offset(text, 0, 4) == 3
        assert utf16_offset_to_position(text, 1) == LspPosition(line=0, character=1)
        assert utf16_offset_to_position(text, 2) == LspPosition(line=0, character=3)
        assert utf16_offset_to_position(text, 3) == LspPosition(line=0, character=4)

    def test_empty_text_position(self):
        assert position_to_utf16_offset("", 0, 0) == 0
        assert position_to_utf16_offset("", 1, 0) is None
        assert utf16_offset_to_position("", 0) == LspPosition(line=0, character=0)

    def test_calculate_lsp_range_from_one_based_values(self):
        text = "alpha\nbravo"

        assert calculate_lsp_range(text, 2, 1, 2, 6) == LspRange(
            start=LspPosition(line=1, character=0),
            end=LspPosition(line=1, character=5),
        )

    def test_range_text_extraction(self):
        text = "alpha\nbravo\ncharlie"

        assert (
            range_text(
                text,
                LspRange(
                    start=LspPosition(line=1, character=0),
                    end=LspPosition(line=1, character=5),
                ),
            )
            == "bravo"
        )

    def test_range_text_extraction_with_emoji(self):
        text = "Log    🤖 Robot"

        assert (
            range_text(
                text,
                LspRange(
                    start=LspPosition(line=0, character=7),
                    end=LspPosition(line=0, character=15),
                ),
            )
            == "🤖 Robot"
        )
