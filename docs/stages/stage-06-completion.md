# Stage 06 — Completion

## Status

done

## Goal

Implementar completação de código para arquivos `.robot`: sections, settings, keywords locais e variables locais.

## Scope

- `textDocument/completion` handler
- `CompletionContext`: posição do cursor, documento, modelo parseado
- Providers:
  - **SectionProvider**: completa `*** Settings ***`, `*** Variables ***`, `*** Test Cases ***`, `*** Keywords ***`
  - **SettingProvider**: completa `Library`, `Resource`, `Variables`, `Documentation`, `Metadata`, `Suite Setup`, `Suite Teardown`, `Test Setup`, `Test Teardown`, `Test Tags`, `Test Template`, `Test Timeout`, `Force Tags`, `Default Tags`
  - **LocalKeywordProvider**: completa nomes de keywords definidas no mesmo arquivo
  - **LocalVariableProvider**: completa nomes de variáveis definidas no mesmo arquivo ($, @, &, %)
- `CompletionItem` com label, kind, detail, documentation, textEdit, data
- Trigger characters: espaço (para settings) e `$`, `@`, `&`, `%` (para variables)
- `isIncomplete`: false no MVP

## Out Of Scope

- Completion de libraries importadas (Stage 09)
- Auto-import
- `completionItem/resolve`
- Snippets completos

## Deliverables

- `src/robot_lsp/application/completion_service.py`
- Providers em módulos internos
- Testes para cada provider

## Acceptance Criteria

- Em linha vazia no início do arquivo: completa sections
- Em `*** Settings ***`: completa settings conhecidos
- Em `*** Keywords ***`: completa keywords definidas no mesmo arquivo
- Em chamada de keyword: completa nomes de keywords
- Em contexto de variável: completa variáveis do arquivo
- `CompletionItem` tem `label`, `kind` e `detail` preenchidos

## Tests

- `test_completion_sections`
- `test_completion_settings`
- `test_completion_local_keyword`
- `test_completion_local_variable`
- `test_completion_trigger_characters`
- `test_completion_empty_result`

## Risks

- Contexto incorreto (saber se cursor está em keyword call vs setting value) requer análise de linha
- Trigger characters podem causar completions inesperados

## Dependencies

- Stage 04 (modelo RF)

## Notes

- Stage concluída com completion inicial para sections, settings, keywords locais e variables locais.
- `textDocument/completion` foi integrado ao `LspServer` como request LSP.
- O serviço usa `DocumentStore` + `ParseService`, sem dependência direta do Robot Framework.
- Completion ainda não resolve libraries/resources importados; isso permanece para Stage 09.
- Validação executada com `just test` e `uv run python -m compileall src tests`.
