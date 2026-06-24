# Stage 11 — Formatting & Code Actions

## Status

done

## Goal

Implementar formatação inicial de documentos Robot Framework e code actions básicas para diagnostics conhecidos.

## Scope

- `textDocument/formatting`
- `textDocument/rangeFormatting`
- `textDocument/codeAction`
- Normalização inicial de espaçamento entre células
- Quick actions para diagnostics conhecidos

## Out Of Scope

- Formatação semântica baseada em AST
- Correção automática de parse errors
- Busca de imports ausentes no workspace
- `codeAction/resolve`
- Configuração persistente de estilo

## Deliverables

- `src/robot_lsp/application/formatting_service.py`
- `src/robot_lsp/application/code_action_service.py`
- Handlers no `LspServer`
- Capabilities de formatting e code action em `lsp_types.py`
- Testes unitários de services e handlers LSP

## Acceptance Criteria

- `textDocument/formatting` retorna `TextEdit` quando há mudanças
- `textDocument/formatting` retorna lista vazia quando documento já está formatado
- `textDocument/rangeFormatting` formata linhas completas tocadas pelo range
- `textDocument/codeAction` retorna quick actions para diagnostics conhecidos
- `initialize` anuncia capabilities de formatting e code action
- Services ausentes resultam em respostas vazias, sem erro

## Tests

- `test_format_robot_text_normalizes_cell_spacing`
- `test_format_document_returns_single_full_document_edit`
- `test_format_document_returns_no_edits_when_unchanged`
- `test_format_range_formats_whole_touched_lines`
- `test_parse_error_diagnostic_returns_quick_fix_action`
- `test_text_document_formatting`
- `test_text_document_range_formatting`
- `test_text_document_code_action`

## Risks

- A formatação atual é textual e pode não cobrir nuances semânticas do Robot Framework.
- Code actions iniciais são informativas e ainda não aplicam correções automáticas.
- `FormattingOptions` ainda não altera o estilo produzido.

## Dependencies

- Stage 03
- Stage 04
- Stage 05

## Notes

- Stage concluída com services de aplicação independentes e integração LSP.
- Validação executada com `just test` e `uv run python -m compileall src tests`.
