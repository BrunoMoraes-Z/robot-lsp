# JSON-RPC

## Stage

Stage 01 — JSON-RPC

## Methods

- N/A (transporte, não método LSP)

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
| -32700 | ParseError | JSON inválido |
| -32600 | InvalidRequest | Estrutura da mensagem inválida |
| -32601 | MethodNotFound | Método não existe |
| -32602 | InvalidParams | Parâmetros inválidos |
| -32603 | InternalError | Erro interno |
| -32002 | ServerNotInitialized | LSP não inicializado |
| -32003 | ServerShuttingDown | LSP desligando |

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

- Parser puro, sem estado
- Validação de campos obrigatórios
- Separação entre request, notification e response pelo campo `id`
