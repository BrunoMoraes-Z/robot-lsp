# Stage 01 — JSON-RPC

## Status

done

## Goal

Implementar o protocolo JSON-RPC 2.0 e o transporte LSP sobre `stdio`, sem dependências externas.

## Scope

- Parser/serializer JSON-RPC 2.0
- Request, Response, Notification, Error
- Error codes padrão: ParseError, InvalidRequest, MethodNotFound, InvalidParams, InternalError, etc.
- LSP framing: `Content-Length: <bytes>\r\n\r\n<json>`
- Leitor thread-safe com buffer parcial
- Escritor thread-safe
- Dispatch de métodos por nome
- Suporte a `$/cancelRequest`
- Testes com mensagens em memória (sem stdio real)

## Out Of Scope

- Qualquer método LSP específico (initialize, etc.)
- Lifecycle do servidor
- Document sync

## Deliverables

- `src/robot_lsp/protocol/jsonrpc.py`
- `src/robot_lsp/protocol/dispatch.py`
- `src/robot_lsp/protocol/transport_stdio.py`
- Testes unitários completos

## Acceptance Criteria

- Mensagens JSON-RPC são serializadas/deserializadas corretamente
- Requests com `id` geram responses correspondentes
- Notifications (sem `id`) não geram responses
- Errors têm code, message e data
- `Content-Length` header é lido e escrito corretamente
- Mensagens parciais são acumuladas até o tamanho completo
- `$/cancelRequest` cancela handler pendente
- Métodos desconhecidos retornam `MethodNotFound`
- Testes de framing com conteúdo multi-byte

## Tests

- `test_json_rpc_request`
- `test_json_rpc_notification`
- `test_json_rpc_response`
- `test_json_rpc_error`
- `test_json_rpc_invalid_json`
- `test_json_rpc_method_not_found`
- `test_transport_content_length`
- `test_transport_partial_message`
- `test_transport_multiple_messages`
- `test_cancel_request`

## Risks

- Thread safety no escritor/leitor concorrente
- Tratamento de mensagens parcialmente recebidas

## Dependencies

- Stage 00

## Notes

- Usar `json` da stdlib
- Reader opera em `sys.stdin.buffer`, writer em `sys.stdout.buffer`
- Logs vão para `stderr`
- Stage concluída com 24 testes específicos de protocolo + teste geral de importação
- Validação executada com `just test` e `uv run python -m compileall src tests`
