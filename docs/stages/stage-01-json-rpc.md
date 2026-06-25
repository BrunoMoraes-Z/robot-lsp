# Stage 01 — JSON-RPC

## Status

done

## Goal

Implement the JSON-RPC 2.0 protocol and LSP transport over `stdio`, without external dependencies.

## Scope

- JSON-RPC 2.0 parser/serializer
- Request, Response, Notification, Error
- Standard error codes: ParseError, InvalidRequest, MethodNotFound, InvalidParams, InternalError, etc.
- LSP framing: `Content-Length: <bytes>\r\n\r\n<json>`
- Thread-safe reader with partial buffer
- Thread-safe writer
- Method dispatch by name
- Support for `$/cancelRequest`
- Tests with in-memory messages (without real stdio)

## Out Of Scope

- Any specific LSP method (initialize, etc.)
- Server lifecycle
- Document sync

## Deliverables

- `src/robot_lsp/protocol/jsonrpc.py`
- `src/robot_lsp/protocol/dispatch.py`
- `src/robot_lsp/protocol/transport_stdio.py`
- Complete unit tests

## Acceptance Criteria

- JSON-RPC messages serialize/deserialize correctly
- Requests with `id` generate matching responses
- Notifications (without `id`) do not generate responses
- Errors include code, message, and data
- `Content-Length` header is read and written correctly
- Partial messages are accumulated until the full size is reached
- `$/cancelRequest` cancels a pending handler
- Unknown methods return `MethodNotFound`
- Framing tests cover multibyte content

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

- Thread safety in concurrent reader/writer usage
- Handling partially received messages

## Dependencies

- Stage 00

## Notes

- Use stdlib `json`
- Reader operates on `sys.stdin.buffer`, writer on `sys.stdout.buffer`
- Logs go to `stderr`
- Stage completed with 24 protocol-specific tests plus the general import test
- Validation executed with `just test` and `uv run python -m compileall src tests`
