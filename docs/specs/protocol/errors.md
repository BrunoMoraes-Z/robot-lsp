# Protocol Errors

## Stage

Stage 02 — LSP Lifecycle

## Error Scenarios

### Before Initialize

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32002,
    "message": "Server not initialized"
  }
}
```

### After Shutdown

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32003,
    "message": "Server is shutting down"
  }
}
```

### Method Not Found

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found: customMethod"
  }
}
```

### Invalid Params

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": "uri is required"
  }
}
```

### Internal Error

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": "ZeroDivisionError"
  }
}
```
