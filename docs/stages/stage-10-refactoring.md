# Stage 10 — Refactoring

## Status

done

## Goal

Implement initial refactoring through `prepareRename`, `rename`, and `WorkspaceEdit`.

## Scope

- `textDocument/prepareRename`
- `textDocument/rename`
- `WorkspaceEdit` with `changes`
- Rename local variables, keywords, and test cases
- Rename in indexed documents when `WorkspaceIndex` is available

## Out Of Scope

- Deep semantic validation of the new name
- Scope-aware rename
- Rename imported symbols from a click on imported usage
- Applying edits to the filesystem

## Deliverables

- `src/robot_lsp/application/refactoring_service.py`
- Handlers in `LspServer`
- `renameProvider` capability with `prepareProvider: true`
- Unit tests for service and LSP handlers

## Acceptance Criteria

- `prepareRename` returns range and placeholder when a symbol is renameable
- `prepareRename` returns `null` for unknown symbols
- `rename` returns `WorkspaceEdit`
- Local rename changes all exact textual occurrences in the open document
- Rename with `WorkspaceIndex` includes indexed files
- Handler returns `null` when service is not configured

## Tests

- `test_prepare_rename_variable`
- `test_prepare_rename_unknown_symbol_returns_none`
- `test_rename_variable_local_document`
- `test_rename_keyword_local_document`
- `test_rename_with_workspace_index_updates_indexed_files`
- `test_text_document_prepare_rename`
- `test_text_document_rename`

## Risks

- Exact textual rename can rename occurrences that are not semantically the same symbol.
- Scope-aware rename will be refined when the semantic usage/definition model matures.

## Dependencies

- Stage 04
- Stage 08
- Stage 09

## Notes

- Stage completed with `RefactoringService` and LSP integration.
- WorkspaceEdit uses `changes` by URI.
- Validation executed with `just test` and `uv run python -m compileall src tests`.
