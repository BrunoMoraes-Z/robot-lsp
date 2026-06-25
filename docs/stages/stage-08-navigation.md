# Stage 08 — Navigation

## Status

done

## Goal

Implement navigation local to the current document for Robot Framework symbols.

## Scope

- `textDocument/definition`
- `textDocument/references`
- `textDocument/documentSymbol`
- `textDocument/foldingRange`
- `textDocument/selectionRange`
- Scope local to the currently open document
- Keywords, variables, imports, test cases, and section ranges

## Out Of Scope

- Workspace-wide references
- Definition for symbols imported from resources/libraries
- Call hierarchy/type hierarchy
- Deep semantic library resolution

## Deliverables

- `src/robot_lsp/application/navigation_service.py`
- Handler integration in `LspServer`
- Navigation capabilities in `initialize`
- Unit tests for service and LSP handlers

## Acceptance Criteria

- `definition` returns locations for local keywords/variables/imports
- `references` returns local occurrences with `includeDeclaration` support
- `documentSymbol` returns imports, variables, test cases, and keywords
- `foldingRange` returns ranges for sections, test cases, and keywords
- `selectionRange` returns symbol range with a line parent when possible
- Handlers return empty lists when service/document does not exist

## Tests

- `test_definition_local_keyword`
- `test_definition_variable`
- `test_references_variable`
- `test_references_excluding_declaration`
- `test_document_symbols`
- `test_folding_ranges`
- `test_selection_ranges_symbol_and_line_parent`
- `test_text_document_definition`
- `test_text_document_references`
- `test_text_document_document_symbol`
- `test_text_document_folding_range`
- `test_text_document_selection_range`

## Risks

- Local scope may return incomplete results until Stage 09.
- Definition ranges depend on the granularity of the current AST adapter.

## Dependencies

- Stage 04
- Stage 06
- Stage 07

## Notes

- Stage completed with navigation local to the current document.
- The `definitionProvider`, `referencesProvider`, `documentSymbolProvider`, `foldingRangeProvider`, and `selectionRangeProvider` capabilities are advertised in `initialize`.
- Cross-file navigation is deferred to Stage 09: Workspace Index.
- Validation executed with `just test` and `uv run python -m compileall src tests`.
