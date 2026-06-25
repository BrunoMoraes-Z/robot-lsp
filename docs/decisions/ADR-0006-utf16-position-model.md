# ADR-0006 — UTF-16 Position Model

## Status

accepted

## Context

The LSP protocol specifies that positions (line, column) use line as a 0-based integer and column as a 0-based UTF-16 code unit offset. Python strings use code point based indexes, and characters such as emoji (which occupy 2 UTF-16 code units) cause discrepancies if ignored.

## Decision

Adopt UTF-16 code units for all LSP positions, with a dedicated conversion layer:

- `LspPosition.line`: 0-based line number.
- `LspPosition.character`: 0-based UTF-16 code unit offset.
- Implement conversion functions in `robot_lsp.domain.positions`:
  - `utf16_offset_to_position(text, offset)`
  - `position_to_utf16_offset(text, line, character)`
  - `calculate_lsp_range(text, start_line, start_col, end_line, end_col)`
- Test with ASCII characters, accented characters (1 code unit), and emoji (2 code units).

## Consequences

- Positions sent to the LSP client will be correct regardless of content.
- Extra conversion complexity, but isolated in `domain/positions.py`.
- Specific tests for multibyte characters.

## Alternatives Considered

- Ignore UTF-16 and use direct Python indexes: rejected because it causes bugs with emoji and accented characters in editors.
- Use an external library: rejected to avoid a dependency for simple functionality.
