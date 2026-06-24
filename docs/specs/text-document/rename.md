# Rename

## Stage

Stage 10 — done

## LSP Methods

- `textDocument/rename`
- `textDocument/prepareRename`

## Notes

Renomear símbolos (keywords, variáveis) com suporte a workspace edit.

## Implemented

- `textDocument/prepareRename`
- `textDocument/rename`
- `WorkspaceEdit` usando `changes`
- Variables, keywords e test cases locais
- Inclusão de arquivos indexados quando `WorkspaceIndex` está disponível

## Limitations

- Rename ainda é textual exato, não semântico por escopo.
- Rename de symbols importados a partir do usage fica para evolução futura.
