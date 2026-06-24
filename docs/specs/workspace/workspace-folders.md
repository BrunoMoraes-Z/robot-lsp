# Workspace Folders

## Stage

**Planned** (Stage 13)

## LSP Methods

- `workspace/didChangeWorkspaceFolders`
- `initialize` params: `workspaceFolders`

## Notes

- Inicialmente, `rootUri` do `initialize` é suficiente
- Workspace folders dinâmicos serão implementados quando houver suporte a multi-root workspace
- Impacta resolução de imports relativos
