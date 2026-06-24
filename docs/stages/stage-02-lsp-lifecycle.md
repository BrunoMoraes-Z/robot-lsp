# Stage 02 — LSP Lifecycle

## Status

planned

## Goal

Implementar o lifecycle básico do LSP: initialize, initialized, shutdown e exit, com estados do servidor e capabilities mínimas.

## Scope

- `initialize` request: processar ClientCapabilities, retornar ServerCapabilities
- `initialized` notification
- `shutdown` request: preparar servidor para desligar
- `exit` notification: encerrar processo
- Estados: `uninitialized`, `running`, `shuttingDown`, `exited`
- Validação: mensagens antes de `initialize` geram erro; mensagens depois de `shutdown` geram erro
- Capabilities mínimas:
  - `textDocumentSync`: Full
  - `completionProvider`: triggerCharacters=[" "], resolveProvider=false
  - `hoverProvider`: true

## Out Of Scope

- Diagnósticos, completion, hover funcionais (apenas declarar capabilities)

## Deliverables

- `src/robot_lsp/protocol/server.py` com `LspServer`
- `src/robot_lsp/protocol/lsp_types.py` com tipos auxiliares
- Testes de sessão LSP via transporte em memória

## Acceptance Criteria

- Servidor responde `initialize` com `capabilities` corretas
- ServerCapabilities inclui `textDocumentSync: { openClose: true, change: Full }`
- `initialized` não gera resposta (é notification)
- `shutdown` retorna `null`
- `exit` encerra o processo
- Requests antes de `initialize` retornam erro `-32002` (server not initialized)
- Requests depois de `shutdown` retornam erro `-32003` (server shutting down)

## Tests

- `test_initialize`
- `test_initialized`
- `test_shutdown`
- `test_exit`
- `test_request_before_initialize`
- `test_request_after_shutdown`
- `test_capabilities_format`

## Risks

- Estado de shutdown deve ser atômico para evitar race conditions

## Dependencies

- Stage 01
