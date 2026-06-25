# Workspace Folders

## Stage

**Planned** (Stage 13)

## LSP Methods

- `workspace/didChangeWorkspaceFolders`
- `initialize` params: `workspaceFolders`

## Notes

- Initially, `rootUri` from `initialize` is sufficient
- Dynamic workspace folders will be implemented when multi-root workspace support exists
- Impacts relative import resolution
