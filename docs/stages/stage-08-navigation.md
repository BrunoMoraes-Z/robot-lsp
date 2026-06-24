# Stage 08 — Navigation

## Status

done

## Goal

Implementar navegação local ao documento atual para símbolos do Robot Framework.

## Scope

- `textDocument/definition`
- `textDocument/references`
- `textDocument/documentSymbol`
- `textDocument/foldingRange`
- `textDocument/selectionRange`
- Escopo local ao documento aberto atual
- Keywords, variables, imports, test cases e ranges de seção

## Out Of Scope

- Referências em todo o workspace
- Definition para symbols importados de resources/libraries
- Call hierarchy/type hierarchy
- Resolução semântica profunda de libraries

## Deliverables

- `src/robot_lsp/application/navigation_service.py`
- Integração dos handlers no `LspServer`
- Capabilities de navegação no `initialize`
- Testes unitários de service e handlers LSP

## Acceptance Criteria

- `definition` retorna localizações para keywords/variables/imports locais
- `references` retorna ocorrências locais com suporte a `includeDeclaration`
- `documentSymbol` retorna imports, variables, test cases e keywords
- `foldingRange` retorna ranges de sections, test cases e keywords
- `selectionRange` retorna range do símbolo com parent de linha quando possível
- Handlers retornam listas vazias quando service/documento não existe

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

- O escopo local pode retornar resultados incompletos até Stage 09.
- Ranges de definição dependem da granularidade do adapter AST atual.

## Dependencies

- Stage 04
- Stage 06
- Stage 07

## Notes

- Stage concluída com navegação local ao documento atual.
- As capabilities `definitionProvider`, `referencesProvider`, `documentSymbolProvider`, `foldingRangeProvider` e `selectionRangeProvider` são anunciadas no `initialize`.
- Navegação cross-file fica para Stage 09 — Workspace Index.
- Validação executada com `just test` e `uv run python -m compileall src tests`.
