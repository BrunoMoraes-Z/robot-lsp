# Stage 03 — Document & Workspace

## Status

done

## Goal

Implementar sincronização de documentos (didOpen, didChange, didClose) e o gerenciamento de workspace.

## Scope

- `textDocument/didOpen`: receber documento, armazenar, iniciar tracking
- `textDocument/didChange` (sync Full): substituir conteúdo completo
- `textDocument/didClose`: remover documento do tracking
- `DocumentStore`: repositório de documentos abertos
- `Document`: URI, path, texto, versão, languageId
- URI helpers: `file://` → path, path → `file://`
- Conversão de posições LSP:
  - Line: 0-based
  - Character: 0-based UTF-16 code units
- Operações com range: calcular texto de um range, split por lines

## Out Of Scope

- Sync incremental (deixado para depois)
- Diagnostics (Stage 05)
- Workspace folders dinâmicos (deixado para Stage 13)

## Deliverables

- `src/robot_lsp/domain/positions.py` (LspPosition, LspRange, cálculos UTF-16)
- `src/robot_lsp/application/document_store.py` (DocumentStore, Document)
- Testes unitários de posições, conversões e store

## Acceptance Criteria

- `didOpen` adiciona documento ao `DocumentStore`
- `didChange` com `textDocumentSyncKind.Full` substitui conteúdo e incrementa versão
- `didClose` remove documento
- URI `file:///c:/projects/test.robot` → path correto
- Conversão UTF-16 funciona: strings com emoji (2 code units) e acentos (1 code unit)
- `LspRange` calcula texto de um range corretamente

## Tests

- `test_did_open`
- `test_did_change_full`
- `test_did_close`
- `test_document_version`
- `test_uri_to_path`
- `test_path_to_uri`
- `test_lsp_position_utf16_ascii`
- `test_lsp_position_utf16_accent`
- `test_lsp_position_utf16_emoji`
- `test_range_text_extraction`

## Risks

- Conversão UTF-16 incorreta causa bugs de posição em todos os recursos do LSP
- URIs com encoding percentual precisam ser decodificadas

## Dependencies

- Stage 02

## Notes

- Stage concluída com `DocumentStore`, `Document`, URI helpers, conversão UTF-16 e handlers LSP de document sync.
- `didChange` usa sync full conforme ADR-0005 e specs de sincronização.
- `position_to_utf16_offset` trata texto vazio, acentos e emoji (2 UTF-16 code units).
- Validação executada com `just test` e `uv run python -m compileall src tests`.
