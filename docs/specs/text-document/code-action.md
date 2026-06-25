# Code Action

## Stage

**Done** (Stage 11)

## LSP Methods

- `textDocument/codeAction`

## Notes

Initial quick actions for known diagnostics.

## Behavior

- `textDocument/codeAction` returns an empty list when the document is not open.
- Diagnostics with `code: parse_error` return an informative `quickfix` action.
- Diagnostics with `code: import_not_found` return an informative `quickfix` action.
- Actions include the original diagnostic in `diagnostics`.

## Out Of Scope

- Apply automatic edits to fix parse errors.
- Resolve missing imports by searching the workspace.
- Fix undefined variables.
- `codeAction/resolve`.
