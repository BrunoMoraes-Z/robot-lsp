# JSON-RPC

## Stage

Stage 01 — JSON-RPC

## Methods

- N/A (transport, not an LSP method)

## Specification

### Request

```json
{"jsonrpc":"2.0","id":1,"method":"textDocument/completion","params":{...}}
```

### Response

```json
{"jsonrpc":"2.0","id":1,"result":{...}}
```

### Notification

```json
{"jsonrpc":"2.0","method":"textDocument/didOpen","params":{...}}
```

### Error

```json
{"jsonrpc":"2.0","id":1,"error":{"code":-32601,"message":"Method not found"}}
```

### Error Codes

| Code | Name | Description |
|---|---|---|
| -32700 | ParseError | Invalid JSON |
| -32600 | InvalidRequest | Invalid message structure |
| -32601 | MethodNotFound | Method does not exist |
| -32602 | InvalidParams | Invalid parameters |
| -32603 | InternalError | Internal error |
| -32002 | ServerNotInitialized | LSP not initialized |
| -32003 | ServerShuttingDown | LSP shutting down |

### Cancelation

Request de cancelamento:

```json
{"jsonrpc":"2.0","method":"$/cancelRequest","params":{"id":1}}
```

## Implementation

### JsonRpcMessage

```python
@dataclass
class JsonRpcMessage:
    jsonrpc: str = "2.0"
    id: int | str | None = None
    method: str | None = None
    params: dict | list | None = None
    result: Any = None
    error: JsonRpcError | None = None
```

### Functions

- `parse_message(json_str: str) -> JsonRpcMessage`
- `encode_message(msg: JsonRpcMessage) -> str`

## Architecture

- Pure, stateless parser
- Required field validation
- Separation between request, notification, and response by the `id` field
