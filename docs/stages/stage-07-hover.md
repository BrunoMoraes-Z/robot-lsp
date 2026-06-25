# Stage 07 — Hover

## Status

done

## Goal

Implement hover to show information about symbols under the cursor: keywords, variables, and imports.

## Scope

- `textDocument/hover` handler
- `HoverContext`: cursor position, document, parsed model
- Providers:
- **KeywordHoverProvider**: shows signature (name + args) and docstring for local keywords
- **VariableHoverProvider**: shows type (scalar/list/dict/secret) and raw value
- **ImportHoverProvider**: shows import type (Library/Resource/Variables) and path
- `Hover` response with `contents` (MarkupContent) and `range`
- Markdown formatting for `contents`
- `null` if nothing is found for hover

## Out Of Scope

- Hover for external library keywords (Stage 09)
- Hover for global-scope variables or keyword arguments

## Deliverables

- `src/robot_lsp/application/hover_service.py`
- Providers in internal modules
- Tests for each provider

## Acceptance Criteria

- Hover on local keyword: returns `**Name(args)**\n\ndocstring` in markdown
- Hover on variable: returns `**Type**: value`
- Hover on import: returns `**Library**: Name` or similar
- Hover `range` covers the symbol under the cursor
- Returns `null` if the cursor is not over a known symbol
- Markdown is formatted correctly (heading, code, etc.)

## Tests

- `test_hover_local_keyword`
- `test_hover_variable`
- `test_hover_import`
- `test_hover_empty`
- `test_hover_range`
- `test_hover_markdown_format`

## Risks

- Identifying the exact symbol under the cursor requires line and column analysis
- Multiline docstrings must be formatted correctly in markdown

## Dependencies

- Stage 04 (RF model)

## Notes

- Stage completed with initial hover for local keywords, local variables, and imports.
- `textDocument/hover` was integrated into `LspServer` as an LSP request.
- The service uses `DocumentStore` + `ParseService`, without a direct Robot Framework dependency.
- Hover for imported libraries/resources remains out of scope and will be handled after workspace index.
- Validation executed with `just test` and `uv run python -m compileall src tests`.
