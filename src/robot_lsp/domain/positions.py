from __future__ import annotations

from .models import LspPosition, LspRange


def position_to_utf16_offset(text: str, line: int, character: int) -> int | None:
    """Convert an LSP position (0-based line, 0-based UTF-16 character) to a code-point offset in text."""
    lines = text.splitlines(keepends=True)
    if line < 0 or line >= len(lines):
        return None
    line_text = lines[line]
    utf16_offset = 0
    code_point_offset = 0
    for ch in line_text:
        if utf16_offset >= character:
            break
        utf16_offset += 1 if ord(ch) < 0x10000 else 2
        code_point_offset += 1
    return sum(len(l) for l in lines[:line]) + code_point_offset


def utf16_offset_to_position(text: str, offset: int) -> LspPosition | None:
    """Convert a code-point offset in text to an LSP position (0-based)."""
    if offset < 0 or offset > len(text):
        return None
    line = 0
    character = 0
    for i, ch in enumerate(text):
        if i >= offset:
            break
        if ch == "\n":
            line += 1
            character = 0
        elif ch == "\r":
            pass
        else:
            character += 1 if ord(ch) < 0x10000 else 2
    return LspPosition(line=line, character=character)


def calculate_lsp_range(
    text: str,
    start_line: int,
    start_col: int,
    end_line: int,
    end_col: int,
    *,
    start_is_1_based: bool = True,
    end_is_1_based: bool = True,
) -> LspRange:
    """Create an LSP range from line/col values, optionally converting 1-based to 0-based."""
    if start_is_1_based:
        start_line = max(0, start_line - 1)
        start_col = max(0, start_col - 1)
    if end_is_1_based:
        end_line = max(0, end_line - 1)
        end_col = max(0, end_col - 1)

    lines = text.splitlines()
    clamped_end_col = end_col
    if end_line < len(lines):
        clamped_end_col = min(end_col, _utf16_len(lines[end_line]))

    return LspRange(
        start=LspPosition(line=start_line, character=start_col),
        end=LspPosition(line=end_line, character=clamped_end_col),
    )


def _utf16_len(text: str) -> int:
    return sum(1 if ord(ch) < 0x10000 else 2 for ch in text)
