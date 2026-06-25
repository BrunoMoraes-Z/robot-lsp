# Formatting

## Stage

**Done** (Stage 11)

## LSP Methods

- `textDocument/formatting`
- `textDocument/rangeFormatting`

## Notes

Format `.robot` files following initial spacing best practices.

## Behavior

- `textDocument/formatting` returns a single `TextEdit` covering the whole document when text changes.
- `textDocument/rangeFormatting` formats full lines touched by the provided range.
- Cell separators are normalized to 4 spaces.
- Trailing whitespace is removed from each line.
- Section lines such as `*** Settings ***` are trimmed.
- Empty lines and comments preserve content without trailing whitespace.

## Out Of Scope

- Reordering settings, test cases, or keywords.
- AST-based semantic formatting.
- Separator width configuration through `FormattingOptions`.
