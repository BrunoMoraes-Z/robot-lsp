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
- Actions incluem o diagnostic original em `diagnostics`.

## Out Of Scope

- Apply automatic edits to fix parse errors.
- Resolver imports ausentes por busca no workspace.
- Fix undefined variables.
- `codeAction/resolve`.
