# Stage 12 — Performance & Isolation

## Status

done

## Goal

Reduzir trabalho repetido em requests comuns e registrar decisões sobre isolamento antes de adicionar concorrência ou subprocessos.

## Scope

- Cache de parse de documentos abertos
- Invalidação por URI, versão e hash do texto
- Limite LRU configurável
- Revisão do cache de workspace existente
- Decisão explícita sobre worker pool e subprocess isolation

## Out Of Scope

- Worker pool para handlers LSP
- Subprocesso para indexação
- Cache persistido em disco
- Telemetria ou profiling detalhado

## Deliverables

- Cache LRU em `src/robot_lsp/application/parse_service.py`
- Testes unitários de cache e invalidação
- Atualização das specs de performance

## Acceptance Criteria

- Documento inalterado reutiliza o mesmo `ParseResult`
- Mudança de texto dispara novo parse
- Mudança de versão dispara novo parse
- Cache respeita limite LRU configurável
- Cache pode ser limpo por URI
- Workspace index mantém cache por mtime + hash
- Subprocess isolation fica documentado como decisão futura baseada em métricas

## Tests

- `test_parse_document_reuses_cached_result_for_unchanged_document`
- `test_parse_document_invalidates_cache_when_text_changes`
- `test_parse_document_invalidates_cache_when_version_changes`
- `test_parse_cache_evicts_least_recently_used_entry`
- `test_clear_uri_removes_cached_entry`
- `test_update_file_reuses_cache_when_unchanged`

## Risks

- O cache guarda `ParseResult` em memória e pode reter modelos de documentos grandes até eviction.
- Como handlers ainda são síncronos, operações realmente longas ainda podem bloquear até stages futuros.
- Cache em disco não existe; workspaces grandes ainda dependem de cache em memória.

## Dependencies

- Stage 03
- Stage 04
- Stage 09

## Notes

- A otimização foi aplicada no `ParseService`, então diagnostics, completion, hover, navigation e refactoring se beneficiam sem mudanças locais.
- Worker pool e subprocesso foram postergados para evitar complexidade prematura.
