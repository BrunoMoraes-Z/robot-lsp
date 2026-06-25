# Rename

## Stage

Stage 10 — done

## LSP Methods

- `textDocument/rename`
- `textDocument/prepareRename`

## Notes

Rename symbols (keywords, variables) with workspace edit support.

## Implemented

- `textDocument/prepareRename`
- `textDocument/rename`
- `WorkspaceEdit` using `changes`
- Local variables, keywords, and test cases
- Inclusion of indexed files when `WorkspaceIndex` is available

## Limitations

- Rename is still exact textual rename, not scope-aware semantic rename.
- Rename of imported symbols from usage is left for future evolution.
