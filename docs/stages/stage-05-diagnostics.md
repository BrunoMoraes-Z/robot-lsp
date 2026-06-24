# Stage 05 — Diagnostics

## Status

done

## Goal

Implementar geração de diagnostics a partir do parse do Robot Framework e publicação via `textDocument/publishDiagnostics`.

## Scope

- Coletar erros de sintaxe do parser RF
- Mapear erros para `LspDiagnostic` com severity, message, range
- Converter ranges RF (1-based) para LSP (0-based UTF-16)
- `textDocument/publishDiagnostics`: enviar diagnostics para o cliente
- `DiagnosticService`: orquestrar:
  - Parse do documento
  - Coleta de diagnostics
  - Debounce (300ms) para evitar flood
  - Cancelar diagnóstico pendente por URI quando novo didChange chega
  - Publicar apenas se houve mudança
- Fallback: quando RF não fornece range, usar linha inteira

## Out Of Scope

- Análise semântica (robocop, regras de boas práticas)
- Code actions

## Deliverables

- `src/robot_lsp/application/diagnostic_service.py`
- `src/robot_lsp/domain/diagnostics.py`
- Integração com `LspServer` para publicar diagnostics

## Acceptance Criteria

- Documento inválido dispara `publishDiagnostics` com ao menos 1 diagnostic
- Documento corrigido limpa diagnostics (array vazio)
- Debounce evita publicações em cada caractere digitado
- Diagnostics cancelados (sobrescritos) não são publicados
- Range do diagnostic cobre a região do erro (ou fallback para linha)
- Severidade correta: error para parse error

## Tests

- `test_diagnostic_from_parse_error`
- `test_diagnostic_cleared_on_fix`
- `test_diagnostic_debounce`
- `test_diagnostic_cancel`
- `test_diagnostic_range_conversion`
- `test_diagnostic_fallback_range`

## Risks

- RF pode não reportar posição exata em todos os erros
- Debounce pode atrasar feedback; ajustar para 300ms como padrão

## Dependencies

- Stage 04 (modelo RF)

## Notes

- Stage concluída com `ParseService`, `DiagnosticService` e integração opcional com `LspServer`.
- O servidor mantém notifications de saída em `outgoing_notifications` até termos o loop de transporte completo.
- `didOpen` e `didChange` agendam diagnostics; `didClose` limpa diagnostics.
- `DiagnosticService.flush(uri)` foi adicionado para testes determinísticos e uso controlado.
- Validação executada com `just test` e `uv run python -m compileall src tests`.
