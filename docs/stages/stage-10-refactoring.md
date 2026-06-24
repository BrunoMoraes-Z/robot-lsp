# Stage 10 — Refactoring

## Status

done

## Goal

Implementar refactoring inicial via `prepareRename`, `rename` e `WorkspaceEdit`.

## Scope

- `textDocument/prepareRename`
- `textDocument/rename`
- `WorkspaceEdit` com `changes`
- Rename de variables, keywords e test cases locais
- Rename em documentos indexados quando `WorkspaceIndex` estiver disponível

## Out Of Scope

- Validação semântica profunda do novo nome
- Rename inteligente por escopo
- Rename de symbols importados a partir de clique em usage importada
- Aplicação de edits no filesystem

## Deliverables

- `src/robot_lsp/application/refactoring_service.py`
- Handlers no `LspServer`
- Capability `renameProvider` com `prepareProvider: true`
- Testes unitários de service e handlers LSP

## Acceptance Criteria

- `prepareRename` retorna range e placeholder quando símbolo é renomeável
- `prepareRename` retorna `null` para símbolos desconhecidos
- `rename` retorna `WorkspaceEdit`
- Rename local altera todas as ocorrências textuais exatas no documento aberto
- Rename com `WorkspaceIndex` inclui arquivos indexados
- Handler retorna `null` quando service não está configurado

## Tests

- `test_prepare_rename_variable`
- `test_prepare_rename_unknown_symbol_returns_none`
- `test_rename_variable_local_document`
- `test_rename_keyword_local_document`
- `test_rename_with_workspace_index_updates_indexed_files`
- `test_text_document_prepare_rename`
- `test_text_document_rename`

## Risks

- Rename textual exato pode renomear ocorrências que não são semanticamente o mesmo símbolo.
- Rename por escopo será refinado quando o modelo semântico de uso/definição amadurecer.

## Dependencies

- Stage 04
- Stage 08
- Stage 09

## Notes

- Stage concluída com `RefactoringService` e integração LSP.
- WorkspaceEdit usa `changes` por URI.
- Validação executada com `just test` e `uv run python -m compileall src tests`.
